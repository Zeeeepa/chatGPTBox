#!/usr/bin/env python3
"""
🚀 Multi-Chat WebUI Hub
A unified interface for accessing different AI chat clients
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our chat interfaces
from interfaces.claude_web import ClaudeWebInterface
from interfaces.copilot_code import CopilotCodeInterface
from interfaces.zai_interface import ZAIInterface
from interfaces.openai_proxy import OpenAIProxyInterface
from utils.config_manager import ConfigManager
from utils.session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Chat WebUI Hub",
    description="Unified interface for accessing different AI chat clients",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
config_manager = ConfigManager()
session_manager = SessionManager()

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Chat interface instances
chat_interfaces: Dict[str, Any] = {}

class ChatRequest(BaseModel):
    interface_type: str
    instance_id: str
    message: str
    session_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class InterfaceConfig(BaseModel):
    interface_type: str
    instance_id: str
    config: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize chat interfaces on startup"""
    logger.info("🚀 Starting Multi-Chat WebUI Hub...")
    
    # Initialize default interfaces
    await initialize_default_interfaces()
    
    logger.info("✅ Multi-Chat WebUI Hub started successfully!")

async def initialize_default_interfaces():
    """Initialize default chat interface instances"""
    
    # Initialize Claude Web interface
    chat_interfaces["claude_web_default"] = ClaudeWebInterface(
        instance_id="claude_web_default",
        config=config_manager.get_interface_config("claude_web")
    )
    
    # Initialize Copilot Code interface
    chat_interfaces["copilot_code_default"] = CopilotCodeInterface(
        instance_id="copilot_code_default",
        config=config_manager.get_interface_config("copilot_code")
    )
    
    # Initialize 3 separate Z.AI instances as requested
    for i in range(1, 4):
        instance_id = f"zai_instance_{i}"
        chat_interfaces[instance_id] = ZAIInterface(
            instance_id=instance_id,
            config=config_manager.get_interface_config("zai", instance_id)
        )
        logger.info(f"✅ Initialized Z.AI instance: {instance_id}")
    
    # Initialize OpenAI Proxy interface
    chat_interfaces["openai_proxy_default"] = OpenAIProxyInterface(
        instance_id="openai_proxy_default",
        config=config_manager.get_interface_config("openai_proxy")
    )

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main interface selector page"""
    available_interfaces = [
        {
            "id": "claude_web_default",
            "name": "Claude Web",
            "description": "Access Claude AI through web interface",
            "type": "claude_web",
            "status": "active" if "claude_web_default" in chat_interfaces else "inactive"
        },
        {
            "id": "copilot_code_default", 
            "name": "GitHub Copilot Code",
            "description": "Access GitHub Copilot for code assistance",
            "type": "copilot_code",
            "status": "active" if "copilot_code_default" in chat_interfaces else "inactive"
        },
        {
            "id": "zai_instance_1",
            "name": "Z.AI Instance #1",
            "description": "Z.AI WebUI connected to OpenAI API (Instance 1)",
            "type": "zai",
            "status": "active" if "zai_instance_1" in chat_interfaces else "inactive"
        },
        {
            "id": "zai_instance_2", 
            "name": "Z.AI Instance #2",
            "description": "Z.AI WebUI connected to OpenAI API (Instance 2)",
            "type": "zai",
            "status": "active" if "zai_instance_2" in chat_interfaces else "inactive"
        },
        {
            "id": "zai_instance_3",
            "name": "Z.AI Instance #3", 
            "description": "Z.AI WebUI connected to OpenAI API (Instance 3)",
            "type": "zai",
            "status": "active" if "zai_instance_3" in chat_interfaces else "inactive"
        },
        {
            "id": "openai_proxy_default",
            "name": "OpenAI Proxy",
            "description": "Direct OpenAI API access with proxy capabilities",
            "type": "openai_proxy",
            "status": "active" if "openai_proxy_default" in chat_interfaces else "inactive"
        }
    ]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "interfaces": available_interfaces,
        "title": "Multi-Chat WebUI Hub"
    })

@app.get("/interface/{interface_id}", response_class=HTMLResponse)
async def interface_page(request: Request, interface_id: str):
    """Individual interface page"""
    if interface_id not in chat_interfaces:
        raise HTTPException(status_code=404, detail="Interface not found")
    
    interface = chat_interfaces[interface_id]
    interface_info = {
        "id": interface_id,
        "name": interface.get_display_name(),
        "type": interface.get_interface_type(),
        "config": interface.get_config(),
        "status": await interface.get_status()
    }
    
    return templates.TemplateResponse("interface.html", {
        "request": request,
        "interface": interface_info,
        "title": f"{interface_info['name']} - Multi-Chat WebUI Hub"
    })

@app.post("/api/chat")
async def send_message(chat_request: ChatRequest):
    """Send message to specific chat interface"""
    interface_id = f"{chat_request.interface_type}_{chat_request.instance_id}"
    
    if interface_id not in chat_interfaces:
        raise HTTPException(status_code=404, detail="Interface not found")
    
    try:
        interface = chat_interfaces[interface_id]
        
        # Send message and get response
        response = await interface.send_message(
            message=chat_request.message,
            session_id=chat_request.session_id,
            config=chat_request.config
        )
        
        return JSONResponse({
            "success": True,
            "response": response,
            "interface_id": interface_id,
            "session_id": response.get("session_id")
        })
        
    except Exception as e:
        logger.error(f"Error sending message to {interface_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interface/create")
async def create_interface(interface_config: InterfaceConfig):
    """Create new interface instance"""
    interface_id = f"{interface_config.interface_type}_{interface_config.instance_id}"
    
    if interface_id in chat_interfaces:
        raise HTTPException(status_code=400, detail="Interface already exists")
    
    try:
        # Create interface based on type
        if interface_config.interface_type == "claude_web":
            interface = ClaudeWebInterface(
                instance_id=interface_config.instance_id,
                config=interface_config.config
            )
        elif interface_config.interface_type == "copilot_code":
            interface = CopilotCodeInterface(
                instance_id=interface_config.instance_id,
                config=interface_config.config
            )
        elif interface_config.interface_type == "zai":
            interface = ZAIInterface(
                instance_id=interface_config.instance_id,
                config=interface_config.config
            )
        elif interface_config.interface_type == "openai_proxy":
            interface = OpenAIProxyInterface(
                instance_id=interface_config.instance_id,
                config=interface_config.config
            )
        else:
            raise HTTPException(status_code=400, detail="Unknown interface type")
        
        chat_interfaces[interface_id] = interface
        await interface.initialize()
        
        return JSONResponse({
            "success": True,
            "interface_id": interface_id,
            "message": f"Interface {interface_id} created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating interface {interface_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/interface/{interface_id}")
async def delete_interface(interface_id: str):
    """Delete interface instance"""
    if interface_id not in chat_interfaces:
        raise HTTPException(status_code=404, detail="Interface not found")
    
    try:
        interface = chat_interfaces[interface_id]
        await interface.cleanup()
        del chat_interfaces[interface_id]
        
        return JSONResponse({
            "success": True,
            "message": f"Interface {interface_id} deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting interface {interface_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interfaces")
async def list_interfaces():
    """List all available interfaces"""
    interfaces_info = []
    
    for interface_id, interface in chat_interfaces.items():
        info = {
            "id": interface_id,
            "name": interface.get_display_name(),
            "type": interface.get_interface_type(),
            "status": await interface.get_status(),
            "config": interface.get_config()
        }
        interfaces_info.append(info)
    
    return JSONResponse({
        "success": True,
        "interfaces": interfaces_info
    })

@app.websocket("/ws/{interface_id}")
async def websocket_endpoint(websocket: WebSocket, interface_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    if interface_id not in chat_interfaces:
        await websocket.send_json({
            "error": "Interface not found",
            "interface_id": interface_id
        })
        await websocket.close()
        return
    
    interface = chat_interfaces[interface_id]
    session_id = session_manager.create_session(interface_id)
    
    try:
        await websocket.send_json({
            "type": "connection_established",
            "interface_id": interface_id,
            "session_id": session_id,
            "interface_name": interface.get_display_name()
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("type") == "chat_message":
                # Send message to interface
                response = await interface.send_message(
                    message=data.get("message", ""),
                    session_id=session_id,
                    config=data.get("config")
                )
                
                # Send response back to client
                await websocket.send_json({
                    "type": "chat_response",
                    "response": response,
                    "session_id": session_id
                })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for interface {interface_id}")
        session_manager.cleanup_session(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for interface {interface_id}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
        session_manager.cleanup_session(session_id)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "interfaces_count": len(chat_interfaces),
        "active_sessions": session_manager.get_active_sessions_count()
    })

if __name__ == "__main__":
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🚀 Starting Multi-Chat WebUI Hub on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
