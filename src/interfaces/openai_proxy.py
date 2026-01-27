"""
🔗 OpenAI Proxy Interface Implementation
Direct OpenAI API access with proxy capabilities
"""

import asyncio
import json
import logging
import time
import aiohttp
from typing import Dict, Any, Optional, AsyncIterator
from .base_interface import BaseInterface

logger = logging.getLogger(__name__)

class OpenAIProxyInterface(BaseInterface):
    """OpenAI Proxy interface for direct API access"""
    
    def __init__(self, instance_id: str, config: Dict[str, Any]):
        super().__init__(instance_id, config)
        
        # OpenAI API configuration
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        
        # Proxy configuration
        self.proxy_url = config.get("proxy_url", None)
        self.proxy_headers = config.get("proxy_headers", {})
        
        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session = None
        
        # Rate limiting
        self.rate_limit = config.get("rate_limit", 60)  # requests per minute
        self.request_times = []
        
        self.logger.info(f"🔗 OpenAI Proxy Interface {instance_id} initialized")
    
    async def initialize(self) -> bool:
        """Initialize OpenAI Proxy interface"""
        try:
            # Create HTTP session
            connector = None
            if self.proxy_url:
                connector = aiohttp.TCPConnector()
            
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                connector=connector,
                headers={
                    "User-Agent": "OpenAI-Proxy-Interface/1.0",
                    "Content-Type": "application/json",
                    **self.proxy_headers
                }
            )
            
            # Test API connection
            if self.api_key:
                await self._test_api_connection()
            
            self.is_initialized = True
            self.logger.info(f"✅ OpenAI Proxy Interface {self.instance_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OpenAI Proxy Interface {self.instance_id}: {str(e)}")
            return False
    
    async def _test_api_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with models endpoint
            url = f"{self.base_url}/models"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    self.logger.info(f"✅ OpenAI API connection test successful for {self.instance_id}")
                    return True
                else:
                    self.logger.warning(f"⚠️ OpenAI API test returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ OpenAI API connection test failed: {str(e)}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.rate_limit:
            return False
        
        self.request_times.append(now)
        return True
    
    async def send_message(self, message: str, session_id: Optional[str] = None, 
                          config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send message through OpenAI Proxy interface"""
        
        if not self.is_initialized:
            await self.initialize()
        
        # Check rate limit
        if not self._check_rate_limit():
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please wait before sending another message.",
                "session_id": session_id,
                "interface": "openai_proxy",
                "instance_id": self.instance_id
            }
        
        # Create or get session
        if not session_id:
            session_id = f"openai_session_{int(time.time())}_{self.instance_id}"
        
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
                "Authorization": f"Bearer {self.api_key}",
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
                "stream": False
            }
            
            self.logger.info(f"🔗 Sending message to OpenAI API via proxy {self.instance_id}")
            
            # Send request to OpenAI API
            url = f"{self.base_url}/chat/completions"
            
            async with self.session.post(url, headers=headers, json=payload) as response:
                
                if response.status == 200:
                    response_data = await response.json()
                    
                    # Extract assistant response
                    assistant_message = response_data["choices"][0]["message"]["content"]
                    
                    # Add assistant response to session
                    session["messages"].append({
                        "role": "assistant", 
                        "content": assistant_message
                    })
                    
                    # Prepare response
                    proxy_response = {
                        "success": True,
                        "message": assistant_message,
                        "session_id": session_id,
                        "interface": "openai_proxy",
                        "instance_id": self.instance_id,
                        "model": model,
                        "usage": response_data.get("usage", {}),
                        "response_metadata": {
                            "finish_reason": response_data["choices"][0].get("finish_reason"),
                            "response_time": time.time() - session["last_activity"]
                        },
                        "ui_state": {
                            "input_area_state": "available",
                            "send_button_state": "enabled",
                            "response_complete": True
                        },
                        "timestamp": time.time()
                    }
                    
                    self.logger.info(f"✅ Successfully processed message in OpenAI Proxy interface {self.instance_id}")
                    return proxy_response
                    
                else:
                    error_text = await response.text()
                    self.logger.error(f"❌ OpenAI API error {response.status}: {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"OpenAI API error: {response.status}",
                        "message": "Sorry, I encountered an error processing your request.",
                        "session_id": session_id,
                        "interface": "openai_proxy",
                        "instance_id": self.instance_id,
                        "ui_state": {
                            "input_area_state": "available",
                            "send_button_state": "enabled",
                            "response_complete": True
                        }
                    }
                    
        except Exception as e:
            self.logger.error(f"❌ Error in OpenAI Proxy interface {self.instance_id}: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Sorry, I encountered an unexpected error.",
                "session_id": session_id,
                "interface": "openai_proxy",
                "instance_id": self.instance_id,
                "ui_state": {
                    "input_area_state": "available",
                    "send_button_state": "enabled",
                    "response_complete": True
                }
            }
    
    async def send_streaming_message(self, message: str, session_id: Optional[str] = None) -> AsyncIterator[Dict[str, Any]]:
        """Send message with streaming response"""
        
        if not self._check_rate_limit():
            yield {
                "type": "stream_error",
                "error": "Rate limit exceeded",
                "session_id": session_id,
                "interface": "openai_proxy",
                "instance_id": self.instance_id
            }
            return
        
        if not session_id:
            session_id = f"openai_session_{int(time.time())}_{self.instance_id}"
        
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
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": session["messages"],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": True
            }
            
            url = f"{self.base_url}/chat/completions"
            
            async with self.session.post(url, headers=headers, json=payload) as response:
                
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
                                    "interface": "openai_proxy",
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
                                        "interface": "openai_proxy",
                                        "instance_id": self.instance_id
                                    }
                                    
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            yield {
                "type": "stream_error",
                "error": str(e),
                "session_id": session_id,
                "interface": "openai_proxy",
                "instance_id": self.instance_id
            }
    
    async def list_models(self) -> Dict[str, Any]:
        """List available OpenAI models"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/models"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    models_data = await response.json()
                    return {
                        "success": True,
                        "models": models_data.get("data", []),
                        "interface": "openai_proxy",
                        "instance_id": self.instance_id
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to fetch models: {response.status}",
                        "interface": "openai_proxy",
                        "instance_id": self.instance_id
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "interface": "openai_proxy",
                "instance_id": self.instance_id
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get OpenAI Proxy interface status"""
        return {
            "healthy": self.is_initialized,
            "interface": "openai_proxy",
            "instance_id": self.instance_id,
            "api_connected": bool(self.api_key),
            "active_sessions": len(self.sessions),
            "model": self.model,
            "rate_limit": self.rate_limit,
            "requests_in_last_minute": len(self.request_times),
            "proxy_enabled": bool(self.proxy_url),
            "last_check": time.time()
        }
    
    def get_display_name(self) -> str:
        """Get display name"""
        return f"OpenAI Proxy ({self.instance_id})"
    
    def get_interface_type(self) -> str:
        """Get interface type"""
        return "openai_proxy"
    
    async def cleanup(self) -> None:
        """Cleanup OpenAI Proxy interface resources"""
        try:
            if self.session:
                await self.session.close()
            
            self.sessions.clear()
            self.request_times.clear()
            self.is_initialized = False
            
            self.logger.info(f"🧹 OpenAI Proxy Interface {self.instance_id} cleaned up")
            
        except Exception as e:
            self.logger.error(f"❌ Error during OpenAI Proxy interface cleanup: {str(e)}")
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "session_id": session_id,
                "message_count": len(session["messages"]),
                "created_at": session["created_at"],
                "last_activity": session["last_activity"],
                "interface": "openai_proxy",
                "instance_id": self.instance_id
            }
        return None
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"🗑️ Cleared session {session_id} in OpenAI Proxy interface {self.instance_id}")
            return True
        return False
