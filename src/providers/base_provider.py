"""
Base Provider Interface for AI Chat Services
Unified interface for all AI providers (Gemini, Claude, OpenAI, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """Types of AI providers"""
    API_BASED = "api"           # Direct API calls (OpenAI, Anthropic API)
    WEB_AUTOMATION = "web"      # Browser automation (Claude web, Gemini web)
    HYBRID = "hybrid"           # Mix of API and web automation
    CUSTOM_WEB = "custom_web"   # Custom web interface with XPath selectors

class MessageRole(Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class ChatMessage:
    """Standardized chat message format"""
    role: MessageRole
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ProviderConfig:
    """Configuration for AI provider"""
    name: str
    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30
    rate_limit: Optional[int] = None
    custom_headers: Optional[Dict[str, str]] = None
    web_config: Optional[Dict[str, Any]] = None  # For web automation configs

@dataclass
class ProviderResponse:
    """Standardized response from AI provider"""
    content: str
    provider: str
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    success: bool = True

@dataclass
class WebUIElements:
    """Web UI element selectors for custom web providers"""
    input_selector: str
    send_button_selector: str
    response_selector: str
    new_chat_selector: Optional[str] = None
    send_button_states: Optional[Dict[str, str]] = None  # initial, progressing, ready
    use_xpath: bool = False

class BaseProvider(ABC):
    """Abstract base class for all AI providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        self.provider_type = config.provider_type
        self.session_data = {}
        self.is_initialized = False
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider (setup sessions, auth, etc.)"""
        pass
    
    @abstractmethod
    async def send_message(self, message: str, conversation_history: List[ChatMessage] = None) -> ProviderResponse:
        """Send a message and get response"""
        pass
    
    @abstractmethod
    async def stream_message(self, message: str, conversation_history: List[ChatMessage] = None) -> AsyncGenerator[str, None]:
        """Send a message and stream response"""
        pass
    
    @abstractmethod
    async def get_models(self) -> List[str]:
        """Get available models for this provider"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and accessible"""
        pass
    
    async def cleanup(self):
        """Cleanup resources (close sessions, browsers, etc.)"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get provider status information"""
        return {
            "name": self.name,
            "type": self.provider_type.value,
            "initialized": self.is_initialized,
            "model": self.config.model,
            "healthy": False  # Will be updated by health_check
        }

class ProviderManager:
    """Manages multiple AI providers"""
    
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self.default_provider: Optional[str] = None
        
    def register_provider(self, provider: BaseProvider, is_default: bool = False):
        """Register a new provider"""
        self.providers[provider.name] = provider
        if is_default or not self.default_provider:
            self.default_provider = provider.name
            
    def get_provider(self, name: Optional[str] = None) -> Optional[BaseProvider]:
        """Get provider by name or default"""
        if name is None:
            name = self.default_provider
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List all registered provider names"""
        return list(self.providers.keys())
    
    async def initialize_all(self):
        """Initialize all registered providers"""
        tasks = []
        for provider in self.providers.values():
            tasks.append(provider.initialize())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for provider_name, result in zip(self.providers.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Failed to initialize provider {provider_name}: {result}")
            else:
                logger.info(f"Provider {provider_name} initialized: {result}")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Health check all providers"""
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        return results
    
    async def cleanup_all(self):
        """Cleanup all providers"""
        for provider in self.providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error(f"Cleanup failed for {provider.name}: {e}")

# Global provider manager instance
provider_manager = ProviderManager()
