"""
Property-based tests for TemplateEngine.

Feature: jinpress-rewrite
"""

import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from jinpress.templates import TemplateEngine

# Strategies for generating valid template names
template_name_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789_-"),
    min_size=1,
    max_size=20,
).map(lambda x: f"{x}.html")

# Strategy for generating simple template content
template_content_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789 \n<>{}/"),
    min_size=1,
    max_size=200,
)


@settings(max_examples=100)
@given(
    template_name=template_name_strategy,
    user_content=template_content_strategy,
    theme_content=template_content_strategy,
)
def test_template_load_priority(template_name, user_content, theme_content):
    """
    Feature: jinpress-rewrite, Property 2: 模板載入優先順序
    Validates: Requirements 3.5

    For any template name, when both user templates directory and theme
    templates directory contain that template, the template engine SHALL
    prioritize loading the user template directory version.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create theme templates directory with template
        theme_dir = tmpdir_path / "theme"
        theme_dir.mkdir()
        theme_template = theme_dir / template_name
        theme_template.write_text(theme_content, encoding="utf-8")

        # Create user templates directory with template (same name)
        user_dir = tmpdir_path / "user"
        user_dir.mkdir()
        user_template = user_dir / template_name
        user_template.write_text(user_content, encoding="utf-8")

        # Create engine with both directories
        engine = TemplateEngine(
            theme_dir=theme_dir,
            user_templates_dir=user_dir,
        )

        # Property: User template SHALL be loaded instead of theme template
        # Verify by checking which source path is returned
        source_path = engine.get_template_source(template_name)
        assert source_path is not None
        assert source_path == str(user_template)

        # Also verify the template exists
        assert engine.has_template(template_name)


@settings(max_examples=100)
@given(
    template_name=template_name_strategy,
    theme_content=template_content_strategy,
)
def test_template_fallback_to_theme(template_name, theme_content):
    """
    Feature: jinpress-rewrite, Property 2: 模板載入優先順序 (fallback case)
    Validates: Requirements 3.5

    For any template name, when only the theme templates directory contains
    that template (user directory is empty or doesn't have it), the template
    engine SHALL load from the theme directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create theme templates directory with template
        theme_dir = tmpdir_path / "theme"
        theme_dir.mkdir()
        theme_template = theme_dir / template_name
        theme_template.write_text(theme_content, encoding="utf-8")

        # Create empty user templates directory
        user_dir = tmpdir_path / "user"
        user_dir.mkdir()

        # Create engine with both directories
        engine = TemplateEngine(
            theme_dir=theme_dir,
            user_templates_dir=user_dir,
        )

        # Property: Theme template SHALL be loaded when user template doesn't exist
        source_path = engine.get_template_source(template_name)
        assert source_path is not None
        assert source_path == str(theme_template)

        # Also verify the template exists
        assert engine.has_template(template_name)


@settings(max_examples=100)
@given(
    template_name=template_name_strategy,
    user_content=template_content_strategy,
)
def test_template_user_only(template_name, user_content):
    """
    Feature: jinpress-rewrite, Property 2: 模板載入優先順序 (user only case)
    Validates: Requirements 3.5

    For any template name that exists only in user directory,
    the template engine SHALL load from the user directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create empty theme templates directory
        theme_dir = tmpdir_path / "theme"
        theme_dir.mkdir()

        # Create user templates directory with template
        user_dir = tmpdir_path / "user"
        user_dir.mkdir()
        user_template = user_dir / template_name
        user_template.write_text(user_content, encoding="utf-8")

        # Create engine with both directories
        engine = TemplateEngine(
            theme_dir=theme_dir,
            user_templates_dir=user_dir,
        )

        # Property: User template SHALL be loaded
        source_path = engine.get_template_source(template_name)
        assert source_path is not None
        assert source_path == str(user_template)

        # Also verify the template exists
        assert engine.has_template(template_name)


# Strategies for generating block names and content
block_name_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz"),
    min_size=3,
    max_size=15,
)

block_content_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789 "),
    min_size=5,
    max_size=50,
).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(
    block_name=block_name_strategy,
    parent_content=block_content_strategy,
    child_content=block_content_strategy,
)
def test_template_inheritance_block_override(block_name, parent_content, child_content):
    """
    Feature: jinpress-rewrite, Property 3: 模板繼承正確性
    Validates: Requirements 3.3

    For any child template that extends a parent template and overrides a block,
    the rendered result SHALL contain the child template's block content
    instead of the parent template's default content.
    """
    # Skip if contents are the same (can't distinguish override)
    if parent_content.strip() == child_content.strip():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create theme templates directory
        theme_dir = tmpdir_path / "theme"
        theme_dir.mkdir()

        # Create parent template (base.html) with a block
        parent_template = theme_dir / "base.html"
        parent_template.write_text(
            f"<html><body>{{% block {block_name} %}}{parent_content}{{% endblock %}}</body></html>",
            encoding="utf-8",
        )

        # Create child template that extends parent and overrides the block
        child_template = theme_dir / "child.html"
        child_template.write_text(
            f'{{% extends "base.html" %}}{{% block {block_name} %}}{child_content}{{% endblock %}}',
            encoding="utf-8",
        )

        # Create engine
        engine = TemplateEngine(theme_dir=theme_dir)

        # Render the child template
        result = engine.render("child.html", {})

        # Property: Rendered result SHALL contain child's block content
        assert child_content in result

        # Property: Rendered result SHALL NOT contain parent's default block content
        # (since it was overridden)
        assert parent_content not in result


@settings(max_examples=100)
@given(
    block_name=block_name_strategy,
    parent_content=block_content_strategy,
)
def test_template_inheritance_default_block(block_name, parent_content):
    """
    Feature: jinpress-rewrite, Property 3: 模板繼承正確性 (default case)
    Validates: Requirements 3.3

    For any child template that extends a parent template but does NOT override
    a block, the rendered result SHALL contain the parent template's default
    block content.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create theme templates directory
        theme_dir = tmpdir_path / "theme"
        theme_dir.mkdir()

        # Create parent template (base.html) with a block
        parent_template = theme_dir / "base.html"
        parent_template.write_text(
            f"<html><body>{{% block {block_name} %}}{parent_content}{{% endblock %}}</body></html>",
            encoding="utf-8",
        )

        # Create child template that extends parent but doesn't override the block
        child_template = theme_dir / "child.html"
        child_template.write_text(
            '{% extends "base.html" %}',
            encoding="utf-8",
        )

        # Create engine
        engine = TemplateEngine(theme_dir=theme_dir)

        # Render the child template
        result = engine.render("child.html", {})

        # Property: Rendered result SHALL contain parent's default block content
        assert parent_content in result


@settings(max_examples=100)
@given(
    block_name=block_name_strategy,
    parent_content=block_content_strategy,
    child_content=block_content_strategy,
)
def test_template_inheritance_user_override(block_name, parent_content, child_content):
    """
    Feature: jinpress-rewrite, Property 3: 模板繼承正確性 (user override)
    Validates: Requirements 3.3, 3.5

    For any user template that overrides a theme template and changes block content,
    the rendered result SHALL contain the user template's block content.
    This tests the combination of template priority and inheritance.
    """
    # Skip if contents are the same (can't distinguish override)
    if parent_content.strip() == child_content.strip():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create theme templates directory
        theme_dir = tmpdir_path / "theme"
        theme_dir.mkdir()

        # Create parent template (base.html) in theme
        parent_template = theme_dir / "base.html"
        parent_template.write_text(
            f"<html><body>{{% block {block_name} %}}{parent_content}{{% endblock %}}</body></html>",
            encoding="utf-8",
        )

        # Create child template in theme
        theme_child = theme_dir / "page.html"
        theme_child.write_text(
            f'{{% extends "base.html" %}}{{% block {block_name} %}}{parent_content}{{% endblock %}}',
            encoding="utf-8",
        )

        # Create user templates directory
        user_dir = tmpdir_path / "user"
        user_dir.mkdir()

        # Create user override of child template with different content
        user_child = user_dir / "page.html"
        user_child.write_text(
            f'{{% extends "base.html" %}}{{% block {block_name} %}}{child_content}{{% endblock %}}',
            encoding="utf-8",
        )

        # Create engine with user templates taking priority
        engine = TemplateEngine(
            theme_dir=theme_dir,
            user_templates_dir=user_dir,
        )

        # Render the page template (should use user's version)
        result = engine.render("page.html", {})

        # Property: Rendered result SHALL contain user's block content
        assert child_content in result
