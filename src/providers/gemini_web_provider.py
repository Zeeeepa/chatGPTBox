"""
Gemini Web Interface Provider
Based on ChatGPTBox logic for Google Gemini web interface
"""

import asyncio
import json
import logging
from typing import List, AsyncGenerator, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from .base_provider import BaseProvider, ProviderConfig, ProviderResponse, ChatMessage, MessageRole, ProviderType

logger = logging.getLogger(__name__)

class GeminiWebProvider(BaseProvider):
    """Gemini Web Interface Provider following ChatGPTBox patterns"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # Gemini specific selectors (based on ChatGPTBox patterns)
        self.selectors = {
            "input_area": "div[contenteditable='true'], textarea[placeholder*='Enter a prompt'], .ql-editor, rich-textarea",
            "send_button": "button[aria-label*='Send'], button[data-testid='send-button'], .send-button, button:has(svg)",
            "response_area": ".model-response-text, .response-container, [data-testid='response'], .markdown-content",
            "new_chat_button": "button[aria-label*='New chat'], .new-chat-button, button:has-text('New chat')",
            "loading_indicator": ".loading, .thinking, .generating, [data-testid='loading']",
            "error_message": ".error-message, .warning, [role='alert']",
            "login_required": "button:has-text('Sign in'), .sign-in-button"
        }
        
        # UI State tracking
        self.ui_state = {
            "input_available": False,
            "send_button_state": "initial",  # initial, progressing, ready
            "response_ready": False,
            "conversation_active": False,
            "login_required": False
        }
        
        self.base_url = config.base_url or "https://gemini.google.com"
        self.conversation_history = []
        
    async def initialize(self) -> bool:
        """Initialize browser and navigate to Gemini"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with ChatGPTBox-like settings
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Set to True for production
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ]
            )
            
            # Create context with proper settings
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                }
            )
            
            # Create page and navigate
            self.page = await self.context.new_page()
            
            # Navigate to Gemini
            await self.page.goto(self.base_url, wait_until="networkidle")
            
            # Wait for page to load
            await self.page.wait_for_timeout(5000)
            
            # Check for login requirement
            login_element = await self.page.query_selector(self.selectors["login_required"])
            if login_element:
                self.ui_state["login_required"] = True
                logger.warning("Gemini requires login - manual intervention needed")
                # Wait for user to login manually
                print("⚠️ Gemini requires login. Please log in manually in the browser window.")
                print("Press Enter when you've completed login...")
                input()
                await self.page.wait_for_timeout(3000)
            
            # Check if we can find the input area
            input_element = await self.page.query_selector(self.selectors["input_area"])
            if input_element:
                self.ui_state["input_available"] = True
                self.ui_state["send_button_state"] = "ready"
                self.ui_state["login_required"] = False
                self.is_initialized = True
                logger.info("Gemini web interface initialized successfully")
                return True
            else:
                logger.error("Could not find Gemini input area")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Gemini web provider: {e}")
            return False
    
    async def send_message(self, message: str, conversation_history: List[ChatMessage] = None) -> ProviderResponse:
        """Send message to Gemini web interface"""
        try:
            if not self.page or not self.ui_state["input_available"]:
                return ProviderResponse(
                    content="",
                    provider=self.name,
                    error="Gemini web interface not initialized",
                    success=False
                )
            
            # Update UI state
            self.ui_state["send_button_state"] = "progressing"
            
            # Find input area
            input_element = await self.page.query_selector(self.selectors["input_area"])
            if input_element:
                # Clear and type message
                await input_element.click()
                await input_element.fill("")  # Clear existing text
                
                # Handle contenteditable vs textarea
                tag_name = await input_element.evaluate("el => el.tagName.toLowerCase()")
                if tag_name == "div":
                    # For contenteditable div
                    await input_element.evaluate(f"el => el.innerHTML = '{message}'")
                else:
                    # For textarea
                    await input_element.type(message, delay=30)
                
                # Wait a moment for UI to update
                await self.page.wait_for_timeout(1000)
                
                # Find and click send button
                send_button = await self.page.query_selector(self.selectors["send_button"])
                if send_button:
                    # Check if button is enabled
                    is_disabled = await send_button.get_attribute("disabled")
                    is_aria_disabled = await send_button.get_attribute("aria-disabled")
                    
                    if not is_disabled and is_aria_disabled != "true":
                        await send_button.click()
                        
                        # Wait for response
                        response_content = await self._wait_for_response()
                        
                        # Update UI state
                        self.ui_state["send_button_state"] = "ready"
                        self.ui_state["response_ready"] = True
                        
                        # Store in conversation history
                        self.conversation_history.append({
                            "role": "user",
                            "content": message
                        })
                        self.conversation_history.append({
                            "role": "assistant", 
                            "content": response_content
                        })
                        
                        return ProviderResponse(
                            content=response_content,
                            provider=self.name,
                            model="gemini-web",
                            success=True,
                            metadata={
                                "ui_state": self.ui_state.copy(),
                                "response_method": "web_automation",
                                "conversation_length": len(self.conversation_history)
                            }
                        )
                    else:
                        return ProviderResponse(
                            content="",
                            provider=self.name,
                            error="Send button is disabled",
                            success=False
                        )
                else:
                    return ProviderResponse(
                        content="",
                        provider=self.name,
                        error="Could not find send button",
                        success=False
                    )
            else:
                return ProviderResponse(
                    content="",
                    provider=self.name,
                    error="Could not find input area",
                    success=False
                )
                
        except Exception as e:
            logger.error(f"Error sending message to Gemini: {e}")
            self.ui_state["send_button_state"] = "ready"
            return ProviderResponse(
                content="",
                provider=self.name,
                error=str(e),
                success=False
            )
    
    async def stream_message(self, message: str, conversation_history: List[ChatMessage] = None) -> AsyncGenerator[str, None]:
        """Stream message response from Gemini"""
        try:
            if not self.page or not self.ui_state["input_available"]:
                yield "Error: Gemini web interface not initialized"
                return
            
            # Update UI state
            self.ui_state["send_button_state"] = "progressing"
            
            # Send message (similar to send_message but with streaming)
            input_element = await self.page.query_selector(self.selectors["input_area"])
            if input_element:
                await input_element.click()
                await input_element.fill("")
                
                tag_name = await input_element.evaluate("el => el.tagName.toLowerCase()")
                if tag_name == "div":
                    await input_element.evaluate(f"el => el.innerHTML = '{message}'")
                else:
                    await input_element.type(message, delay=30)
                
                await self.page.wait_for_timeout(1000)
                
                send_button = await self.page.query_selector(self.selectors["send_button"])
                if send_button:
                    is_disabled = await send_button.get_attribute("disabled")
                    is_aria_disabled = await send_button.get_attribute("aria-disabled")
                    
                    if not is_disabled and is_aria_disabled != "true":
                        await send_button.click()
                        
                        # Stream response as it appears
                        async for chunk in self._stream_response():
                            yield chunk
                        
                        self.ui_state["send_button_state"] = "ready"
                    else:
                        yield "Error: Send button is disabled"
                else:
                    yield "Error: Could not find send button"
            else:
                yield "Error: Could not find input area"
                
        except Exception as e:
            logger.error(f"Error streaming from Gemini: {e}")
            yield f"Error: {str(e)}"
    
    async def _wait_for_response(self, timeout: int = 60) -> str:
        """Wait for Gemini response and extract content"""
        try:
            # Wait for loading indicator to appear
            try:
                await self.page.wait_for_selector(self.selectors["loading_indicator"], timeout=3000)
                # Wait for loading to disappear
                await self.page.wait_for_selector(self.selectors["loading_indicator"], state="detached", timeout=timeout * 1000)
            except:
                # No loading indicator found, continue
                pass
            
            # Wait for response to appear
            await self.page.wait_for_timeout(3000)
            
            # Try multiple selectors for response content
            response_selectors = [
                self.selectors["response_area"],
                ".model-response-text",
                "[data-testid='response']",
                ".markdown-content",
                ".response-container p",
                ".message-content"
            ]
            
            for selector in response_selectors:
                try:
                    response_elements = await self.page.query_selector_all(selector)
                    if response_elements:
                        # Get the last response (most recent)
                        last_response = response_elements[-1]
                        content = await last_response.inner_text()
                        if content and content.strip():
                            return content.strip()
                except:
                    continue
            
            # Fallback: try to extract any new text content
            await self.page.wait_for_timeout(2000)
            
            # Look for any text that might be a response
            all_text_elements = await self.page.query_selector_all("p, div, span")
            for element in reversed(all_text_elements[-10:]):  # Check last 10 elements
                try:
                    text = await element.inner_text()
                    if text and len(text) > 20 and not any(keyword in text.lower() for keyword in ["send", "new chat", "sign in"]):
                        return text.strip()
                except:
                    continue
            
            return "Response received from Gemini (content extraction needs refinement)"
                
        except Exception as e:
            logger.error(f"Error waiting for Gemini response: {e}")
            return f"Error extracting response: {str(e)}"
    
    async def _stream_response(self) -> AsyncGenerator[str, None]:
        """Stream response as it appears (for real-time streaming)"""
        try:
            # Wait for response to start appearing
            await self.page.wait_for_timeout(2000)
            
            previous_content = ""
            max_iterations = 30  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                try:
                    # Get current response content
                    response_elements = await self.page.query_selector_all(self.selectors["response_area"])
                    if response_elements:
                        current_content = await response_elements[-1].inner_text()
                        
                        # If content has grown, yield the new part
                        if len(current_content) > len(previous_content):
                            new_content = current_content[len(previous_content):]
                            if new_content.strip():
                                yield new_content
                            previous_content = current_content
                        
                        # Check if response is complete (no loading indicators)
                        loading_element = await self.page.query_selector(self.selectors["loading_indicator"])
                        if not loading_element:
                            break
                    
                    await asyncio.sleep(0.5)
                    iteration += 1
                    
                except Exception as e:
                    logger.error(f"Error in streaming iteration: {e}")
                    break
            
            # Final check for any remaining content
            if iteration >= max_iterations:
                final_response = await self._wait_for_response(timeout=10)
                if len(final_response) > len(previous_content):
                    yield final_response[len(previous_content):]
                    
        except Exception as e:
            logger.error(f"Error streaming Gemini response: {e}")
            yield f"Error in streaming: {str(e)}"
    
    async def new_chat(self) -> bool:
        """Start a new chat session"""
        try:
            if not self.page:
                return False
            
            new_chat_button = await self.page.query_selector(self.selectors["new_chat_button"])
            if new_chat_button:
                await new_chat_button.click()
                await self.page.wait_for_timeout(3000)
                self.ui_state["conversation_active"] = False
                self.conversation_history = []
                return True
            else:
                # Fallback: refresh the page
                await self.page.reload(wait_until="networkidle")
                await self.page.wait_for_timeout(5000)
                self.conversation_history = []
                return True
                
        except Exception as e:
            logger.error(f"Error starting new chat: {e}")
            return False
    
    async def get_models(self) -> List[str]:
        """Get available models"""
        return ["gemini-pro", "gemini-pro-vision", "gemini-web"]
    
    async def health_check(self) -> bool:
        """Check if Gemini web interface is accessible"""
        try:
            if not self.page:
                return False
            
            # Check if we can access the input area
            input_element = await self.page.query_selector(self.selectors["input_area"])
            return input_element is not None and not self.ui_state["login_required"]
            
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False
    
    async def cleanup(self):
        """Close browser and cleanup resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error during Gemini cleanup: {e}")

# Test function for Gemini web interface
async def test_gemini_web():
    """Test Gemini web interface with dynamic prompts"""
    config = ProviderConfig(
        name="gemini-web",
        provider_type=ProviderType.WEB_AUTOMATION,
        base_url="https://gemini.google.com",
        timeout=60
    )
    
    provider = GeminiWebProvider(config)
    
    try:
        # Initialize
        print("🔄 Initializing Gemini web provider...")
        success = await provider.initialize()
        print(f"✅ Initialization: {'Success' if success else 'Failed'}")
        
        if not success:
            return
        
        # Test health check
        print("🔄 Testing health check...")
        healthy = await provider.health_check()
        print(f"✅ Health check: {'Healthy' if healthy else 'Unhealthy'}")
        
        # Test dynamic prompts
        test_prompts = [
            "What is the capital of Japan?",
            "Explain machine learning in simple terms",
            "Write a haiku about technology",
            "What are the benefits of renewable energy?",
            "How does photosynthesis work?"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n🔄 Test {i}: {prompt}")
            
            # Send message
            response = await provider.send_message(prompt)
            
            if response.success:
                print(f"✅ Response: {response.content[:300]}...")
                if response.metadata:
                    print(f"📊 Metadata: {response.metadata}")
            else:
                print(f"❌ Error: {response.error}")
            
            # Wait between tests
            await asyncio.sleep(3)
        
        # Test streaming response
        print("\n🔄 Testing streaming response...")
        stream_content = ""
        async for chunk in provider.stream_message("Tell me about artificial intelligence"):
            stream_content += chunk
            print(chunk, end="", flush=True)
        print(f"\n✅ Streaming complete. Total length: {len(stream_content)}")
        
        # Test new chat functionality
        print("\n🔄 Testing new chat...")
        new_chat_success = await provider.new_chat()
        print(f"✅ New chat: {'Success' if new_chat_success else 'Failed'}")
        
        # Test follow-up conversation
        print("\n🔄 Testing follow-up conversation...")
        response1 = await provider.send_message("What is Python programming?")
        if response1.success:
            print(f"✅ First response: {response1.content[:200]}...")
            
            response2 = await provider.send_message("Can you give me a simple example?")
            if response2.success:
                print(f"✅ Follow-up response: {response2.content[:200]}...")
            else:
                print(f"❌ Follow-up error: {response2.error}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await provider.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_gemini_web())
