"""
Codegen API Provider
Routes requests to Codegen API for OpenAI, Anthropic, and Gemini endpoints
"""

import aiohttp
import json
import logging
from typing import List, AsyncGenerator, Dict, Any, Optional
from .base_provider import BaseProvider, ProviderConfig, ProviderResponse, ChatMessage, MessageRole, ProviderType

logger = logging.getLogger(__name__)

class CodegenAPIProvider(BaseProvider):
    """Provider that routes requests to Codegen API"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_base = config.base_url or "https://api.codegen.com"
        self.api_key = config.api_key
        
    async def initialize(self) -> bool:
        """Initialize HTTP session and test connection"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "ChatGPTBox-WebAPI/1.0"
                }
            )
            
            # Test connection
            health_ok = await self.health_check()
            self.is_initialized = health_ok
            return health_ok
            
        except Exception as e:
            logger.error(f"Failed to initialize Codegen API provider: {e}")
            return False
    
    async def send_message(self, message: str, conversation_history: List[ChatMessage] = None) -> ProviderResponse:
        """Send message to Codegen API"""
        try:
            # Prepare messages in OpenAI format
            messages = []
            if conversation_history:
                for msg in conversation_history:
                    messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
            
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Prepare request payload
            payload = {
                "model": self.config.model or "gpt-4",
                "messages": messages,
                "temperature": self.config.temperature,
                "stream": False
            }
            
            if self.config.max_tokens:
                payload["max_tokens"] = self.config.max_tokens
            
            # Make API request
            async with self.session.post(
                f"{self.api_base}/v1/chat/completions",
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract response content
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    model = data.get("model", self.config.model)
                    
                    return ProviderResponse(
                        content=content,
                        provider=self.name,
                        model=model,
                        usage=usage,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Codegen API error {response.status}: {error_text}")
                    return ProviderResponse(
                        content="",
                        provider=self.name,
                        error=f"API Error {response.status}: {error_text}",
                        success=False
                    )
                    
        except Exception as e:
            logger.error(f"Error sending message to Codegen API: {e}")
            return ProviderResponse(
                content="",
                provider=self.name,
                error=str(e),
                success=False
            )
    
    async def stream_message(self, message: str, conversation_history: List[ChatMessage] = None) -> AsyncGenerator[str, None]:
        """Stream message response from Codegen API"""
        try:
            # Prepare messages
            messages = []
            if conversation_history:
                for msg in conversation_history:
                    messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
            
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Prepare streaming request
            payload = {
                "model": self.config.model or "gpt-4",
                "messages": messages,
                "temperature": self.config.temperature,
                "stream": True
            }
            
            if self.config.max_tokens:
                payload["max_tokens"] = self.config.max_tokens
            
            # Make streaming request
            async with self.session.post(
                f"{self.api_base}/v1/chat/completions",
                json=payload
            ) as response:
                
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            if data_str == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    yield f"Error {response.status}: {error_text}"
                    
        except Exception as e:
            logger.error(f"Error streaming from Codegen API: {e}")
            yield f"Error: {str(e)}"
    
    async def get_models(self) -> List[str]:
        """Get available models from Codegen API"""
        try:
            async with self.session.get(f"{self.api_base}/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model["id"] for model in data.get("data", [])]
                    return models
                else:
                    logger.error(f"Failed to get models: {response.status}")
                    return ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "gemini-pro"]
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "gemini-pro"]
    
    async def health_check(self) -> bool:
        """Check if Codegen API is accessible"""
        try:
            if not self.session:
                return False
                
            async with self.session.get(f"{self.api_base}/v1/models") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def cleanup(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

# Test function for dynamic prompts
async def test_codegen_api():
    """Test Codegen API with dynamic prompts"""
    config = ProviderConfig(
        name="codegen-api",
        provider_type=ProviderType.API_BASED,
        api_key="your-codegen-api-key",  # Replace with actual key
        base_url="https://api.codegen.com",
        model="gpt-4",
        temperature=0.7
    )
    
    provider = CodegenAPIProvider(config)
    
    try:
        # Initialize
        print("🔄 Initializing Codegen API provider...")
        success = await provider.initialize()
        print(f"✅ Initialization: {'Success' if success else 'Failed'}")
        
        if not success:
            return
        
        # Test health check
        print("🔄 Testing health check...")
        healthy = await provider.health_check()
        print(f"✅ Health check: {'Healthy' if healthy else 'Unhealthy'}")
        
        # Test get models
        print("🔄 Getting available models...")
        models = await provider.get_models()
        print(f"✅ Available models: {models}")
        
        # Test dynamic prompts
        test_prompts = [
            "What is the capital of France?",
            "Explain quantum computing in simple terms",
            "Write a Python function to calculate fibonacci numbers",
            "What are the latest developments in AI?",
            "How do I implement a REST API in FastAPI?"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n🔄 Test {i}: {prompt}")
            
            # Test regular message
            response = await provider.send_message(prompt)
            if response.success:
                print(f"✅ Response: {response.content[:200]}...")
                if response.usage:
                    print(f"📊 Usage: {response.usage}")
            else:
                print(f"❌ Error: {response.error}")
            
            # Test streaming (for first prompt only)
            if i == 1:
                print("🔄 Testing streaming response...")
                stream_content = ""
                async for chunk in provider.stream_message(prompt):
                    stream_content += chunk
                    print(chunk, end="", flush=True)
                print(f"\n✅ Streaming complete. Total length: {len(stream_content)}")
        
        # Test follow-up conversation
        print("\n🔄 Testing follow-up conversation...")
        conversation = [
            ChatMessage(role=MessageRole.USER, content="What is Python?"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Python is a high-level programming language...")
        ]
        
        followup_response = await provider.send_message(
            "Can you give me a simple Python example?", 
            conversation_history=conversation
        )
        
        if followup_response.success:
            print(f"✅ Follow-up response: {followup_response.content[:200]}...")
        else:
            print(f"❌ Follow-up error: {followup_response.error}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await provider.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_codegen_api())
