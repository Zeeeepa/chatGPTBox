"""
Unified Chat API Endpoints
Routes requests to appropriate AI providers (Codegen API, Gemini Web, Claude Web, etc.)
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from ..providers.base_provider import provider_manager, ProviderConfig, ProviderType, ChatMessage, MessageRole, WebUIElements
from ..providers.codegen_api_provider import CodegenAPIProvider
from ..providers.zai_web_provider import ZAIWebProvider
from ..providers.gemini_web_provider import GeminiWebProvider
from ..providers.claude_web_provider import ClaudeWebProvider
from ..providers.custom_web_provider import CustomWebProvider, create_custom_provider

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None
    stream: bool = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    content: str
    provider: str
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None

class ProviderStatus(BaseModel):
    name: str
    type: str
    initialized: bool
    healthy: bool
    model: Optional[str] = None

class CustomProviderConfig(BaseModel):
    name: str
    base_url: str
    input_selector: str
    send_button_selector: str
    response_selector: str
    new_chat_selector: Optional[str] = None
    send_button_states: Optional[Dict[str, str]] = None
    use_xpath: bool = False

# FastAPI app
app = FastAPI(
    title="ChatGPTBox-Style Multi-AI API",
    description="Unified API for multiple AI providers with web automation support",
    version="1.0.0"
)

# Global state
websocket_connections: Dict[str, WebSocket] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize all providers on startup"""
    logger.info("Initializing AI providers...")
    
    # Initialize Codegen API provider
    codegen_config = ProviderConfig(
        name="codegen-api",
        provider_type=ProviderType.API_BASED,
        api_key="your-codegen-api-key",  # Should come from environment
        base_url="https://api.codegen.com",
        model="gpt-4"
    )
    codegen_provider = CodegenAPIProvider(codegen_config)
    provider_manager.register_provider(codegen_provider, is_default=True)
    
    # Initialize Z.AI web provider
    zai_config = ProviderConfig(
        name="zai-web",
        provider_type=ProviderType.WEB_AUTOMATION,
        base_url="https://chat.z.ai"
    )
    zai_provider = ZAIWebProvider(zai_config)
    provider_manager.register_provider(zai_provider)
    
    # Initialize Gemini web provider
    gemini_config = ProviderConfig(
        name="gemini-web",
        provider_type=ProviderType.WEB_AUTOMATION,
        base_url="https://gemini.google.com"
    )
    gemini_provider = GeminiWebProvider(gemini_config)
    provider_manager.register_provider(gemini_provider)
    
    # Initialize Claude web provider
    claude_config = ProviderConfig(
        name="claude-web",
        provider_type=ProviderType.WEB_AUTOMATION,
        base_url="https://claude.ai"
    )
    claude_provider = ClaudeWebProvider(claude_config)
    provider_manager.register_provider(claude_provider)
    
    # Initialize predefined custom providers
    deepseek_provider = create_custom_provider("deepseek")
    provider_manager.register_provider(deepseek_provider)
    
    mistral_provider = create_custom_provider("mistral")
    provider_manager.register_provider(mistral_provider)
    
    # Initialize all providers
    await provider_manager.initialize_all()
    
    logger.info("All providers initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup all providers on shutdown"""
    logger.info("Cleaning up providers...")
    await provider_manager.cleanup_all()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ChatGPTBox-Style Multi-AI API",
        "version": "1.0.0",
        "providers": provider_manager.list_providers(),
        "endpoints": {
            "chat": "/v1/chat/completions",
            "stream": "/v1/chat/stream",
            "providers": "/v1/providers",
            "health": "/v1/health",
            "websocket": "/ws/{client_id}"
        }
    }

@app.get("/v1/providers", response_model=List[ProviderStatus])
async def list_providers():
    """List all available providers and their status"""
    providers = []
    health_results = await provider_manager.health_check_all()
    
    for name in provider_manager.list_providers():
        provider = provider_manager.get_provider(name)
        if provider:
            status = provider.get_status()
            status["healthy"] = health_results.get(name, False)
            providers.append(ProviderStatus(**status))
    
    return providers

@app.get("/v1/health")
async def health_check():
    """Health check endpoint"""
    health_results = await provider_manager.health_check_all()
    
    return {
        "status": "healthy" if any(health_results.values()) else "unhealthy",
        "providers": health_results,
        "timestamp": asyncio.get_event_loop().time()
    }

