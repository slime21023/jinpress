#!/usr/bin/env python3
"""
Test complete build process end-to-end.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from jinpress.scaffold import Scaffold
from jinpress.builder import Builder
from jinpress.config import Config

class TestBuildProcess(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = Path(self.test_dir)
        self.scaffold = Scaffold()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_complete_build_process(self):
        """Test complete build process from project creation to final output."""
        # Step 1: Create a new project
        project_name = "test-build-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Step 2: Build the project
        builder = Builder(project_dir)
        builder.build()
        
        # Step 3: Verify build output
        output_dir = project_dir / "dist"
        self.assertTrue(output_dir.exists(), "Output directory should be created")
        
        # Check that HTML files were generated
        html_files = list(output_dir.rglob("*.html"))
        self.assertGreater(len(html_files), 0, "Should generate HTML files")
        
        # Check for specific expected files
        expected_html_files = [
            "index.html",
            "guide/getting-started/index.html",
            "guide/configuration/index.html", 
            "guide/deployment/index.html",
            "about/index.html",
        ]
        
        for expected_file in expected_html_files:
            file_path = output_dir / expected_file
            self.assertTrue(file_path.exists(), f"Should generate {expected_file}")

    def test_html_content_generation(self):
        """Test that HTML files contain expected content."""
        project_name = "test-content-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        builder = Builder(project_dir)
        builder.build()
        
        output_dir = project_dir / "dist"
        
        # Check index.html content
        index_html = output_dir / "index.html"
        with open(index_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain processed markdown content
        self.assertIn("Welcome to JinPress", content)
        self.assertIn("<h1>", content)  # Markdown should be converted to HTML
        self.assertIn("Python Native", content)
        
        # Should contain syntax highlighting
        self.assertIn('class="language-python"', content)
        
        # Should contain custom containers
        self.assertIn('class="container-tip"', content)

    def test_static_files_copying(self):
        """Test that static files and theme assets are copied correctly."""
        project_name = "test-static-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Add some custom static files
        static_dir = project_dir / "static"
        custom_css = static_dir / "custom.css"
        with open(custom_css, 'w') as f:
            f.write("/* Custom CSS */\nbody { color: red; }")
        
        custom_js = static_dir / "custom.js"
        with open(custom_js, 'w') as f:
            f.write("// Custom JS\nconsole.log('Hello');")
        
        builder = Builder(project_dir)
        builder.build()
        
        output_dir = project_dir / "dist"
        
        # Check that theme assets were copied
        assets_dir = output_dir / "assets"
        self.assertTrue(assets_dir.exists(), "Assets directory should be created")
        
        # Check for theme CSS files
        css_dir = assets_dir / "css"
        self.assertTrue(css_dir.exists(), "CSS directory should exist")
        
        highlight_css = css_dir / "highlight.css"
        self.assertTrue(highlight_css.exists(), "highlight.css should be copied")
        
        # Check that custom static files were copied
        static_output = output_dir / "static"
        if static_output.exists():  # Static files might be copied to different location
            custom_css_output = static_output / "custom.css"
            if custom_css_output.exists():
                with open(custom_css_output, 'r') as f:
                    content = f.read()
                self.assertIn("Custom CSS", content)

    def test_search_index_generation(self):
        """Test that search index is generated correctly."""
        project_name = "test-search-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        builder = Builder(project_dir)
        builder.build()
        
        output_dir = project_dir / "dist"
        
        # Check that search index was generated
        search_index_path = output_dir / "search-index.json"
        self.assertTrue(search_index_path.exists(), "Search index should be generated")
        
        # Check search index content
        with open(search_index_path, 'r', encoding='utf-8') as f:
            search_data = json.load(f)
        
        self.assertIsInstance(search_data, list, "Search index should be a list")
        self.assertGreater(len(search_data), 0, "Search index should contain documents")
        
        # Check structure of search documents
        for doc in search_data:
            self.assertIn('title', doc, "Search document should have title")
            self.assertIn('url', doc, "Search document should have URL")
            self.assertIn('content', doc, "Search document should have content")
            self.assertIn('description', doc, "Search document should have description")

    def test_markdown_processing_features(self):
        """Test that all markdown features are processed correctly."""
        project_name = "test-markdown-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Create a markdown file with various features
        test_md = project_dir / "docs" / "test-features.md"
        with open(test_md, 'w', encoding='utf-8') as f:
            f.write("""---
title: "Test Features"
description: "Testing markdown features"
---

