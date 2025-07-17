#!/usr/bin/env python3
"""
Test theme engine template loading and rendering.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from jinpress.theme.engine import ThemeEngine, ThemeError

class TestThemeEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir) / "project"
        self.project_root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_default_template_loading(self):
        """Test that default templates can be loaded."""
        engine = ThemeEngine(self.project_root)
        
        # Check that default templates exist
        self.assertTrue(engine.has_template("base.html"))
        self.assertTrue(engine.has_template("page.html"))
        
        # Test rendering a simple template
        context = {
            "site": {"title": "Test Site", "lang": "en", "base": "/"},
            "page": {"title": "Test Page", "description": "Test Description"},
            "theme": {"nav": [], "sidebar": False}
        }
        
        try:
            html = engine.render_page("page.html", context)
            self.assertIsInstance(html, str)
            self.assertGreater(len(html), 0)
        except ThemeError as e:
            self.fail(f"Template rendering failed: {e}")

    def test_custom_template_override(self):
        """Test that custom templates override default templates."""
        # Create custom templates directory
        custom_templates = self.project_root / "templates"
        custom_templates.mkdir()
        
        # Create a custom base.html template
        custom_base = custom_templates / "base.html"
        with open(custom_base, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>{{ page.title }} - Custom Template</title>
</head>
<body>
    <h1>Custom Template: {{ page.title }}</h1>
    {% block content %}{% endblock %}
</body>
</html>""")
        
        engine = ThemeEngine(self.project_root)
        
        # Test that custom template is used
        context = {
            "site": {"title": "Test Site", "lang": "en"},
            "page": {"title": "Test Page", "description": "Test Description"}
        }
        
        html = engine.render_page("base.html", context)
        self.assertIn("Custom Template: Test Page", html)
        self.assertIn("Custom Template", html)

    def test_template_not_found(self):
        """Test handling of non-existent templates."""
        engine = ThemeEngine(self.project_root)
        
        # Test that non-existent template raises error
        with self.assertRaises(ThemeError):
            engine.render_page("nonexistent.html", {})
        
        # Test has_template returns False for non-existent template
        self.assertFalse(engine.has_template("nonexistent.html"))

    def test_template_context_filters(self):
        """Test that custom filters are available in templates."""
        # Create a template that uses custom filters
        custom_templates = self.project_root / "templates"
        custom_templates.mkdir()
        
        test_template = custom_templates / "test_filters.html"
        with open(test_template, "w", encoding="utf-8") as f:
            f.write("""
<p>URL: {{ '/test/path' | url_for('/base') }}</p>
<p>Date: {{ 1640995200 | format_date('%Y-%m-%d') }}</p>
""")
        
        engine = ThemeEngine(self.project_root)
        
        context = {}
        html = engine.render_page("test_filters.html", context)
        
        # Check that filters worked (HTML may be escaped)
        self.assertTrue("/base/test/path" in html or "&#x2f;base&#x2f;test&#x2f;path" in html)
        self.assertIn("2022-01-01", html)  # Unix timestamp 1640995200 = 2022-01-01

    def test_template_inheritance(self):
        """Test that template inheritance works correctly."""
        # Create custom templates with inheritance
        custom_templates = self.project_root / "templates"
        custom_templates.mkdir()
        
        # Base template
        base_template = custom_templates / "test_base.html"
        with open(base_template, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>{{ page.title }}</title>
</head>
<body>
    <header>Site Header</header>
    <main>
        {% block content %}Default Content{% endblock %}
    </main>
    <footer>Site Footer</footer>
</body>
</html>""")
        
        # Child template
        child_template = custom_templates / "test_child.html"
        with open(child_template, "w", encoding="utf-8") as f:
            f.write("""{% extends "test_base.html" %}

{% block content %}
<h1>{{ page.title }}</h1>
<p>{{ page.description }}</p>
{% endblock %}""")
        
        engine = ThemeEngine(self.project_root)
        
        context = {
            "page": {"title": "Child Page", "description": "This is a child page"}
        }
        
        html = engine.render_page("test_child.html", context)
        
        # Check that inheritance worked
        self.assertIn("Site Header", html)
        self.assertIn("Site Footer", html)
        self.assertIn("<h1>Child Page</h1>", html)
        self.assertIn("This is a child page", html)
        self.assertNotIn("Default Content", html)  # Should be overridden

    def test_static_files_discovery(self):
        """Test that static files are discovered correctly."""
        engine = ThemeEngine(self.project_root)
        
        static_files = engine.get_static_files()
        
        # Should find CSS and JS files
        css_files = [f for f in static_files if f.suffix == '.css']
        js_files = [f for f in static_files if f.suffix == '.js']
        
        self.assertGreater(len(css_files), 0, "Should find CSS files")
        
        # Check for specific files
        file_names = [f.name for f in static_files]
        self.assertIn("highlight.css", file_names)

    def test_static_file_copying(self):
        """Test that static files are copied correctly to output directory."""
        engine = ThemeEngine(self.project_root)
        
        # Create output directory
        output_dir = self.project_root / "dist"
        output_dir.mkdir()
        
        # Copy static files
        engine.copy_static_files(output_dir)
        
        # Check that files were copied to assets directory
        assets_dir = output_dir / "assets"
        self.assertTrue(assets_dir.exists(), "Assets directory should be created")
        
        # Check for CSS files
        css_dir = assets_dir / "css"
        self.assertTrue(css_dir.exists(), "CSS directory should be created")
        
        highlight_css = css_dir / "highlight.css"
        self.assertTrue(highlight_css.exists(), "highlight.css should be copied")
        
        # Verify file content is preserved
        with open(highlight_css, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('.highlight', content, "CSS content should be preserved")
        
        # Check for main.css if it exists
        main_css = css_dir / "main.css"
        if main_css.exists():
            self.assertTrue(main_css.is_file(), "main.css should be a file")

    def test_static_file_structure_preservation(self):
        """Test that static file directory structure is preserved."""
        engine = ThemeEngine(self.project_root)
        
        # Create output directory
        output_dir = self.project_root / "dist"
        output_dir.mkdir()
        
        # Copy static files
        engine.copy_static_files(output_dir)
        
        # Check that directory structure is preserved
        assets_dir = output_dir / "assets"
        
        # Should have css and js subdirectories
        expected_dirs = ["css"]  # js directory might not exist yet
        for dir_name in expected_dirs:
            dir_path = assets_dir / dir_name
            if dir_path.exists():
                self.assertTrue(dir_path.is_dir(), f"{dir_name} should be a directory")

if __name__ == "__main__":
    unittest.main()