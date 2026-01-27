"""
🧠 Claude Web Interface Implementation
Connects to Claude AI through web interface automation
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
from .base_interface import BaseInterface

logger = logging.getLogger(__name__)

class ClaudeWebInterface(BaseInterface):
    """Claude Web interface using browser automation"""
    
    def __init__(self, instance_id: str, config: Dict[str, Any]):
        super().__init__(instance_id, config)
        
        # Claude Web specific configuration
        self.claude_url = config.get("claude_url", "https://claude.ai/chat")
        self.headless = config.get("headless", True)
        self.timeout = config.get("timeout", 30000)
        
        # Browser automation
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Claude UI selectors
        self.selectors = {
            "message_input": 'div[contenteditable="true"]',
            "send_button": 'button[aria-label="Send Message"]',
            "messages": '.font-claude-message',
            "new_chat": 'button:has-text("New Chat")',
            "loading": '.animate-pulse'
        }
        
        self.logger.info(f"🧠 Claude Web Interface {instance_id} initialized")
    
    async def initialize(self) -> bool:
        """Initialize Claude Web interface with browser automation"""
        try:
            # Launch Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create new page
            self.page = await self.browser.new_page()
            
            # Set user agent
            await self.page.set_user_agent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Navigate to Claude
            await self.page.goto(self.claude_url, wait_until="networkidle")
            
            # Wait for page to load
            await self.page.wait_for_timeout(3000)
            
            self.is_initialized = True
            self.logger.info(f"✅ Claude Web Interface {self.instance_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Claude Web Interface {self.instance_id}: {str(e)}")
            return False
    
    async def send_message(self, message: str, session_id: Optional[str] = None, 
                          config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send message to Claude through web interface"""
        
        if not self.is_initialized:
            await self.initialize()
        
        # Create or get session
        if not session_id:
            session_id = f"claude_session_{int(time.time())}_{self.instance_id}"
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "created_at": time.time(),
                "last_activity": time.time()
            }
        
        session = self.sessions[session_id]
        session["last_activity"] = time.time()
        
        try:
            # Wait for input field to be available
            await self.page.wait_for_selector(self.selectors["message_input"], timeout=self.timeout)
            
            # Clear any existing text and type new message
            input_field = self.page.locator(self.selectors["message_input"])
            await input_field.click()
            await input_field.fill("")
            await input_field.type(message, delay=50)  # Human-like typing
            
            # Click send button
            send_button = self.page.locator(self.selectors["send_button"])
            await send_button.click()
            
            # Wait for response to start appearing
            await self.page.wait_for_timeout(2000)
            
            # Wait for loading to complete
            try:
                await self.page.wait_for_selector(self.selectors["loading"], state="detached", timeout=60000)
            except:
                pass  # Continue if loading indicator doesn't appear
            
            # Extract Claude's response
            messages = await self.page.locator(self.selectors["messages"]).all()
            
            if messages:
                # Get the last message (Claude's response)
                last_message = messages[-1]
                response_text = await last_message.inner_text()
                
                # Add to session
                session["messages"].extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response_text}
                ])
                
                claude_response = {
                    "success": True,
                    "message": response_text,
                    "session_id": session_id,
                    "interface": "claude_web",
                    "instance_id": self.instance_id,
                    "ui_state": {
                        "input_area_state": "available",
                        "send_button_state": "enabled",
                        "response_complete": True
                    },
                    "timestamp": time.time()
                }
                
                self.logger.info(f"✅ Successfully processed message in Claude Web interface {self.instance_id}")
                return claude_response
                
            else:
                return {
                    "success": False,
                    "error": "No response received from Claude",
                    "message": "Sorry, I didn't receive a response from Claude.",
                    "session_id": session_id,
                    "interface": "claude_web",
                    "instance_id": self.instance_id
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error in Claude Web interface {self.instance_id}: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Sorry, I encountered an error communicating with Claude.",
                "session_id": session_id,
                "interface": "claude_web",
                "instance_id": self.instance_id
            }
    
    async def start_new_chat(self) -> bool:
        """Start a new chat session (click New Chat button)"""
        try:
            new_chat_button = self.page.locator(self.selectors["new_chat"])
            if await new_chat_button.is_visible():
                await new_chat_button.click()
                await self.page.wait_for_timeout(2000)
                return True
            return False
        except Exception as e:
            self.logger.error(f"❌ Error starting new chat: {str(e)}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Claude Web interface status"""
        try:
            # Check if page is responsive
            page_title = await self.page.title() if self.page else "No page"
            
            return {
                "healthy": self.is_initialized and self.page is not None,
                "interface": "claude_web",
                "instance_id": self.instance_id,
                "browser_connected": self.browser is not None,
                "page_title": page_title,
                "active_sessions": len(self.sessions),
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "healthy": False,
                "interface": "claude_web",
                "instance_id": self.instance_id,
                "error": str(e),
                "last_check": time.time()
            }
    
    def get_display_name(self) -> str:
        """Get display name"""
        return f"Claude Web ({self.instance_id})"
    
    def get_interface_type(self) -> str:
        """Get interface type"""
        return "claude_web"
    
    async def cleanup(self) -> None:
        """Cleanup Claude Web interface resources"""
        try:
            if self.page:
                await self.page.close()
            
            if self.browser:
                await self.browser.close()
            
            if self.playwright:
                await self.playwright.stop()
            
            self.sessions.clear()
            self.is_initialized = False
            
            self.logger.info(f"🧹 Claude Web Interface {self.instance_id} cleaned up")
            
        except Exception as e:
            self.logger.error(f"❌ Error during Claude Web interface cleanup: {str(e)}")
    
    async def take_screenshot(self, path: str = None) -> str:
        """Take screenshot of current page"""
        try:
            if not path:
                path = f"claude_screenshot_{self.instance_id}_{int(time.time())}.png"
            
            await self.page.screenshot(path=path)
            return path
        except Exception as e:
            self.logger.error(f"❌ Error taking screenshot: {str(e)}")
            return ""
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "session_id": session_id,
                "message_count": len(session["messages"]),
                "created_at": session["created_at"],
                "last_activity": session["last_activity"],
                "interface": "claude_web",
                "instance_id": self.instance_id
            }
        return None