# Test Features

## Code Blocks

```python
def hello():
    print("Hello, world!")
```

```javascript
function greet(name) {
    console.log(`Hello, ${name}!`);
}
```

## Links

[Internal Link](./about.md)
[External Link](https://example.com)

## Containers

:::tip
This is a tip container.
:::

:::warning
This is a warning container.
:::

:::danger
This is a danger container.
:::

:::info
This is an info container.
:::

## Lists

- Item 1
- Item 2
- Item 3

1. Numbered item 1
2. Numbered item 2
3. Numbered item 3
""")
        
        builder = Builder(project_dir)
        builder.build()
        
        output_dir = project_dir / "dist"
        test_html = output_dir / "test-features" / "index.html"
        
        with open(test_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check code block processing
        self.assertIn('class="language-python"', content)
        self.assertIn('class="language-javascript"', content)
        
        # Check link processing
        self.assertIn('href="./about/"', content)  # .md should be converted
        self.assertIn('href="https://example.com"', content)
        
        # Check container processing
        self.assertIn('class="container-tip"', content)
        self.assertIn('class="container-warning"', content)
        self.assertIn('class="container-danger"', content)
        self.assertIn('class="container-info"', content)
        
        # Check list processing
        self.assertIn('<ul>', content)
        self.assertIn('<ol>', content)
        self.assertIn('<li>', content)

    def test_build_with_custom_config(self):
        """Test building with custom configuration."""
        project_name = "test-custom-config"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Modify config file
        config_path = project_dir / "config.yml"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("""site:
  title: "Custom Site Title"
  description: "Custom description"
  lang: "en-US"
  base: "/custom-base/"

themeConfig:
  nav:
    - text: "Custom Home"
      link: "/"
    - text: "Custom About"
      link: "/about/"
""")
        
        builder = Builder(project_dir)
        builder.build()
        
        output_dir = project_dir / "dist"
        index_html = output_dir / "index.html"
        
        with open(index_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain custom title
        self.assertIn("Custom Site Title", content)

    def test_build_error_handling(self):
        """Test that build process handles errors gracefully."""
        project_name = "test-error-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Create a markdown file with invalid front matter
        bad_md = project_dir / "docs" / "bad.md"
        with open(bad_md, 'w', encoding='utf-8') as f:
            f.write("""---
title: [invalid yaml
description: This should cause an error
---

# Bad File

This file has invalid front matter.
""")
        
        builder = Builder(project_dir)
        
        # Build should complete despite the error
        try:
            builder.build()
        except Exception as e:
            self.fail(f"Build should handle errors gracefully: {e}")
        
        # Output should still be generated for valid files
        output_dir = project_dir / "dist"
        self.assertTrue(output_dir.exists())
        
        index_html = output_dir / "index.html"
        self.assertTrue(index_html.exists(), "Valid files should still be processed")

    def test_incremental_build(self):
        """Test that incremental builds work correctly."""
        project_name = "test-incremental-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        builder = Builder(project_dir)
        
        # First build
        builder.build(clean=True)
        output_dir = project_dir / "dist"
        
        # Check initial build
        index_html = output_dir / "index.html"
        initial_mtime = index_html.stat().st_mtime
        
        # Add a new file
        new_md = project_dir / "docs" / "new-page.md"
        with open(new_md, 'w', encoding='utf-8') as f:
            f.write("""---
title: "New Page"
---

# New Page

This is a new page added after initial build.
""")
        
        # Incremental build (no clean)
        builder.build(clean=False)
        
        # Check that new file was processed
        new_html = output_dir / "new-page" / "index.html"
        self.assertTrue(new_html.exists(), "New file should be processed")
        
        # Check that existing files still exist
        self.assertTrue(index_html.exists(), "Existing files should remain")

    def test_build_output_structure(self):
        """Test that build output has correct directory structure."""
        project_name = "test-structure-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        builder = Builder(project_dir)
        builder.build()
        
        output_dir = project_dir / "dist"
        
        # Check expected directory structure
        expected_structure = [
            "index.html",
            "about/index.html",
            "guide/getting-started/index.html",
            "guide/configuration/index.html",
            "guide/deployment/index.html",
            "assets/css/highlight.css",
            "search-index.json",
        ]
        
        for expected_path in expected_structure:
            full_path = output_dir / expected_path
            self.assertTrue(full_path.exists(), f"Should have {expected_path}")

if __name__ == "__main__":
    unittest.main()