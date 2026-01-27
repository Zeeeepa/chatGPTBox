"""
Custom Web Provider
Configurable web interface provider for any chat URL (DeepSeek, Mistral, etc.)
Supports custom XPath/CSS selectors for input, send button, response areas
"""

import asyncio
import json
import logging
from typing import List, AsyncGenerator, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from .base_provider import BaseProvider, ProviderConfig, ProviderResponse, ChatMessage, MessageRole, ProviderType, WebUIElements

logger = logging.getLogger(__name__)

class CustomWebProvider(BaseProvider):
    """Custom Web Interface Provider with configurable selectors"""
    
    def __init__(self, config: ProviderConfig, ui_elements: WebUIElements):
        super().__init__(config)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.ui_elements = ui_elements
        
        # UI State tracking
        self.ui_state = {
            "input_available": False,
            "send_button_state": "initial",  # initial, progressing, ready
            "response_ready": False,
            "conversation_active": False,
            "login_required": False
        }
        
        self.base_url = config.base_url
        self.conversation_history = []
        
        # Default send button states if not provided
        if not self.ui_elements.send_button_states:
            self.ui_elements.send_button_states = {
                "initial": "Ready to receive",
                "progressing": "Progressing",
                "ready": "Ready to receive"
            }
    
    async def initialize(self) -> bool:
        """Initialize browser and navigate to custom URL"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with standard settings
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Set to True for production
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ]
            )
            
            # Create context
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Create page and navigate
            self.page = await self.context.new_page()
            
            # Navigate to custom URL
            await self.page.goto(self.base_url, wait_until="networkidle")
            
            # Wait for page to load
            await self.page.wait_for_timeout(5000)
            
            # Check if we can find the input area
            input_element = await self._find_element(self.ui_elements.input_selector)
            if input_element:
                self.ui_state["input_available"] = True
                self.ui_state["send_button_state"] = "ready"
                self.is_initialized = True
                logger.info(f"Custom web interface initialized successfully for {self.base_url}")
                return True
            else:
                logger.error(f"Could not find input area with selector: {self.ui_elements.input_selector}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize custom web provider: {e}")
            return False
    
    async def _find_element(self, selector: str):
        """Find element using XPath or CSS selector"""
        if not self.page:
            return None
            
        try:
            if self.ui_elements.use_xpath:
                return await self.page.query_selector(f"xpath={selector}")
            else:
                return await self.page.query_selector(selector)
        except Exception as e:
            logger.error(f"Error finding element with selector {selector}: {e}")
            return None
    
    async def _find_elements(self, selector: str):
        """Find elements using XPath or CSS selector"""
        if not self.page:
            return []
            
        try:
            if self.ui_elements.use_xpath:
                return await self.page.query_selector_all(f"xpath={selector}")
            else:
                return await self.page.query_selector_all(selector)
        except Exception as e:
            logger.error(f"Error finding elements with selector {selector}: {e}")
            return []
    
    async def send_message(self, message: str, conversation_history: List[ChatMessage] = None) -> ProviderResponse:
        """Send message to custom web interface"""
        try:
            if not self.page or not self.ui_state["input_available"]:
                return ProviderResponse(
                    content="",
                    provider=self.name,
                    error="Custom web interface not initialized",
                    success=False
                )
            
            # Update UI state
            self.ui_state["send_button_state"] = "progressing"
            
            # Find input area
            input_element = await self._find_element(self.ui_elements.input_selector)
            if input_element:
                # Clear and type message
                await input_element.click()
                await input_element.fill("")  # Clear existing text
                
                # Handle different input types
                tag_name = await input_element.evaluate("el => el.tagName.toLowerCase()")
                if tag_name == "div" and await input_element.get_attribute("contenteditable"):
                    # For contenteditable div
                    await input_element.evaluate(f"el => el.innerHTML = '{message}'")
                    # Trigger input event
                    await input_element.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
                else:
                    # For textarea or input
                    await input_element.type(message, delay=30)
                
                # Wait for UI to update
                await self.page.wait_for_timeout(1000)
                
                # Find and click send button
                send_button = await self._find_element(self.ui_elements.send_button_selector)
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
                            model=f"custom-web-{self.base_url.split('//')[1].split('/')[0]}",
                            success=True,
                            metadata={
                                "ui_state": self.ui_state.copy(),
                                "response_method": "web_automation",
                                "conversation_length": len(self.conversation_history),
                                "base_url": self.base_url
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
                        error=f"Could not find send button with selector: {self.ui_elements.send_button_selector}",
                        success=False
                    )
            else:
                return ProviderResponse(
                    content="",
                    provider=self.name,
                    error=f"Could not find input area with selector: {self.ui_elements.input_selector}",
                    success=False
                )
                
        except Exception as e:
            logger.error(f"Error sending message to custom web interface: {e}")
            self.ui_state["send_button_state"] = "ready"
            return ProviderResponse(
                content="",
                provider=self.name,
                error=str(e),
                success=False
            )
    
    async def stream_message(self, message: str, conversation_history: List[ChatMessage] = None) -> AsyncGenerator[str, None]:
        """Stream message response from custom web interface"""
        try:
            if not self.page or not self.ui_state["input_available"]:
                yield "Error: Custom web interface not initialized"
                return
            
            # Update UI state
            self.ui_state["send_button_state"] = "progressing"
            
            # Send message (similar to send_message but with streaming)
            input_element = await self._find_element(self.ui_elements.input_selector)
            if input_element:
                await input_element.click()
                await input_element.fill("")
                
                tag_name = await input_element.evaluate("el => el.tagName.toLowerCase()")
                if tag_name == "div" and await input_element.get_attribute("contenteditable"):
                    await input_element.evaluate(f"el => el.innerHTML = '{message}'")
                    await input_element.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
                else:
                    await input_element.type(message, delay=30)
                
                await self.page.wait_for_timeout(1000)
                
                send_button = await self._find_element(self.ui_elements.send_button_selector)
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
                    yield f"Error: Could not find send button with selector: {self.ui_elements.send_button_selector}"
            else:
                yield f"Error: Could not find input area with selector: {self.ui_elements.input_selector}"
                
        except Exception as e:
            logger.error(f"Error streaming from custom web interface: {e}")
            yield f"Error: {str(e)}"
    
    async def _wait_for_response(self, timeout: int = 60) -> str:
        """Wait for response and extract content"""
        try:
            # Wait for response to appear
            await self.page.wait_for_timeout(3000)
            
            # Try to find response elements
            response_elements = await self._find_elements(self.ui_elements.response_selector)
            
            if response_elements:
                # Get the last response (most recent)
                last_response = response_elements[-1]
                content = await last_response.inner_text()
                if content and content.strip():
                    return content.strip()
            
            # Fallback: wait a bit more and try again
            await self.page.wait_for_timeout(3000)
            response_elements = await self._find_elements(self.ui_elements.response_selector)
            
            if response_elements:
                last_response = response_elements[-1]
                content = await last_response.inner_text()
                if content and content.strip():
                    return content.strip()
            
            return f"Response received from {self.base_url} (content extraction needs refinement)"
                
        except Exception as e:
            logger.error(f"Error waiting for response: {e}")
            return f"Error extracting response: {str(e)}"
    
    async def _stream_response(self) -> AsyncGenerator[str, None]:
        """Stream response as it appears"""
        try:
            # Wait for response to start appearing
            await self.page.wait_for_timeout(2000)
            
            previous_content = ""
            max_iterations = 30
            iteration = 0
            
            while iteration < max_iterations:
                try:
                    # Get current response content
                    response_elements = await self._find_elements(self.ui_elements.response_selector)
                    if response_elements:
                        current_content = await response_elements[-1].inner_text()
                        
                        # If content has grown, yield the new part
                        if len(current_content) > len(previous_content):
                            new_content = current_content[len(previous_content):]
                            if new_content.strip():
                                yield new_content
                            previous_content = current_content
                        
                        # Check if response seems complete (no more changes)
                        await asyncio.sleep(1)
                        new_check_content = await response_elements[-1].inner_text()
                        if new_check_content == current_content:
                            # Content hasn't changed, likely complete
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
            logger.error(f"Error streaming response: {e}")
            yield f"Error in streaming: {str(e)}"
    
    async def new_chat(self) -> bool:
        """Start a new chat session"""
        try:
            if not self.page:
                return False
            
            if self.ui_elements.new_chat_selector:
                new_chat_button = await self._find_element(self.ui_elements.new_chat_selector)
                if new_chat_button:
                    await new_chat_button.click()
                    await self.page.wait_for_timeout(3000)
                    self.ui_state["conversation_active"] = False
                    self.conversation_history = []
                    return True
            
            # Fallback: refresh the page
            await self.page.reload(wait_until="networkidle")
            await self.page.wait_for_timeout(5000)
            self.conversation_history = []
            return True
                
        except Exception as e:
            logger.error(f"Error starting new chat: {e}")
            return False
    
    async def get_send_button_state(self) -> str:
        """Get current send button state"""
        try:
            if not self.page:
                return "unknown"
            
            send_button = await self._find_element(self.ui_elements.send_button_selector)
            if send_button:
                is_disabled = await send_button.get_attribute("disabled")
                is_aria_disabled = await send_button.get_attribute("aria-disabled")
                
                if is_disabled or is_aria_disabled == "true":
                    return "progressing"
                else:
                    return "ready"
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error getting send button state: {e}")
            return "unknown"
    
    async def get_models(self) -> List[str]:
        """Get available models"""
        domain = self.base_url.split('//')[1].split('/')[0]
        return [f"custom-web-{domain}"]
    
    async def health_check(self) -> bool:
        """Check if custom web interface is accessible"""
        try:
            if not self.page:
                return False
            
            # Check if we can access the input area
            input_element = await self._find_element(self.ui_elements.input_selector)
            return input_element is not None
            
        except Exception as e:
            logger.error(f"Custom web health check failed: {e}")
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
            logger.error(f"Error during custom web cleanup: {e}")

# Predefined configurations for popular services
PREDEFINED_CONFIGS = {
    "deepseek": {
        "base_url": "https://chat.deepseek.com/",
        "ui_elements": WebUIElements(
            input_selector="textarea[placeholder*='Ask me anything'], .chat-input textarea",
            send_button_selector="button[type='submit'], .send-button, button:has(svg)",
            response_selector=".message-content, .response-text, .markdown-content",
            new_chat_selector="button:has-text('New Chat'), .new-chat-button",
            send_button_states={
                "initial": "Ready to receive",
                "progressing": "Generating...",
                "ready": "Ready to receive"
            },
            use_xpath=False
        )
    },
    "mistral": {
        "base_url": "https://chat.mistral.ai/chat",
        "ui_elements": WebUIElements(
            input_selector="textarea[placeholder*='Type a message'], .chat-input",
            send_button_selector="button[aria-label*='Send'], .send-button",
            response_selector=".message-content, .response-content",
            new_chat_selector="button:has-text('New conversation'), .new-conversation",
            send_button_states={
                "initial": "Send message",
                "progressing": "Sending...",
                "ready": "Send message"
            },
            use_xpath=False
        )
    },
    "perplexity": {
        "base_url": "https://www.perplexity.ai/",
        "ui_elements": WebUIElements(
            input_selector="textarea[placeholder*='Ask anything'], .search-input",
            send_button_selector="button[aria-label*='Submit'], .submit-button",
            response_selector=".answer-content, .response-text",
            new_chat_selector="button:has-text('New'), .new-thread",
            use_xpath=False
        )
    }
}

def create_custom_provider(service_name: str, custom_config: Optional[Dict] = None) -> CustomWebProvider:
    """Create a custom web provider for a specific service"""
    
    if service_name in PREDEFINED_CONFIGS:
        config_data = PREDEFINED_CONFIGS[service_name]
        config = ProviderConfig(
            name=f"custom-{service_name}",
            provider_type=ProviderType.CUSTOM_WEB,
            base_url=config_data["base_url"]
        )
        return CustomWebProvider(config, config_data["ui_elements"])
    
    elif custom_config:
        config = ProviderConfig(
            name=custom_config.get("name", "custom-web"),
            provider_type=ProviderType.CUSTOM_WEB,
            base_url=custom_config["base_url"]
        )
        
        ui_elements = WebUIElements(
            input_selector=custom_config["input_selector"],
            send_button_selector=custom_config["send_button_selector"],
            response_selector=custom_config["response_selector"],
            new_chat_selector=custom_config.get("new_chat_selector"),
            send_button_states=custom_config.get("send_button_states"),
            use_xpath=custom_config.get("use_xpath", False)
        )
        
        return CustomWebProvider(config, ui_elements)
    
    else:
        raise ValueError(f"Unknown service '{service_name}' and no custom config provided")

# Test function for custom web interfaces
async def test_custom_web():
    """Test custom web interface with dynamic prompts"""
    
    # Test DeepSeek
    print("🔄 Testing DeepSeek...")
    deepseek_provider = create_custom_provider("deepseek")
    
    try:
        success = await deepseek_provider.initialize()
        print(f"✅ DeepSeek initialization: {'Success' if success else 'Failed'}")
        
        if success:
            response = await deepseek_provider.send_message("What is artificial intelligence?")
            if response.success:
                print(f"✅ DeepSeek response: {response.content[:200]}...")
            else:
                print(f"❌ DeepSeek error: {response.error}")
    finally:
        await deepseek_provider.cleanup()
    
    # Test custom configuration
    print("\n🔄 Testing custom configuration...")
    custom_config = {
        "name": "custom-test",
        "base_url": "https://chat.openai.com/",
        "input_selector": "textarea[data-id='root']",
        "send_button_selector": "button[data-testid='send-button']",
        "response_selector": ".markdown",
        "new_chat_selector": "a[href='/']",
        "use_xpath": False
    }
    
    custom_provider = create_custom_provider("custom", custom_config)
    
    try:
        success = await custom_provider.initialize()
        print(f"✅ Custom initialization: {'Success' if success else 'Failed'}")
        
        if success:
            # Test UI state
            button_state = await custom_provider.get_send_button_state()
            print(f"📊 Send button state: {button_state}")
            
            # Test health check
            healthy = await custom_provider.health_check()
            print(f"✅ Health check: {'Healthy' if healthy else 'Unhealthy'}")
    finally:
        await custom_provider.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_custom_web())
