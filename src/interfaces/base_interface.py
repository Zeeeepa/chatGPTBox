"""
🔧 Base Interface Class
Abstract base class for all chat interfaces
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

class BaseInterface(ABC):
    """Abstract base class for all chat interfaces"""
    
    def __init__(self, instance_id: str, config: Dict[str, Any]):
        self.instance_id = instance_id
        self.config = config
        self.is_initialized = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{instance_id}")
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the interface"""
        pass
    
    @abstractmethod
    async def send_message(self, message: str, session_id: Optional[str] = None, 
                          config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a message and return response"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get current interface status"""
        pass
    
    @abstractmethod
    def get_display_name(self) -> str:
        """Get human-readable display name"""
        pass
    
    @abstractmethod
    def get_interface_type(self) -> str:
        """Get interface type identifier"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Get interface configuration"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update interface configuration"""
        self.config.update(new_config)
        self.logger.info(f"Configuration updated for {self.instance_id}")
    
    async def health_check(self) -> bool:
        """Basic health check"""
        try:
            status = await self.get_status()
            return status.get("healthy", False)
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
