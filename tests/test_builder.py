
#!/usr/bin/env python3
"""
Test Builder functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from jinpress.builder import Builder, BuildError
from jinpress.config import Config, ConfigError

class TestBuilder(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        
        # Create basic project structure
        self.docs_dir = self.project_root / "docs"
        self.docs_dir.mkdir()
        self.output_dir = self.project_root / "dist"
        
        # Create config file
        self.config_path = self.project_root / "config.yml"
        with open(self.config_path, "w") as f:
            f.write("""title: Test Site
description: A test site
lang: en
base: /
docs_dir: docs
output_dir: dist
""")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_builder_creation(self):
        """Test that Builder can be created successfully."""
        builder = Builder(project_root=self.project_root)
        self.assertIsInstance(builder, Builder)
        self.assertEqual(builder.project_root, self.project_root)

    def test_builder_with_config_object(self):
        """Test Builder creation with explicit config object."""
        config = Config(self.config_path)
        builder = Builder(project_root=self.project_root, config=config)
        self.assertIsInstance(builder, Builder)
        self.assertIsInstance(builder.config, Config)

    def test_builder_missing_config(self):
        """Test Builder handles missing config file."""
        # Remove config file
        self.config_path.unlink()
        
        with self.assertRaises(ConfigError):
            Builder(project_root=self.project_root)

    def test_builder_get_build_info(self):
        """Test that Builder can provide build information."""
        builder = Builder(project_root=self.project_root)
        build_info = builder.get_build_info()
        
        self.assertIsInstance(build_info, dict)
        self.assertIn('project_root', build_info)
        self.assertIn('config_file', build_info)
        self.assertIn('docs_dir', build_info)
        self.assertIn('output_dir', build_info)
        self.assertIn('site_title', build_info)

    def test_builder_build_empty_site(self):
        """Test building a site with no content."""
        builder = Builder(project_root=self.project_root)
        
        # Should not raise an exception
        try:
            builder.build()
        except Exception as e:
            self.fail(f"Building empty site should not fail: {e}")
        
        # Output directory should be created
        self.assertTrue(self.output_dir.exists())

    def test_builder_build_with_content(self):
        """Test building a site with markdown content."""
        # Create some markdown files
        index_file = self.docs_dir / "index.md"
        with open(index_file, "w") as f:
            f.write("""---
title: Home Page
---

# Welcome

This is the home page.
""")
        
        about_file = self.docs_dir / "about.md"
        with open(about_file, "w") as f:
            f.write("""---
title: About
---

# About Us

This is the about page.
""")
        
        builder = Builder(project_root=self.project_root)
        builder.build()
        
        # Check that HTML files were created
        self.assertTrue(self.output_dir.exists())
        
        # Check for index.html
        index_html = self.output_dir / "index.html"
        if index_html.exists():
            with open(index_html, 'r') as f:
                content = f.read()
            self.assertIn("Welcome", content)

    def test_builder_build_clean(self):
        """Test building with clean option."""
        builder = Builder(project_root=self.project_root)
        
        # Create output directory with some files
        self.output_dir.mkdir(exist_ok=True)
        old_file = self.output_dir / "old.html"
        with open(old_file, "w") as f:
            f.write("old content")
        
        # Build with clean=True
        builder.build(clean=True)
        
        # Old file should be removed
        self.assertFalse(old_file.exists())

    def test_builder_build_no_clean(self):
        """Test building without clean option."""
        builder = Builder(project_root=self.project_root)
        
        # Create output directory with some files
        self.output_dir.mkdir(exist_ok=True)
        old_file = self.output_dir / "old.html"
        with open(old_file, "w") as f:
            f.write("old content")
        
        # Build with clean=False
        builder.build(clean=False)
        
        # Old file should still exist
        self.assertTrue(old_file.exists())

    def test_builder_handles_invalid_markdown(self):
        """Test that Builder handles invalid markdown gracefully."""
        # Create markdown file with invalid front matter
        bad_file = self.docs_dir / "bad.md"
        with open(bad_file, "w") as f:
            f.write("""---
title: [invalid yaml
---

# Content
""")
        
        builder = Builder(project_root=self.project_root)
        
        # Should handle the error gracefully
        try:
            builder.build()
        except Exception as e:
            # Should be a specific build error, not a generic exception
            self.assertIsInstance(e, (BuildError, Exception))

if __name__ == '__main__':
    unittest.main()