@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """Send a chat message to specified provider"""
    try:
        # Get provider
        provider = provider_manager.get_provider(request.provider)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider '{request.provider}' not found")
        
        # Convert conversation history
        conversation_history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                role = MessageRole(msg.get("role", "user"))
                content = msg.get("content", "")
                conversation_history.append(ChatMessage(role=role, content=content))
        
        # Send message
        response = await provider.send_message(request.message, conversation_history)
        
        return ChatResponse(
            content=response.content,
            provider=response.provider,
            model=response.model,
            usage=response.usage,
            metadata=response.metadata,
            success=response.success,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response from specified provider"""
    try:
        # Get provider
        provider = provider_manager.get_provider(request.provider)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider '{request.provider}' not found")
        
        # Convert conversation history
        conversation_history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                role = MessageRole(msg.get("role", "user"))
                content = msg.get("content", "")
                conversation_history.append(ChatMessage(role=role, content=content))
        
        async def generate_stream():
            try:
                async for chunk in provider.stream_message(request.message, conversation_history):
                    # Format as Server-Sent Events
                    yield f"data: {json.dumps({'content': chunk, 'provider': provider.name})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'content': '[DONE]', 'provider': provider.name})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                yield f"data: {json.dumps({'error': str(e), 'provider': provider.name})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in chat streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/providers/custom")
async def add_custom_provider(config: CustomProviderConfig):
    """Add a custom web provider"""
    try:
        # Create UI elements
        ui_elements = WebUIElements(
            input_selector=config.input_selector,
            send_button_selector=config.send_button_selector,
            response_selector=config.response_selector,
            new_chat_selector=config.new_chat_selector,
            send_button_states=config.send_button_states,
            use_xpath=config.use_xpath
        )
        
        # Create provider config
        provider_config = ProviderConfig(
            name=config.name,
            provider_type=ProviderType.CUSTOM_WEB,
            base_url=config.base_url
        )
        
        # Create and register provider
        custom_provider = CustomWebProvider(provider_config, ui_elements)
        provider_manager.register_provider(custom_provider)
        
        # Initialize the provider
        success = await custom_provider.initialize()
        
        return {
            "message": f"Custom provider '{config.name}' added successfully",
            "initialized": success,
            "provider": config.name
        }
        
    except Exception as e:
        logger.error(f"Error adding custom provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    websocket_connections[client_id] = websocket
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            provider_name = message_data.get("provider")
            message = message_data.get("message", "")
            
            # Get provider
            provider = provider_manager.get_provider(provider_name)
            if not provider:
                await websocket.send_text(json.dumps({
                    "error": f"Provider '{provider_name}' not found",
                    "type": "error"
                }))
                continue
            
            # Send typing indicator
            await websocket.send_text(json.dumps({
                "type": "typing",
                "provider": provider_name
            }))
            
            try:
                # Stream response
                async for chunk in provider.stream_message(message):
                    await websocket.send_text(json.dumps({
                        "type": "chunk",
                        "content": chunk,
                        "provider": provider_name
                    }))
                
                # Send completion
                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "provider": provider_name
                }))
                
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": str(e),
                    "provider": provider_name
                }))
                
    except WebSocketDisconnect:
        if client_id in websocket_connections:
            del websocket_connections[client_id]
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if client_id in websocket_connections:
            del websocket_connections[client_id]

@app.post("/v1/providers/{provider_name}/new-chat")
async def new_chat(provider_name: str):
    """Start a new chat session with specified provider"""
    try:
        provider = provider_manager.get_provider(provider_name)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
        
        # Check if provider supports new chat
        if hasattr(provider, 'new_chat'):
            success = await provider.new_chat()
            return {
                "message": f"New chat started with {provider_name}",
                "success": success
            }
        else:
            return {
                "message": f"Provider {provider_name} does not support new chat",
                "success": False
            }
            
    except Exception as e:
        logger.error(f"Error starting new chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/providers/{provider_name}/models")
async def get_provider_models(provider_name: str):
    """Get available models for specified provider"""
    try:
        provider = provider_manager.get_provider(provider_name)
        if not provider:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
        
        models = await provider.get_models()
        return {
            "provider": provider_name,
            "models": models
        }
        
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint for dynamic prompts
@app.post("/v1/test/dynamic-prompts")
async def test_dynamic_prompts(background_tasks: BackgroundTasks):
    """Test all providers with dynamic prompts"""
    
    async def run_tests():
        test_prompts = [
            "What is the capital of France?",
            "Explain machine learning in simple terms",
            "Write a Python function to reverse a string",
            "What are the benefits of renewable energy?",
            "How does blockchain technology work?"
        ]
        
        results = {}
        
        for provider_name in provider_manager.list_providers():
            provider = provider_manager.get_provider(provider_name)
            if not provider:
                continue
                
            provider_results = []
            
            for prompt in test_prompts:
                try:
                    response = await provider.send_message(prompt)
                    provider_results.append({
                        "prompt": prompt,
                        "success": response.success,
                        "response_length": len(response.content) if response.content else 0,
                        "error": response.error
                    })
                except Exception as e:
                    provider_results.append({
                        "prompt": prompt,
                        "success": False,
                        "response_length": 0,
                        "error": str(e)
                    })
            
            results[provider_name] = provider_results
        
        logger.info(f"Dynamic prompt test results: {results}")
    
    background_tasks.add_task(run_tests)
    
    return {
        "message": "Dynamic prompt testing started in background",
        "providers": provider_manager.list_providers()
    }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the server
    uvicorn.run(
        "src.api.chat_endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
