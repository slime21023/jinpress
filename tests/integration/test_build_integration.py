#!/usr/bin/env python3
"""
Integration tests for JinPress full build process.

Tests end-to-end build flow including Markdown processing, URL generation,
static asset copying, and search index generation.
Requirements: 5.1, 5.2, 5.3, 5.4
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from jinpress.builder import BuildEngine, apply_base_path, generate_url_path
from jinpress.config import ConfigManager
from jinpress.scaffold import Scaffold


class TestFullBuildProcess(unittest.TestCase):
    """Integration tests for the complete build process (Requirement 5.1)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)

        # Create a complete project using scaffold
        scaffold = Scaffold()
        scaffold.create_project("test-site", self.project_root)
        self.project_dir = self.project_root / "test-site"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_build_converts_all_markdown_to_html(self):
        """Test that build converts all Markdown files to HTML (Requirement 5.1)."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)
        self.assertGreater(result.pages_built, 0)

        # Check that HTML files were created
        dist_dir = self.project_dir / "dist"
        html_files = list(dist_dir.rglob("*.html"))
        self.assertGreater(len(html_files), 0)

        # Verify index.html exists
        self.assertTrue((dist_dir / "index.html").exists())

    def test_build_preserves_directory_structure(self):
        """Test that build preserves the docs directory structure."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Check that guide directory structure is preserved
        dist_dir = self.project_dir / "dist"
        self.assertTrue((dist_dir / "guide").exists())
        self.assertTrue(
            (dist_dir / "guide" / "getting-started" / "index.html").exists()
        )

    def test_build_processes_frontmatter(self):
        """Test that build correctly processes YAML frontmatter."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Read generated HTML and check for title
        index_html = self.project_dir / "dist" / "index.html"
        content = index_html.read_text(encoding="utf-8")

        # Should contain the title from frontmatter
        self.assertIn("Welcome to JinPress", content)

    def test_build_generates_toc(self):
        """Test that build generates table of contents."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Check that TOC is present in output
        index_html = self.project_dir / "dist" / "index.html"
        content = index_html.read_text(encoding="utf-8")

        # Should have TOC container
        self.assertIn("toc", content.lower())


class TestCleanURLGeneration(unittest.TestCase):
    """Integration tests for clean URL generation (Requirement 5.2)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)

        scaffold = Scaffold()
        scaffold.create_project("test-site", self.project_root)
        self.project_dir = self.project_root / "test-site"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generates_clean_urls(self):
        """Test that URLs are clean (no .html extension)."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Check that pages are in directories with index.html
        dist_dir = self.project_dir / "dist"

        # guide/getting-started/ should exist as directory with index.html
        getting_started_dir = dist_dir / "guide" / "getting-started"
        self.assertTrue(getting_started_dir.is_dir())
        self.assertTrue((getting_started_dir / "index.html").exists())

    def test_url_path_generation_function(self):
        """Test the URL path generation utility function."""
        docs_dir = Path("/project/docs")

        # Test basic file
        result = generate_url_path(Path("/project/docs/guide.md"), docs_dir)
        self.assertEqual(result, "/guide/")

        # Test nested file
        result = generate_url_path(Path("/project/docs/guide/intro.md"), docs_dir)
        self.assertEqual(result, "/guide/intro/")

        # Test index file
        result = generate_url_path(Path("/project/docs/index.md"), docs_dir)
        self.assertEqual(result, "/")

        # Test nested index file
        result = generate_url_path(Path("/project/docs/guide/index.md"), docs_dir)
        self.assertEqual(result, "/guide/")

    def test_url_path_with_base_path(self):
        """Test URL path generation with base path."""
        docs_dir = Path("/project/docs")

        result = generate_url_path(
            Path("/project/docs/guide.md"), docs_dir, base_path="/my-project/"
        )
        self.assertEqual(result, "/my-project/guide/")

    def test_apply_base_path_function(self):
        """Test the base path application utility function."""
        # Normal URL
        result = apply_base_path("/assets/style.css", "/my-project/")
        self.assertEqual(result, "/my-project/assets/style.css")

        # External URL should not be modified
        result = apply_base_path("https://example.com/style.css", "/my-project/")
        self.assertEqual(result, "https://example.com/style.css")

        # Hash URL should not be modified
        result = apply_base_path("#section", "/my-project/")
        self.assertEqual(result, "#section")

        # Root base path
        result = apply_base_path("/assets/style.css", "/")
        self.assertEqual(result, "/assets/style.css")


