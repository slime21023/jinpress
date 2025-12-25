"""
Property-based tests for ConfigManager.

Feature: jinpress-rewrite
"""

import tempfile
from pathlib import Path

import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from jinpress.config import ConfigManager

# Strategies for generating valid configuration values
site_title_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
site_description_strategy = st.text(max_size=500)
site_lang_strategy = st.sampled_from(["en", "zh-TW", "ja", "ko", "fr", "de", "es"])
site_base_strategy = st.sampled_from(["/", "/docs/", "/my-project/", "/v1/"])

nav_item_strategy = st.fixed_dictionaries(
    {
        "text": st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        "link": st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    }
)

footer_strategy = st.fixed_dictionaries(
    {
        "message": st.text(max_size=200),
        "copyright": st.text(max_size=100),
    }
)


@st.composite
def partial_site_config_strategy(draw):
    """Generate partial site configuration dictionaries."""
    config = {}
    if draw(st.booleans()):
        config["title"] = draw(site_title_strategy)
    if draw(st.booleans()):
        config["description"] = draw(site_description_strategy)
    if draw(st.booleans()):
        config["lang"] = draw(site_lang_strategy)
    if draw(st.booleans()):
        config["base"] = draw(site_base_strategy)
    return config


@st.composite
def partial_theme_config_strategy(draw):
    """Generate partial theme configuration dictionaries."""
    config = {}
    if draw(st.booleans()):
        config["nav"] = draw(st.lists(nav_item_strategy, max_size=5))
    if draw(st.booleans()):
        config["sidebar"] = draw(st.fixed_dictionaries({}))
    if draw(st.booleans()):
        config["footer"] = draw(footer_strategy)
    if draw(st.booleans()):
        config["last_updated"] = draw(st.booleans())
    return config


@st.composite
def partial_config_strategy(draw):
    """Generate partial configuration dictionaries."""
    config = {}
    if draw(st.booleans()):
        config["site"] = draw(partial_site_config_strategy())
    if draw(st.booleans()):
        config["theme"] = draw(partial_theme_config_strategy())
    return config


@settings(max_examples=100)
@given(partial_config=partial_config_strategy())
def test_config_merge_completeness(partial_config):
    """
    Feature: jinpress-rewrite, Property 1: 配置合併完整性
    Validates: Requirements 1.4, 1.5

    For any partial configuration dictionary, after merging with defaults,
    the result SHALL contain all default fields, and user-provided values
    SHALL override default values.
    """
    manager = ConfigManager()
    default_config = manager.get_default_config()

    # Create a temporary directory with the partial config
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "jinpress.yml"

        # Write partial config to file
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(partial_config, f)

        # Load the merged config
        merged_config = manager.load(Path(tmpdir))

        # Property 1: Result SHALL contain all default fields
        # Check site config fields exist
        assert hasattr(merged_config.site, "title")
        assert hasattr(merged_config.site, "description")
        assert hasattr(merged_config.site, "lang")
        assert hasattr(merged_config.site, "base")

        # Check theme config fields exist
        assert hasattr(merged_config.theme, "nav")
        assert hasattr(merged_config.theme, "sidebar")
        assert hasattr(merged_config.theme, "footer")
        assert hasattr(merged_config.theme, "edit_link")
        assert hasattr(merged_config.theme, "last_updated")

        # Property 2: User-provided values SHALL override defaults
        if "site" in partial_config:
            site_partial = partial_config["site"]
            if "title" in site_partial:
                assert merged_config.site.title == site_partial["title"]
            if "description" in site_partial:
                assert merged_config.site.description == site_partial["description"]
            if "lang" in site_partial:
                assert merged_config.site.lang == site_partial["lang"]
            if "base" in site_partial:
                assert merged_config.site.base == site_partial["base"]

        if "theme" in partial_config:
            theme_partial = partial_config["theme"]
            if "nav" in theme_partial:
                assert merged_config.theme.nav == theme_partial["nav"]
            if "sidebar" in theme_partial:
                assert merged_config.theme.sidebar == theme_partial["sidebar"]
            if "footer" in theme_partial:
                assert merged_config.theme.footer == theme_partial["footer"]
            if "last_updated" in theme_partial:
                assert merged_config.theme.last_updated == theme_partial["last_updated"]

        # Property 3: Missing fields SHALL use default values
        if "site" not in partial_config or "title" not in partial_config.get(
            "site", {}
        ):
            assert merged_config.site.title == default_config.site.title
        if "site" not in partial_config or "description" not in partial_config.get(
            "site", {}
        ):
            assert merged_config.site.description == default_config.site.description
        if "site" not in partial_config or "lang" not in partial_config.get("site", {}):
            assert merged_config.site.lang == default_config.site.lang
        if "site" not in partial_config or "base" not in partial_config.get("site", {}):
            assert merged_config.site.base == default_config.site.base

        if "theme" not in partial_config or "nav" not in partial_config.get(
            "theme", {}
        ):
            assert merged_config.theme.nav == default_config.theme.nav
        if "theme" not in partial_config or "sidebar" not in partial_config.get(
            "theme", {}
        ):
            assert merged_config.theme.sidebar == default_config.theme.sidebar
        if "theme" not in partial_config or "footer" not in partial_config.get(
            "theme", {}
        ):
            assert merged_config.theme.footer == default_config.theme.footer
        if "theme" not in partial_config or "last_updated" not in partial_config.get(
            "theme", {}
        ):
            assert merged_config.theme.last_updated == default_config.theme.last_updated
