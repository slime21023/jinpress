"""
Unit tests for ConfigManager.

Tests configuration validation and default value loading.
Requirements: 1.6
"""

import tempfile
from pathlib import Path

import pytest

from jinpress.config import (
    ConfigError,
    ConfigManager,
    JinPressConfig,
    SiteConfig,
    ThemeConfig,
)


class TestConfigManagerValidation:
    """Tests for ConfigManager.validate() method."""

    def test_validate_valid_config(self):
        """Test that a valid config passes validation."""
        manager = ConfigManager()
        config = JinPressConfig(
            site=SiteConfig(
                title="My Site",
                description="A test site",
                lang="en",
                base="/",
            ),
            theme=ThemeConfig(
                nav=[{"text": "Home", "link": "/"}],
                sidebar={},
                footer={"message": "Built with JinPress"},
                last_updated=True,
            ),
        )
        errors = manager.validate(config)
        assert errors == []

    def test_validate_empty_title_error(self):
        """Test that empty title produces validation error."""
        manager = ConfigManager()
        config = JinPressConfig(
            site=SiteConfig(title="", description="", lang="en", base="/")
        )
        errors = manager.validate(config)
        assert any("site.title" in e for e in errors)

    def test_validate_whitespace_title_error(self):
        """Test that whitespace-only title produces validation error."""
        manager = ConfigManager()
        config = JinPressConfig(
            site=SiteConfig(title="   ", description="", lang="en", base="/")
        )
        errors = manager.validate(config)
        assert any("site.title" in e for e in errors)

    def test_validate_invalid_base_path(self):
        """Test that base path not starting with / produces error."""
        manager = ConfigManager()
        config = JinPressConfig(
            site=SiteConfig(title="Test", description="", lang="en", base="docs/")
        )
        errors = manager.validate(config)
        assert any("site.base" in e and "/" in e for e in errors)

    def test_validate_invalid_nav_item_missing_text(self):
        """Test that nav item without text produces error."""
        manager = ConfigManager()
        config = JinPressConfig(
            site=SiteConfig(title="Test"),
            theme=ThemeConfig(nav=[{"link": "/"}]),
        )
        errors = manager.validate(config)
        assert any("nav" in e and "text" in e for e in errors)

    def test_validate_invalid_nav_item_missing_link(self):
        """Test that nav item without link produces error."""
        manager = ConfigManager()
        config = JinPressConfig(
            site=SiteConfig(title="Test"),
            theme=ThemeConfig(nav=[{"text": "Home"}]),
        )
        errors = manager.validate(config)
        assert any("nav" in e and "link" in e for e in errors)

    def test_validate_invalid_edit_link_missing_pattern(self):
        """Test that edit_link without pattern produces error."""
        manager = ConfigManager()
        config = JinPressConfig(
            site=SiteConfig(title="Test"),
            theme=ThemeConfig(edit_link={"text": "Edit"}),
        )
        errors = manager.validate(config)
        assert any("edit_link" in e and "pattern" in e for e in errors)


class TestConfigManagerDefaultLoading:
    """Tests for ConfigManager default value loading."""

    def test_get_default_config_returns_jinpress_config(self):
        """Test that get_default_config returns JinPressConfig instance."""
        manager = ConfigManager()
        config = manager.get_default_config()
        assert isinstance(config, JinPressConfig)

    def test_default_site_title(self):
        """Test default site title value."""
        manager = ConfigManager()
        config = manager.get_default_config()
        assert config.site.title == "JinPress Site"

    def test_default_site_lang(self):
        """Test default site language value."""
        manager = ConfigManager()
        config = manager.get_default_config()
        assert config.site.lang == "zh-TW"

    def test_default_site_base(self):
        """Test default site base path value."""
        manager = ConfigManager()
        config = manager.get_default_config()
        assert config.site.base == "/"

    def test_default_theme_nav_is_empty_list(self):
        """Test default theme nav is empty list."""
        manager = ConfigManager()
        config = manager.get_default_config()
        assert config.theme.nav == []

    def test_default_theme_sidebar_is_empty_dict(self):
        """Test default theme sidebar is empty dict."""
        manager = ConfigManager()
        config = manager.get_default_config()
        assert config.theme.sidebar == {}

    def test_default_theme_last_updated_is_true(self):
        """Test default theme last_updated is True."""
        manager = ConfigManager()
        config = manager.get_default_config()
        assert config.theme.last_updated is True