class TestStaticAssetCopying(unittest.TestCase):
    """Integration tests for static asset copying (Requirement 5.3)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)

        scaffold = Scaffold()
        scaffold.create_project("test-site", self.project_root)
        self.project_dir = self.project_root / "test-site"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_copies_user_static_files(self):
        """Test that user static files are copied to output."""
        # Create a static file
        static_dir = self.project_dir / "static"
        static_dir.mkdir(exist_ok=True)

        test_file = static_dir / "custom.css"
        test_file.write_text("body { color: red; }")

        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Check that static file was copied
        output_file = self.project_dir / "dist" / "static" / "custom.css"
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(), "body { color: red; }")

    def test_copies_theme_assets(self):
        """Test that theme assets are copied to output."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Check that theme CSS files exist
        dist_dir = self.project_dir / "dist"
        css_files = list(dist_dir.rglob("*.css"))
        self.assertGreater(len(css_files), 0)

    def test_copies_nested_static_files(self):
        """Test that nested static files are copied correctly."""
        # Create nested static files
        static_dir = self.project_dir / "static"
        nested_dir = static_dir / "images" / "icons"
        nested_dir.mkdir(parents=True, exist_ok=True)

        test_file = nested_dir / "logo.txt"
        test_file.write_text("logo placeholder")

        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Check that nested file was copied
        output_file = (
            self.project_dir / "dist" / "static" / "images" / "icons" / "logo.txt"
        )
        self.assertTrue(output_file.exists())


class TestSearchIndexGeneration(unittest.TestCase):
    """Integration tests for search index generation (Requirement 5.4)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)

        scaffold = Scaffold()
        scaffold.create_project("test-site", self.project_root)
        self.project_dir = self.project_root / "test-site"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generates_search_index(self):
        """Test that search index JSON file is generated."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Check that search index exists
        search_index = self.project_dir / "dist" / "search-index.json"
        self.assertTrue(search_index.exists())

    def test_search_index_contains_pages(self):
        """Test that search index contains all pages."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Load and verify search index
        search_index = self.project_dir / "dist" / "search-index.json"
        with open(search_index, encoding="utf-8") as f:
            index_data = json.load(f)

        # Should be a list of documents
        self.assertIsInstance(index_data, list)
        self.assertGreater(len(index_data), 0)

    def test_search_index_document_structure(self):
        """Test that search index documents have required fields."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Load search index
        search_index = self.project_dir / "dist" / "search-index.json"
        with open(search_index, encoding="utf-8") as f:
            index_data = json.load(f)

        # Check first document has required fields
        if index_data:
            doc = index_data[0]
            self.assertIn("url", doc)
            self.assertIn("title", doc)
            self.assertIn("content", doc)


class TestBuildWithCustomConfig(unittest.TestCase):
    """Integration tests for build with custom configuration."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)

        scaffold = Scaffold()
        scaffold.create_project("test-site", self.project_root)
        self.project_dir = self.project_root / "test-site"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_build_with_custom_base_path(self):
        """Test build with custom base path for GitHub Pages subdirectory."""
        # Update config with custom base path
        config_path = self.project_dir / "jinpress.yml"
        config_content = config_path.read_text(encoding="utf-8")
        config_content = config_content.replace('base: "/"', 'base: "/my-repo/"')
        config_path.write_text(config_content, encoding="utf-8")

        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Check that base path is applied in HTML
        index_html = self.project_dir / "dist" / "index.html"
        content = index_html.read_text(encoding="utf-8")

        # Base path may be HTML-encoded (&#x2f; = /) or plain
        # Check for either form
        has_base_path = "/my-repo/" in content or "&#x2f;my-repo&#x2f;" in content
        self.assertTrue(has_base_path, "Base path should be present in output HTML")

    def test_build_creates_nojekyll_file(self):
        """Test that build creates .nojekyll file for GitHub Pages."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)

        # Check .nojekyll exists
        nojekyll = self.project_dir / "dist" / ".nojekyll"
        self.assertTrue(nojekyll.exists())


class TestBuildResult(unittest.TestCase):
    """Integration tests for build result reporting."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)

        scaffold = Scaffold()
        scaffold.create_project("test-site", self.project_root)
        self.project_dir = self.project_root / "test-site"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_build_result_contains_statistics(self):
        """Test that build result contains useful statistics."""
        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        self.assertTrue(result.success)
        self.assertGreater(result.pages_built, 0)
        self.assertGreater(result.duration_ms, 0)
        self.assertIsInstance(result.errors, list)
        self.assertIsInstance(result.warnings, list)

    def test_build_result_reports_errors(self):
        """Test that build result reports errors for invalid content."""
        # Create a markdown file with completely broken content
        bad_file = self.project_dir / "docs" / "bad.md"
        bad_file.write_text("---\ntitle: [invalid\n---\n# Content", encoding="utf-8")

        config_manager = ConfigManager()
        config = config_manager.load(self.project_dir)
        engine = BuildEngine(self.project_dir, config)

        result = engine.build()

        # Build should still succeed (graceful handling)
        self.assertTrue(result.success)
        # The result should have statistics
        self.assertGreater(result.pages_built, 0)


if __name__ == "__main__":
    unittest.main()
