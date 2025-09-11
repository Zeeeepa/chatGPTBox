"""
🤖 Z.AI Interface Implementation
Connects Z.AI WebUI to OpenAI API with full compatibility
"""

import asyncio
import json
import logging
import aiohttp
import time
from typing import Dict, Any, Optional, List
from .base_interface import BaseInterface

logger = logging.getLogger(__name__)

class ZAIInterface(BaseInterface):
    """Z.AI WebUI interface with OpenAI API compatibility"""
    
    def __init__(self, instance_id: str, config: Dict[str, Any]):
        super().__init__(instance_id, config)
        
        # Z.AI specific configuration
        self.zai_base_url = config.get("zai_base_url", "https://z.ai")
        self.openai_api_key = config.get("openai_api_key", "")
        self.openai_base_url = config.get("openai_base_url", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        
        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session = None
        
        # Z.AI WebUI elements (from your HTML example)
        self.ui_elements = {
            "chat_input": "#chat-input",
            "send_button": "#send-message-button",
            "response_area": ".chat-messages",
            "new_chat_button": ".new-chat-button"
        }
        
        self.logger.info(f"🤖 Z.AI Interface {instance_id} initialized")
    
    async def initialize(self) -> bool:
        """Initialize Z.AI interface and OpenAI connection"""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={
                    "User-Agent": "Z.AI-WebUI-Interface/1.0",
                    "Content-Type": "application/json"
                }
            )
            
            # Test OpenAI API connection
            if self.openai_api_key:
                await self._test_openai_connection()
            
            self.is_initialized = True
            self.logger.info(f"✅ Z.AI Interface {self.instance_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Z.AI Interface {self.instance_id}: {str(e)}")
            return False
    
    async def _test_openai_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple completion request
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            async with self.session.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=test_payload
            ) as response:
                if response.status == 200:
                    self.logger.info(f"✅ OpenAI API connection test successful for {self.instance_id}")
                    return True
                else:
                    self.logger.warning(f"⚠️ OpenAI API test returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ OpenAI API connection test failed: {str(e)}")
            return False
    
    async def send_message(self, message: str, session_id: Optional[str] = None, 
                          config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send message through Z.AI interface to OpenAI API"""
        
        if not self.is_initialized:
            await self.initialize()
        
        # Create or get session
        if not session_id:
            session_id = f"zai_session_{int(time.time())}_{self.instance_id}"
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "created_at": time.time(),
                "last_activity": time.time()
            }
        
        session = self.sessions[session_id]
        session["last_activity"] = time.time()
        
        # Add user message to session
        user_message = {"role": "user", "content": message}
        session["messages"].append(user_message)
        
        try:
            # Prepare OpenAI API request
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            # Use config overrides if provided
            model = config.get("model", self.model) if config else self.model
            temperature = config.get("temperature", self.temperature) if config else self.temperature
            max_tokens = config.get("max_tokens", self.max_tokens) if config else self.max_tokens
            
            payload = {
                "model": model,
                "messages": session["messages"],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False  # We'll handle streaming separately if needed
            }
            
            self.logger.info(f"🤖 Sending message to OpenAI API via Z.AI interface {self.instance_id}")
            
            # Send request to OpenAI API
            async with self.session.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    # Extract assistant response
                    assistant_message = response_data["choices"][0]["message"]["content"]
                    
                    # Add assistant response to session
                    session["messages"].append({
                        "role": "assistant", 
                        "content": assistant_message
                    })
                    
                    # Prepare Z.AI style response
                    zai_response = {
                        "success": True,
                        "message": assistant_message,
                        "session_id": session_id,
                        "interface": "zai",
                        "instance_id": self.instance_id,
                        "model": model,
                        "usage": response_data.get("usage", {}),
                        "ui_state": {
                            "input_area_state": "available",
                            "send_button_state": "enabled",
                            "response_complete": True
                        },
                        "timestamp": time.time()
                    }
                    
                    self.logger.info(f"✅ Successfully processed message in Z.AI interface {self.instance_id}")
                    return zai_response
                    
                else:
                    error_text = await response.text()
                    self.logger.error(f"❌ OpenAI API error {response.status}: {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"OpenAI API error: {response.status}",
                        "message": "Sorry, I encountered an error processing your request.",
                        "session_id": session_id,
                        "interface": "zai",
                        "instance_id": self.instance_id,
                        "ui_state": {
                            "input_area_state": "available",
                            "send_button_state": "enabled",
                            "response_complete": True
                        }
                    }
                    
        except Exception as e:
            self.logger.error(f"❌ Error in Z.AI interface {self.instance_id}: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Sorry, I encountered an unexpected error.",
                "session_id": session_id,
                "interface": "zai",
                "instance_id": self.instance_id,
                "ui_state": {
                    "input_area_state": "available",
                    "send_button_state": "enabled",
                    "response_complete": True
                }
            }
    
    async def send_streaming_message(self, message: str, session_id: Optional[str] = None) -> AsyncIterator[Dict[str, Any]]:
        """Send message with streaming response (Z.AI style)"""
        
        if not session_id:
            session_id = f"zai_session_{int(time.time())}_{self.instance_id}"
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "created_at": time.time(),
                "last_activity": time.time()
            }
        
        session = self.sessions[session_id]
        session["messages"].append({"role": "user", "content": message})
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": session["messages"],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": True
            }
            
            async with self.session.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    full_response = ""
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('data: '):
                            data = line[6:]
                            
                            if data == '[DONE]':
                                # Final response
                                session["messages"].append({
                                    "role": "assistant",
                                    "content": full_response
                                })
                                
                                yield {
                                    "type": "stream_complete",
                                    "session_id": session_id,
                                    "interface": "zai",
                                    "instance_id": self.instance_id,
                                    "full_response": full_response
                                }
                                break
                            
                            try:
                                chunk_data = json.loads(data)
                                delta = chunk_data["choices"][0]["delta"]
                                
                                if "content" in delta:
                                    content = delta["content"]
                                    full_response += content
                                    
                                    yield {
                                        "type": "stream_chunk",
                                        "content": content,
                                        "session_id": session_id,
                                        "interface": "zai",
                                        "instance_id": self.instance_id
                                    }
                                    
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            yield {
                "type": "stream_error",
                "error": str(e),
                "session_id": session_id,
                "interface": "zai",
                "instance_id": self.instance_id
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Z.AI interface status"""
        return {
            "healthy": self.is_initialized,
            "interface": "zai",
            "instance_id": self.instance_id,
            "openai_connected": bool(self.openai_api_key),
            "active_sessions": len(self.sessions),
            "model": self.model,
            "ui_elements": self.ui_elements,
            "last_check": time.time()
        }
    
    def get_display_name(self) -> str:
        """Get display name"""
        return f"Z.AI WebUI ({self.instance_id})"
    
    def get_interface_type(self) -> str:
        """Get interface type"""
        return "zai"
    
    async def cleanup(self) -> None:
        """Cleanup Z.AI interface resources"""
        try:
            if self.session:
                await self.session.close()
            
            self.sessions.clear()
            self.is_initialized = False
            
            self.logger.info(f"🧹 Z.AI Interface {self.instance_id} cleaned up")
            
        except Exception as e:
            self.logger.error(f"❌ Error during Z.AI interface cleanup: {str(e)}")
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "session_id": session_id,
                "message_count": len(session["messages"]),
                "created_at": session["created_at"],
                "last_activity": session["last_activity"],
                "interface": "zai",
                "instance_id": self.instance_id
            }
        return None
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session (like clicking new chat button)"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"🗑️ Cleared session {session_id} in Z.AI interface {self.instance_id}")
            return True
        return False
    
    def get_ui_state(self) -> Dict[str, Any]:
        """Get current UI state (mimics Z.AI WebUI state)"""
        return {
            "input_area": {
                "placeholder": "How can I help you today?",
                "enabled": True,
                "height": "72px"
            },
            "send_button": {
                "enabled": True,
                "state": "ready"
            },
            "interface_type": "zai",
            "instance_id": self.instance_id,
            "model": self.model
        }