class TestConfigManagerErrorHandling:
    """Tests for ConfigManager error handling with descriptive messages."""

    def test_invalid_yaml_syntax_error(self):
        """Test that invalid YAML produces descriptive error."""
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "jinpress.yml"
            config_path.write_text("site:\n  title: [unclosed bracket\n")

            with pytest.raises(ConfigError) as exc_info:
                manager.load(Path(tmpdir))

            error_msg = str(exc_info.value)
            assert "YAML" in error_msg or "syntax" in error_msg.lower()
            assert str(config_path) in error_msg or "jinpress.yml" in error_msg

    def test_invalid_site_type_error(self):
        """Test that non-dict site value produces descriptive error."""
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "jinpress.yml"
            config_path.write_text("site: not a dict\n")

            with pytest.raises(ConfigError) as exc_info:
                manager.load(Path(tmpdir))

            error_msg = str(exc_info.value)
            assert "site" in error_msg

    def test_invalid_theme_type_error(self):
        """Test that non-dict theme value produces descriptive error."""
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "jinpress.yml"
            config_path.write_text("theme: not a dict\n")

            with pytest.raises(ConfigError) as exc_info:
                manager.load(Path(tmpdir))

            error_msg = str(exc_info.value)
            assert "theme" in error_msg

    def test_missing_config_file_uses_defaults(self):
        """Test that missing config file returns defaults (Requirement 1.2)."""
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config = manager.load(Path(tmpdir))
            default_config = manager.get_default_config()

            assert config.site.title == default_config.site.title
            assert config.site.lang == default_config.site.lang
            assert config.site.base == default_config.site.base

    def test_load_and_validate_raises_on_invalid(self):
        """Test that load_and_validate raises ConfigError for invalid config."""
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "jinpress.yml"
            config_path.write_text("site:\n  title: ''\n")  # Empty title

            with pytest.raises(ConfigError) as exc_info:
                manager.load_and_validate(Path(tmpdir))

            error_msg = str(exc_info.value)
            assert "title" in error_msg


class TestConfigManagerYamlLoading:
    """Tests for ConfigManager YAML file loading."""

    def test_load_jinpress_yml(self):
        """Test loading jinpress.yml file."""
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "jinpress.yml"
            config_path.write_text(
                "site:\n  title: My Docs\n  description: Test docs\n"
            )

            config = manager.load(Path(tmpdir))
            assert config.site.title == "My Docs"
            assert config.site.description == "Test docs"

    def test_load_legacy_config_yml(self):
        """Test loading legacy config.yml file as fallback."""
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yml"
            config_path.write_text("site:\n  title: Legacy Config\n")

            config = manager.load(Path(tmpdir))
            assert config.site.title == "Legacy Config"

    def test_jinpress_yml_takes_priority(self):
        """Test that jinpress.yml takes priority over config.yml."""
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "jinpress.yml").write_text("site:\n  title: New Config\n")
            (Path(tmpdir) / "config.yml").write_text("site:\n  title: Old Config\n")

            config = manager.load(Path(tmpdir))
            assert config.site.title == "New Config"

    def test_load_full_config(self):
        """Test loading a complete configuration file."""
        manager = ConfigManager()
        full_config = """
site:
  title: Full Test Site
  description: A complete test
  lang: en
  base: /docs/

theme:
  nav:
    - text: Home
      link: /
    - text: Guide
      link: /guide/
  sidebar:
    /guide/:
      - text: Getting Started
        link: /guide/getting-started/
  footer:
    message: Built with JinPress
    copyright: "(c) 2025"
  last_updated: false
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "jinpress.yml"
            config_path.write_text(full_config, encoding="utf-8")

            config = manager.load(Path(tmpdir))

            assert config.site.title == "Full Test Site"
            assert config.site.description == "A complete test"
            assert config.site.lang == "en"
            assert config.site.base == "/docs/"

            assert len(config.theme.nav) == 2
            assert config.theme.nav[0]["text"] == "Home"
            assert "/guide/" in config.theme.sidebar
            assert config.theme.footer["message"] == "Built with JinPress"
            assert config.theme.last_updated is False
