"""
⚙️ Configuration Manager
Manages configuration for different chat interfaces
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration for chat interfaces"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_cache: Dict[str, Any] = {}
        self.default_configs = self._load_default_configs()
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        logger.info(f"⚙️ ConfigManager initialized with config dir: {self.config_dir}")
    
    def _load_default_configs(self) -> Dict[str, Any]:
        """Load default configurations for all interfaces"""
        return {
            "claude_web": {
                "claude_url": "https://claude.ai/chat",
                "headless": True,
                "timeout": 30000
            },
            "copilot_code": {
                "copilot_url": "https://github.com/features/copilot",
                "github_url": "https://github.com",
                "headless": True,
                "timeout": 30000
            },
            "zai": {
                "zai_base_url": "https://z.ai",
                "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
                "openai_base_url": "https://api.openai.com/v1",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "openai_proxy": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "rate_limit": 60
            }
        }
    
    def get_interface_config(self, interface_type: str, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific interface"""
        
        # Create cache key
        cache_key = f"{interface_type}_{instance_id}" if instance_id else interface_type
        
        # Check cache first
        if cache_key in self.config_cache:
            return self.config_cache[cache_key].copy()
        
        # Load from file or use defaults
        config = self._load_config_from_file(interface_type, instance_id)
        
        if not config:
            config = self.default_configs.get(interface_type, {}).copy()
        
        # Apply instance-specific overrides for Z.AI instances
        if interface_type == "zai" and instance_id:
            config = self._apply_zai_instance_config(config, instance_id)
        
        # Cache the config
        self.config_cache[cache_key] = config.copy()
        
        logger.info(f"📋 Loaded config for {cache_key}")
        return config
    
    def _apply_zai_instance_config(self, base_config: Dict[str, Any], instance_id: str) -> Dict[str, Any]:
        """Apply instance-specific configuration for Z.AI instances"""
        config = base_config.copy()
        
        # Different configurations for each Z.AI instance
        if instance_id == "zai_instance_1":
            config.update({
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "instance_name": "Z.AI GPT-4 Standard"
            })
        elif instance_id == "zai_instance_2":
            config.update({
                "model": "gpt-3.5-turbo",
                "temperature": 0.5,
                "max_tokens": 1500,
                "instance_name": "Z.AI GPT-3.5 Fast"
            })
        elif instance_id == "zai_instance_3":
            config.update({
                "model": "gpt-4",
                "temperature": 0.9,
                "max_tokens": 3000,
                "instance_name": "Z.AI GPT-4 Creative"
            })
        
        return config
    
    def _load_config_from_file(self, interface_type: str, instance_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load configuration from file"""
        
        # Try instance-specific config first
        if instance_id:
            instance_file = self.config_dir / f"{interface_type}_{instance_id}.json"
            if instance_file.exists():
                try:
                    with open(instance_file, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"❌ Error loading config from {instance_file}: {str(e)}")
        
        # Try general interface config
        interface_file = self.config_dir / f"{interface_type}.json"
        if interface_file.exists():
            try:
                with open(interface_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ Error loading config from {interface_file}: {str(e)}")
        
        return None
    
    def save_interface_config(self, interface_type: str, config: Dict[str, Any], 
                            instance_id: Optional[str] = None) -> bool:
        """Save configuration for a specific interface"""
        
        try:
            # Determine filename
            if instance_id:
                filename = f"{interface_type}_{instance_id}.json"
            else:
                filename = f"{interface_type}.json"
            
            config_file = self.config_dir / filename
            
            # Save to file
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Update cache
            cache_key = f"{interface_type}_{instance_id}" if instance_id else interface_type
            self.config_cache[cache_key] = config.copy()
            
            logger.info(f"💾 Saved config for {cache_key} to {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving config: {str(e)}")
            return False
    
    def update_interface_config(self, interface_type: str, updates: Dict[str, Any], 
                              instance_id: Optional[str] = None) -> bool:
        """Update configuration for a specific interface"""
        
        # Get current config
        current_config = self.get_interface_config(interface_type, instance_id)
        
        # Apply updates
        current_config.update(updates)
        
        # Save updated config
        return self.save_interface_config(interface_type, current_config, instance_id)
    
    def delete_interface_config(self, interface_type: str, instance_id: Optional[str] = None) -> bool:
        """Delete configuration for a specific interface"""
        
        try:
            # Determine filename
            if instance_id:
                filename = f"{interface_type}_{instance_id}.json"
            else:
                filename = f"{interface_type}.json"
            
            config_file = self.config_dir / filename
            
            # Delete file if exists
            if config_file.exists():
                config_file.unlink()
            
            # Remove from cache
            cache_key = f"{interface_type}_{instance_id}" if instance_id else interface_type
            if cache_key in self.config_cache:
                del self.config_cache[cache_key]
            
            logger.info(f"🗑️ Deleted config for {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting config: {str(e)}")
            return False
    
    def list_interface_configs(self) -> Dict[str, Any]:
        """List all available interface configurations"""
        
        configs = {}
        
        # Add default configs
        for interface_type in self.default_configs:
            configs[interface_type] = {
                "type": interface_type,
                "source": "default",
                "instances": []
            }
        
        # Scan config directory for custom configs
        if self.config_dir.exists():
            for config_file in self.config_dir.glob("*.json"):
                filename = config_file.stem
                
                if "_" in filename:
                    # Instance-specific config
                    interface_type, instance_id = filename.split("_", 1)
                    if interface_type not in configs:
                        configs[interface_type] = {
                            "type": interface_type,
                            "source": "custom",
                            "instances": []
                        }
                    configs[interface_type]["instances"].append(instance_id)
                else:
                    # General interface config
                    interface_type = filename
                    if interface_type not in configs:
                        configs[interface_type] = {
                            "type": interface_type,
                            "source": "custom",
                            "instances": []
                        }
                    configs[interface_type]["source"] = "custom"
        
        return configs
    
    def clear_cache(self) -> None:
        """Clear configuration cache"""
        self.config_cache.clear()
        logger.info("🧹 Configuration cache cleared")
    
    def reload_config(self, interface_type: str, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Reload configuration from file"""
        
        # Remove from cache
        cache_key = f"{interface_type}_{instance_id}" if instance_id else interface_type
        if cache_key in self.config_cache:
            del self.config_cache[cache_key]
        
        # Load fresh config
        return self.get_interface_config(interface_type, instance_id)
    
    def validate_config(self, interface_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration for a specific interface"""
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Interface-specific validation
        if interface_type == "zai":
            if not config.get("openai_api_key"):
                validation_result["errors"].append("OpenAI API key is required for Z.AI interface")
            
            if not config.get("model"):
                validation_result["errors"].append("Model is required for Z.AI interface")
        
        elif interface_type == "openai_proxy":
            if not config.get("api_key"):
                validation_result["errors"].append("API key is required for OpenAI Proxy interface")
            
            if not config.get("base_url"):
                validation_result["errors"].append("Base URL is required for OpenAI Proxy interface")
        
        elif interface_type == "claude_web":
            if not config.get("claude_url"):
                validation_result["errors"].append("Claude URL is required for Claude Web interface")
        
        elif interface_type == "copilot_code":
            if not config.get("github_url"):
                validation_result["errors"].append("GitHub URL is required for Copilot Code interface")
        
        # Set valid flag
        validation_result["valid"] = len(validation_result["errors"]) == 0
        
        return validation_result
    
    def get_environment_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables"""
        
        overrides = {}
        
        # Common environment variables
        env_mappings = {
            "OPENAI_API_KEY": ["zai.openai_api_key", "openai_proxy.api_key"],
            "CLAUDE_URL": ["claude_web.claude_url"],
            "GITHUB_URL": ["copilot_code.github_url"],
            "HEADLESS_BROWSER": ["claude_web.headless", "copilot_code.headless"],
            "BROWSER_TIMEOUT": ["claude_web.timeout", "copilot_code.timeout"]
        }
        
        for env_var, config_paths in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                for path in config_paths:
                    interface_type, config_key = path.split(".", 1)
                    if interface_type not in overrides:
                        overrides[interface_type] = {}
                    
                    # Convert string values to appropriate types
                    if config_key in ["headless"]:
                        overrides[interface_type][config_key] = env_value.lower() in ["true", "1", "yes"]
                    elif config_key in ["timeout"]:
                        try:
                            overrides[interface_type][config_key] = int(env_value)
                        except ValueError:
                            logger.warning(f"⚠️ Invalid integer value for {env_var}: {env_value}")
                    else:
                        overrides[interface_type][config_key] = env_value
        
        return overrides
