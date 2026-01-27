#!/usr/bin/env python3
"""
Simple client example for ChatGPTBox-style Multi-AI API
Demonstrates basic usage of the API endpoints
"""

import asyncio
import aiohttp
import json
import websockets
from typing import Dict, Any

class MultiAIClient:
    """Simple client for the Multi-AI API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def list_providers(self) -> Dict[str, Any]:
        """List all available providers"""
        async with self.session.get(f"{self.base_url}/v1/providers") as response:
            return await response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        async with self.session.get(f"{self.base_url}/v1/health") as response:
            return await response.json()
    
    async def send_message(self, message: str, provider: str, **kwargs) -> Dict[str, Any]:
        """Send a message to specified provider"""
        payload = {
            "message": message,
            "provider": provider,
            **kwargs
        }
        
        async with self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        ) as response:
            return await response.json()
    
    async def stream_message(self, message: str, provider: str, **kwargs):
        """Stream a message response from specified provider"""
        payload = {
            "message": message,
            "provider": provider,
            **kwargs
        }
        
        async with self.session.post(
            f"{self.base_url}/v1/chat/stream",
            json=payload
        ) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        break
                    try:
                        chunk_data = json.loads(data)
                        yield chunk_data.get('content', '')
                    except json.JSONDecodeError:
                        continue
    
    async def websocket_chat(self, provider: str, client_id: str = "example_client"):
        """Connect via WebSocket for real-time chat"""
        uri = f"ws://localhost:8000/ws/{client_id}"
        
        async with websockets.connect(uri) as websocket:
            print(f"Connected to WebSocket for provider: {provider}")
            
            # Send a message
            message_data = {
                "provider": provider,
                "message": "Hello via WebSocket!"
            }
            await websocket.send(json.dumps(message_data))
            
            # Listen for responses
            async for message in websocket:
                data = json.loads(message)
                
                if data.get('type') == 'chunk':
                    print(f"Chunk: {data.get('content', '')}", end="", flush=True)
                elif data.get('type') == 'complete':
                    print(f"\nResponse complete from {data.get('provider')}")
                    break
                elif data.get('type') == 'error':
                    print(f"Error: {data.get('error')}")
                    break
    
    async def add_custom_provider(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a custom web provider"""
        async with self.session.post(
            f"{self.base_url}/v1/providers/custom",
            json=config
        ) as response:
            return await response.json()
    
    async def new_chat(self, provider: str) -> Dict[str, Any]:
        """Start a new chat session"""
        async with self.session.post(
            f"{self.base_url}/v1/providers/{provider}/new-chat"
        ) as response:
            return await response.json()

async def main():
    """Main example function"""
    
    async with MultiAIClient() as client:
        print("🚀 ChatGPTBox-style Multi-AI API Client Example")
        print("=" * 50)
        
        # Check API health
        print("\n1. Health Check")
        health = await client.health_check()
        print(f"API Status: {health.get('status', 'unknown')}")
        
        # List providers
        print("\n2. Available Providers")
        providers = await client.list_providers()
        for provider in providers:
            status = "✅" if provider.get('healthy') else "❌"
            print(f"{status} {provider['name']} ({provider['type']})")
        
        # Test API-based provider (if available)
        print("\n3. Testing API Provider")
        try:
            response = await client.send_message(
                message="What is the capital of France?",
                provider="codegen-api"
            )
            if response.get('success'):
                print(f"Response: {response['content'][:200]}...")
            else:
                print(f"Error: {response.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"API provider test failed: {e}")
        
        # Test web automation provider (if available)
        print("\n4. Testing Web Provider")
        try:
            response = await client.send_message(
                message="Hello, how are you today?",
                provider="claude-web"
            )
            if response.get('success'):
                print(f"Response: {response['content'][:200]}...")
                print(f"UI State: {response.get('metadata', {}).get('ui_state', {})}")
            else:
                print(f"Error: {response.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Web provider test failed: {e}")
        
        # Test streaming
        print("\n5. Testing Streaming Response")
        try:
            print("Streaming response: ", end="", flush=True)
            async for chunk in client.stream_message(
                message="Count from 1 to 5",
                provider="codegen-api"
            ):
                print(chunk, end="", flush=True)
            print("\nStreaming complete!")
        except Exception as e:
            print(f"Streaming test failed: {e}")
        
        # Test custom provider addition
        print("\n6. Adding Custom Provider")
        try:
            custom_config = {
                "name": "example-custom",
                "base_url": "https://chat.openai.com/",
                "input_selector": "textarea[data-id='root']",
                "send_button_selector": "button[data-testid='send-button']",
                "response_selector": ".markdown",
                "new_chat_selector": "a[href='/']"
            }
            
            result = await client.add_custom_provider(custom_config)
            print(f"Custom provider added: {result.get('message', 'Success')}")
        except Exception as e:
            print(f"Custom provider test failed: {e}")
        
        # Test WebSocket (commented out as it requires manual interaction)
        print("\n7. WebSocket Test (Skipped - requires manual interaction)")
        # try:
        #     await client.websocket_chat("claude-web")
        # except Exception as e:
        #     print(f"WebSocket test failed: {e}")
        
        # Test new chat functionality
        print("\n8. Testing New Chat")
        try:
            result = await client.new_chat("claude-web")
            print(f"New chat result: {result.get('message', 'Success')}")
        except Exception as e:
            print(f"New chat test failed: {e}")
        
        print("\n✅ Example completed!")

if __name__ == "__main__":
    asyncio.run(main())
