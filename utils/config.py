"""
Configuration management for AI Meeting Assistant.
"""
import os
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration manager for the AI Meeting Assistant."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._override_with_env_vars()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Dict containing configuration values.
        """
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_path} not found. Using default values.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return {}
    
    def _override_with_env_vars(self) -> None:
        """Override configuration values with environment variables."""
        # API Keys
        if os.getenv("OPENAI_API_KEY"):
            self.set_nested_value(["api_keys", "openai", "api_key"], os.getenv("OPENAI_API_KEY"))
        
        if os.getenv("GOOGLE_CLIENT_ID"):
            self.set_nested_value(["api_keys", "google", "client_id"], os.getenv("GOOGLE_CLIENT_ID"))
        
        if os.getenv("GOOGLE_CLIENT_SECRET"):
            self.set_nested_value(["api_keys", "google", "client_secret"], os.getenv("GOOGLE_CLIENT_SECRET"))
        
        if os.getenv("AWS_ACCESS_KEY_ID"):
            self.set_nested_value(["api_keys", "aws", "access_key_id"], os.getenv("AWS_ACCESS_KEY_ID"))
        
        if os.getenv("AWS_SECRET_ACCESS_KEY"):
            self.set_nested_value(["api_keys", "aws", "secret_access_key"], os.getenv("AWS_SECRET_ACCESS_KEY"))
        
        # LLM Configuration
        if os.getenv("LLM_MODEL"):
            self.set_nested_value(["llm", "model"], os.getenv("LLM_MODEL"))
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Dot-separated path to the configuration value.
            default: Default value to return if the key is not found.
            
        Returns:
            Configuration value or default.
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_nested_value(self, keys: list, default: Any = None) -> Any:
        """
        Get a nested configuration value.
        
        Args:
            keys: List of keys to traverse.
            default: Default value to return if the key is not found.
            
        Returns:
            Configuration value or default.
        """
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_nested_value(self, keys: list, value: Any) -> None:
        """
        Set a nested configuration value.
        
        Args:
            keys: List of keys to traverse.
            value: Value to set.
        """
        if not keys:
            return
        
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def save(self) -> None:
        """Save the current configuration to the YAML file."""
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config file: {e}")


# Create a singleton instance
config = Config()


def get_config() -> Config:
    """
    Get the configuration instance.
    
    Returns:
        Config instance.
    """
    return config
