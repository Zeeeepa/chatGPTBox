"""
Z.AI Web Interface Provider
Programmatic response retrieval and state management for Z.AI web chat
"""

import asyncio
import json
import logging
from typing import List, AsyncGenerator, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from .base_provider import BaseProvider, ProviderConfig, ProviderResponse, ChatMessage, MessageRole, ProviderType

logger = logging.getLogger(__name__)

class ZAIWebProvider(BaseProvider):
    """Z.AI Web Interface Provider with state management"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # Z.AI specific selectors
        self.selectors = {
            "input_area": "textarea[placeholder*='输入消息'], textarea[placeholder*='Type a message'], #chat-input",
            "send_button": "button[type='submit'], button:has-text('发送'), button:has-text('Send'), .send-button",
            "response_area": ".message-content, .chat-message, .response-text, [data-testid='message-content']",
            "new_chat_button": "button:has-text('新对话'), button:has-text('New Chat'), .new-chat-btn",
            "loading_indicator": ".loading, .typing-indicator, .generating"
        }
        
        # UI State tracking
        self.ui_state = {
            "input_available": False,
            "send_button_state": "initial",  # initial, progressing, ready
            "response_ready": False,
            "conversation_active": False
        }
        
        self.base_url = config.base_url or "https://chat.z.ai"
        
    async def initialize(self) -> bool:
        """Initialize browser and navigate to Z.AI"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with specific settings for Z.AI
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Set to True for production
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                ]
            )
            
            # Create context with proper settings
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            # Create page and navigate
            self.page = await self.context.new_page()
            
            # Navigate to Z.AI
            await self.page.goto(self.base_url, wait_until="networkidle")
            
            # Wait for page to load and check for input elements
            await self.page.wait_for_timeout(3000)
            
            # Check if we can find the input area
            input_element = await self.page.query_selector(self.selectors["input_area"])
            if input_element:
                self.ui_state["input_available"] = True
                self.ui_state["send_button_state"] = "ready"
                self.is_initialized = True
                logger.info("Z.AI web interface initialized successfully")
                return True
            else:
                logger.error("Could not find Z.AI input area")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Z.AI web provider: {e}")
            return False
    
    async def send_message(self, message: str, conversation_history: List[ChatMessage] = None) -> ProviderResponse:
        """Send message to Z.AI web interface"""
        try:
            if not self.page or not self.ui_state["input_available"]:
                return ProviderResponse(
                    content="",
                    provider=self.name,
                    error="Z.AI web interface not initialized",
                    success=False
                )
            
            # Update UI state
            self.ui_state["send_button_state"] = "progressing"
            
            # Clear input area and type message
            input_element = await self.page.query_selector(self.selectors["input_area"])
            if input_element:
                await input_element.click()
                await input_element.fill("")  # Clear existing text
                await input_element.type(message, delay=50)  # Type with human-like delay
                
                # Find and click send button
                send_button = await self.page.query_selector(self.selectors["send_button"])
                if send_button:
                    # Check if button is enabled
                    is_disabled = await send_button.get_attribute("disabled")
                    if not is_disabled:
                        await send_button.click()
                        
                        # Wait for response
                        response_content = await self._wait_for_response()
                        
                        # Update UI state
                        self.ui_state["send_button_state"] = "ready"
                        self.ui_state["response_ready"] = True
                        
                        return ProviderResponse(
                            content=response_content,
                            provider=self.name,
                            model="z.ai-web",
                            success=True,
                            metadata={
                                "ui_state": self.ui_state.copy(),
                                "response_method": "web_automation"
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
            logger.error(f"Error sending message to Z.AI: {e}")
            self.ui_state["send_button_state"] = "ready"
            return ProviderResponse(
                content="",
                provider=self.name,
                error=str(e),
                success=False
            )
    
    async def stream_message(self, message: str, conversation_history: List[ChatMessage] = None) -> AsyncGenerator[str, None]:
        """Stream message response from Z.AI (simulated streaming)"""
        try:
            # Send message normally first
            response = await self.send_message(message, conversation_history)
            
            if response.success:
                # Simulate streaming by yielding chunks
                content = response.content
                chunk_size = 10
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    yield chunk
                    await asyncio.sleep(0.05)  # Small delay to simulate streaming
            else:
                yield f"Error: {response.error}"
                
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def _wait_for_response(self, timeout: int = 30) -> str:
        """Wait for Z.AI response and extract content"""
        try:
            # Wait for loading indicator to appear (if any)
            try:
                await self.page.wait_for_selector(self.selectors["loading_indicator"], timeout=2000)
                # Wait for loading to disappear
                await self.page.wait_for_selector(self.selectors["loading_indicator"], state="detached", timeout=timeout * 1000)
            except:
                # No loading indicator found, continue
                pass
            
            # Wait for new response to appear
            await self.page.wait_for_timeout(2000)  # Give time for response to render
            
            # Get all response elements
            response_elements = await self.page.query_selector_all(self.selectors["response_area"])
            
            if response_elements:
                # Get the last response (most recent)
                last_response = response_elements[-1]
                content = await last_response.inner_text()
                return content.strip()
            else:
                # Fallback: try to get any text that looks like a response
                await self.page.wait_for_timeout(3000)
                page_content = await self.page.content()
                
                # Simple heuristic to extract response
                # This would need to be refined based on Z.AI's actual HTML structure
                return "Response received from Z.AI (content extraction needs refinement)"
                
        except Exception as e:
            logger.error(f"Error waiting for Z.AI response: {e}")
            return f"Error extracting response: {str(e)}"
    
    async def get_ui_state(self) -> Dict[str, Any]:
        """Get current UI state"""
        if not self.page:
            return {"error": "Page not initialized"}
        
        try:
            # Check input availability
            input_element = await self.page.query_selector(self.selectors["input_area"])
            self.ui_state["input_available"] = input_element is not None
            
            # Check send button state
            send_button = await self.page.query_selector(self.selectors["send_button"])
            if send_button:
                is_disabled = await send_button.get_attribute("disabled")
                self.ui_state["send_button_state"] = "progressing" if is_disabled else "ready"
            
            # Check for loading indicators
            loading_element = await self.page.query_selector(self.selectors["loading_indicator"])
            if loading_element:
                self.ui_state["send_button_state"] = "progressing"
            
            return self.ui_state.copy()
            
        except Exception as e:
            logger.error(f"Error getting UI state: {e}")
            return {"error": str(e)}
    
    async def new_chat(self) -> bool:
        """Start a new chat session"""
        try:
            if not self.page:
                return False
            
            new_chat_button = await self.page.query_selector(self.selectors["new_chat_button"])
            if new_chat_button:
                await new_chat_button.click()
                await self.page.wait_for_timeout(2000)
                self.ui_state["conversation_active"] = False
                return True
            else:
                # Fallback: refresh the page
                await self.page.reload(wait_until="networkidle")
                await self.page.wait_for_timeout(3000)
                return True
                
        except Exception as e:
            logger.error(f"Error starting new chat: {e}")
            return False
    
    async def get_models(self) -> List[str]:
        """Get available models (Z.AI specific)"""
        return ["z.ai-web", "z.ai-gpt4", "z.ai-claude"]
    
    async def health_check(self) -> bool:
        """Check if Z.AI web interface is accessible"""
        try:
            if not self.page:
                return False
            
            # Check if we can access the input area
            input_element = await self.page.query_selector(self.selectors["input_area"])
            return input_element is not None
            
        except Exception as e:
            logger.error(f"Z.AI health check failed: {e}")
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
            logger.error(f"Error during Z.AI cleanup: {e}")

# Test function for Z.AI web interface
async def test_zai_web():
    """Test Z.AI web interface with dynamic prompts"""
    config = ProviderConfig(
        name="zai-web",
        provider_type=ProviderType.WEB_AUTOMATION,
        base_url="https://chat.z.ai",
        timeout=30
    )
    
    provider = ZAIWebProvider(config)
    
    try:
        # Initialize
        print("🔄 Initializing Z.AI web provider...")
        success = await provider.initialize()
        print(f"✅ Initialization: {'Success' if success else 'Failed'}")
        
        if not success:
            return
        
        # Test UI state
        print("🔄 Getting UI state...")
        ui_state = await provider.get_ui_state()
        print(f"✅ UI State: {ui_state}")
        
        # Test health check
        print("🔄 Testing health check...")
        healthy = await provider.health_check()
        print(f"✅ Health check: {'Healthy' if healthy else 'Unhealthy'}")
        
        # Test dynamic prompts
        test_prompts = [
            "Hello, how are you?",
            "What is artificial intelligence?",
            "Can you help me write a Python function?",
            "Tell me about the weather",
            "What are your capabilities?"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n🔄 Test {i}: {prompt}")
            
            # Get UI state before sending
            ui_before = await provider.get_ui_state()
            print(f"📊 UI State before: {ui_before}")
            
            # Send message
            response = await provider.send_message(prompt)
            
            if response.success:
                print(f"✅ Response: {response.content[:200]}...")
                if response.metadata:
                    print(f"📊 Metadata: {response.metadata}")
            else:
                print(f"❌ Error: {response.error}")
            
            # Get UI state after sending
            ui_after = await provider.get_ui_state()
            print(f"📊 UI State after: {ui_after}")
            
            # Wait between tests
            await asyncio.sleep(2)
        
        # Test new chat functionality
        print("\n🔄 Testing new chat...")
        new_chat_success = await provider.new_chat()
        print(f"✅ New chat: {'Success' if new_chat_success else 'Failed'}")
        
        # Test streaming (simulated)
        print("\n🔄 Testing streaming response...")
        stream_content = ""
        async for chunk in provider.stream_message("Tell me a short story"):
            stream_content += chunk
            print(chunk, end="", flush=True)
        print(f"\n✅ Streaming complete. Total length: {len(stream_content)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await provider.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_zai_web())
