"""
Configuration loader and validator for JinPress.

Handles loading and validating jinpress.yml files with sensible defaults.
Implements the ConfigManager pattern with dataclass-based configuration.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when there's an error in configuration."""

    def __init__(
        self, message: str, key: str | None = None, file_path: Path | None = None
    ):
        self.key = key
        self.file_path = file_path

        # Build descriptive error message with location info
        location_parts = []
        if file_path:
            location_parts.append(f"file: {file_path}")
        if key:
            location_parts.append(f"key: {key}")

        if location_parts:
            full_message = f"{message} ({', '.join(location_parts)})"
        else:
            full_message = message

        super().__init__(full_message)


@dataclass
class SiteConfig:
    """Site-level configuration."""

    title: str = "JinPress Site"
    description: str = ""
    lang: str = "zh-TW"
    base: str = "/"


@dataclass
class ThemeConfig:
    """Theme-level configuration."""

    nav: list[dict[str, str]] = field(default_factory=list)
    sidebar: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    footer: dict[str, str] = field(default_factory=dict)
    edit_link: dict[str, str] | None = None
    last_updated: bool = True


@dataclass
class JinPressConfig:
    """Main JinPress configuration container."""

    site: SiteConfig = field(default_factory=SiteConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {"site": asdict(self.site), "theme": asdict(self.theme)}


class ConfigManager:
    """
    Configuration manager for JinPress.

    Handles loading, validating, and merging configuration with defaults.
    Supports YAML format configuration files (jinpress.yml).
    """

    CONFIG_FILENAME = "jinpress.yml"
    LEGACY_CONFIG_FILENAME = "config.yml"

    def __init__(self):
        """Initialize ConfigManager."""
        pass

    def get_default_config(self) -> JinPressConfig:
        """
        Get the default configuration.

        Returns:
            JinPressConfig with all default values.
        """
        return JinPressConfig()

    def load(self, project_root: Path) -> JinPressConfig:
        """
        Load configuration from project root.

        Looks for jinpress.yml (or config.yml as fallback) in the project root.
        If no config file exists, returns default configuration.

        Args:
            project_root: Path to the project root directory.

        Returns:
            JinPressConfig with merged user and default values.

        Raises:
            ConfigError: If the config file contains invalid YAML or values.
        """
        project_root = Path(project_root)

        # Try jinpress.yml first, then config.yml as fallback
        config_path = project_root / self.CONFIG_FILENAME
        if not config_path.exists():
            config_path = project_root / self.LEGACY_CONFIG_FILENAME

        # If no config file exists, return defaults (Requirement 1.2)
        if not config_path.exists():
            return self.get_default_config()

        # Load and parse YAML
        try:
            with open(config_path, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            # Extract line number if available
            line_info = ""
            if hasattr(e, "problem_mark") and e.problem_mark:
                line_info = f" at line {e.problem_mark.line + 1}"
            raise ConfigError(
                f"Invalid YAML syntax{line_info}: {e}", file_path=config_path
            ) from e
        except Exception as e:
            raise ConfigError(
                f"Error reading config file: {e}", file_path=config_path
            ) from e

        # Merge with defaults and create config object
        return self._merge_config(raw_config, config_path)

    def _merge_config(
        self, raw_config: dict[str, Any], config_path: Path
    ) -> JinPressConfig:
        """
        Merge raw configuration dictionary with defaults.

        Args:
            raw_config: Raw configuration dictionary from YAML.
            config_path: Path to config file (for error messages).

        Returns:
            JinPressConfig with merged values.
        """
        default_config = self.get_default_config()

        # Merge site config
        site_dict = raw_config.get("site", {})
        if not isinstance(site_dict, dict):
            raise ConfigError(
                "site must be a dictionary", key="site", file_path=config_path
            )

        site_config = SiteConfig(
            title=site_dict.get("title", default_config.site.title),
            description=site_dict.get("description", default_config.site.description),
            lang=site_dict.get("lang", default_config.site.lang),
            base=site_dict.get("base", default_config.site.base),
        )

        # Merge theme config
        theme_dict = raw_config.get("theme", {})
        if not isinstance(theme_dict, dict):
            raise ConfigError(
                "theme must be a dictionary", key="theme", file_path=config_path
            )

        theme_config = ThemeConfig(
            nav=theme_dict.get("nav", default_config.theme.nav),
            sidebar=theme_dict.get("sidebar", default_config.theme.sidebar),
            footer=theme_dict.get("footer", default_config.theme.footer),
            edit_link=theme_dict.get("edit_link", default_config.theme.edit_link),
            last_updated=theme_dict.get(
                "last_updated", default_config.theme.last_updated
            ),
        )

        return JinPressConfig(site=site_config, theme=theme_config)

    def validate(self, config: JinPressConfig) -> list[str]:
        """
        Validate configuration and return list of errors.

        Args:
            config: JinPressConfig to validate.

        Returns:
            List of error messages. Empty list if valid.
        """
        errors = []

        # Validate site.title is required and non-empty (Requirement 1.3)
        if not config.site.title or not config.site.title.strip():
            errors.append("site.title is required and cannot be empty")

        # Validate site.title is a string
        if not isinstance(config.site.title, str):
            errors.append("site.title must be a string")

        # Validate site.description is a string
        if not isinstance(config.site.description, str):
            errors.append("site.description must be a string")

        # Validate site.lang is a string
        if not isinstance(config.site.lang, str):
            errors.append("site.lang must be a string")

        # Validate site.base is a string and starts with /
        if not isinstance(config.site.base, str):
            errors.append("site.base must be a string")
        elif not config.site.base.startswith("/"):
            errors.append("site.base must start with '/'")

        # Validate theme.nav is a list
        if not isinstance(config.theme.nav, list):
            errors.append("theme.nav must be a list")
        else:
            # Validate nav items structure
            for i, nav_item in enumerate(config.theme.nav):
                if not isinstance(nav_item, dict):
                    errors.append(f"theme.nav[{i}] must be a dictionary")
                elif "text" not in nav_item or "link" not in nav_item:
                    errors.append(f"theme.nav[{i}] must have 'text' and 'link' fields")

        # Validate theme.sidebar is a dict
        if not isinstance(config.theme.sidebar, dict):
            errors.append("theme.sidebar must be a dictionary")

        # Validate theme.footer is a dict
        if not isinstance(config.theme.footer, dict):
            errors.append("theme.footer must be a dictionary")

        # Validate theme.edit_link if present
        if config.theme.edit_link is not None:
            if not isinstance(config.theme.edit_link, dict):
                errors.append("theme.edit_link must be a dictionary")
            elif "pattern" not in config.theme.edit_link:
                errors.append("theme.edit_link must have 'pattern' field")

        # Validate theme.last_updated is a boolean
        if not isinstance(config.theme.last_updated, bool):
            errors.append("theme.last_updated must be a boolean")

        return errors

    def load_and_validate(self, project_root: Path) -> JinPressConfig:
        """
        Load and validate configuration.

        Convenience method that loads config and raises ConfigError if invalid.

        Args:
            project_root: Path to the project root directory.

        Returns:
            Validated JinPressConfig.

        Raises:
            ConfigError: If configuration is invalid.
        """
        config = self.load(project_root)
        errors = self.validate(config)

        if errors:
            raise ConfigError(
                f"Configuration validation failed: {'; '.join(errors)}",
                file_path=project_root / self.CONFIG_FILENAME,
            )

        return config


# Legacy compatibility - keep the old Config class for backward compatibility
class Config:
    """
    Legacy configuration manager for JinPress sites.

    This class is kept for backward compatibility.
    New code should use ConfigManager instead.
    """

    def __init__(self, config_path: str | Path | None = None):
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

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}") from e
        except Exception as e:
            raise ConfigError(f"Error reading config file: {e}") from e

        return config

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

    def to_dict(self) -> dict[str, Any]:
        """Get full configuration as dictionary."""
        return self._config.copy()
