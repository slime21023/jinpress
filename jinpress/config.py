"""
Configuration loader and validator for JinPress.

Handles loading and validating config.yml files with sensible defaults.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


class ConfigError(Exception):
    """Raised when there's an error in configuration."""
    pass


class Config:
    """Configuration manager for JinPress sites."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config.yml file. If None, looks for config.yml
                        in current directory.
        """
        if config_path is None:
            config_path = Path.cwd() / "config.yml"
        else:
            config_path = Path(config_path)
            
        self.config_path = config_path
        self._config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigError(f"Error reading config file: {e}")
        
        # Merge with defaults
        return self._merge_defaults(config)
    
    def _merge_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with default values."""
        defaults = {
            "site": {
                "title": "JinPress Site",
                "description": "A JinPress documentation site",
                "lang": "en-US",
                "base": "/"
            },
            "themeConfig": {
                "nav": [],
                "sidebar": {},
                "socialLinks": [],
                "editLink": {
                    "pattern": "",
                    "text": "Edit this page"
                },
                "footer": {
                    "message": "",
                    "copyright": ""
                },
                "lastUpdated": True
            }
        }
        
        return self._deep_merge(defaults, config)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries.
        
        Args:
            base: Base dictionary (defaults)
            override: Override dictionary (user config)
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Direct assignment for non-dict values or new keys
                result[key] = value
        
        return result
    
    def _validate_config(self) -> None:
        """Validate configuration structure and values."""
        # Validate site config
        site = self._config.get("site", {})
        if not isinstance(site.get("title"), str):
            raise ConfigError("site.title must be a string")
        if not isinstance(site.get("description"), str):
            raise ConfigError("site.description must be a string")
        if not isinstance(site.get("lang"), str):
            raise ConfigError("site.lang must be a string")
        if not isinstance(site.get("base"), str):
            raise ConfigError("site.base must be a string")
        
        # Validate theme config
        theme_config = self._config.get("themeConfig", {})
        if not isinstance(theme_config.get("nav"), list):
            raise ConfigError("themeConfig.nav must be a list")
        if not isinstance(theme_config.get("sidebar"), dict):
            raise ConfigError("themeConfig.sidebar must be a dictionary")
        if not isinstance(theme_config.get("socialLinks"), list):
            raise ConfigError("themeConfig.socialLinks must be a list")
        
        # Validate navigation items
        for nav_item in theme_config.get("nav", []):
            if not isinstance(nav_item, dict):
                raise ConfigError("Navigation items must be dictionaries")
            if "text" not in nav_item or "link" not in nav_item:
                raise ConfigError("Navigation items must have 'text' and 'link' fields")
    
    @property
    def site(self) -> Dict[str, Any]:
        """Get site configuration."""
        return self._config["site"]
    
    @property
    def theme_config(self) -> Dict[str, Any]:
        """Get theme configuration."""
        return self._config["themeConfig"]
    
    @property
    def title(self) -> str:
        """Get site title."""
        return self.site["title"]
    
    @property
    def description(self) -> str:
        """Get site description."""
        return self.site["description"]
    
    @property
    def lang(self) -> str:
        """Get site language."""
        return self.site["lang"]
    
    @property
    def base(self) -> str:
        """Get site base path."""
        base = self.site["base"]
        if not base.startswith("/"):
            base = "/" + base
        if not base.endswith("/"):
            base = base + "/"
        return base
    
    @property
    def nav(self) -> List[Dict[str, Any]]:
        """Get navigation configuration."""
        return self.theme_config["nav"]
    
    @property
    def sidebar(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get sidebar configuration."""
        return self.theme_config["sidebar"]
    
    @property
    def social_links(self) -> List[Dict[str, str]]:
        """Get social links configuration."""
        return self.theme_config["socialLinks"]
    
    @property
    def edit_link(self) -> Dict[str, str]:
        """Get edit link configuration."""
        return self.theme_config["editLink"]
    
    @property
    def footer(self) -> Dict[str, str]:
        """Get footer configuration."""
        return self.theme_config["footer"]
    
    @property
    def last_updated(self) -> bool:
        """Get last updated configuration."""
        return self.theme_config["lastUpdated"]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self._config.copy()
