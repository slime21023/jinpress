
#!/usr/bin/env python3
"""
Test Config functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from jinpress.config import Config, ConfigError

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = Path(self.test_dir) / "config.yml"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_config_creation(self):
        """Test basic config creation and value retrieval."""
        with open(self.config_path, "w") as f:
            f.write("title: Test Site")
        config = Config(self.config_path)
        self.assertEqual(config.get('title'), "Test Site")

    def test_config_not_found(self):
        """Test that missing config file raises ConfigError."""
        with self.assertRaises(ConfigError):
            Config(self.config_path)

    def test_config_full_structure(self):
        """Test config with full site structure."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("""title: My Site
description: A comprehensive test site
lang: en
base: /
docs_dir: docs
output_dir: dist
theme:
  nav:
    - text: Home
      link: /
    - text: About
      link: /about/
  sidebar: true
  editLink:
    pattern: https://github.com/user/repo/edit/main/docs/:path
    text: Edit this page
  footer:
    message: Built with JinPress
    copyright: (c) 2024 My Site
""")
        
        config = Config(self.config_path)
        
        # Test basic properties
        self.assertEqual(config.get('title'), "My Site")
        self.assertEqual(config.get('description'), "A comprehensive test site")
        self.assertEqual(config.get('lang'), "en")
        self.assertEqual(config.get('base'), "/")
        self.assertEqual(config.get('docs_dir'), "docs")
        self.assertEqual(config.get('output_dir'), "dist")
        
        # Test theme configuration
        theme = config.get('theme')
        self.assertIsInstance(theme, dict)
        self.assertIn('nav', theme)
        self.assertIn('sidebar', theme)
        self.assertIn('editLink', theme)
        self.assertIn('footer', theme)
        
        # Test navigation structure
        nav = theme['nav']
        self.assertEqual(len(nav), 2)
        self.assertEqual(nav[0]['text'], "Home")
        self.assertEqual(nav[0]['link'], "/")

    def test_config_default_values(self):
        """Test that config provides sensible defaults."""
        with open(self.config_path, "w") as f:
            f.write("title: Minimal Site")
        
        config = Config(self.config_path)
        
        # Should have title
        self.assertEqual(config.get('title'), "Minimal Site")
        
        # Should provide defaults for missing values
        self.assertIsNotNone(config.get('lang', 'en'))
        self.assertIsNotNone(config.get('base', '/'))

    def test_config_invalid_yaml(self):
        """Test that invalid YAML raises ConfigError."""
        with open(self.config_path, "w") as f:
            f.write("""title: Test Site
invalid: [unclosed bracket
description: This should fail
""")
        
        with self.assertRaises(ConfigError):
            Config(self.config_path)

    def test_config_empty_file(self):
        """Test handling of empty config file."""
        with open(self.config_path, "w") as f:
            f.write("")
        
        config = Config(self.config_path)
        
        # Should handle empty config gracefully
        self.assertIsNone(config.get('title'))
        self.assertEqual(config.get('title', 'Default'), 'Default')

    def test_config_nested_values(self):
        """Test accessing nested configuration values."""
        with open(self.config_path, "w") as f:
            f.write("""title: Test Site
theme:
  colors:
    primary: blue
    secondary: green
  layout:
    sidebar: true
    width: 1200
""")
        
        config = Config(self.config_path)
        
        # Test nested access
        theme = config.get('theme')
        self.assertIsInstance(theme, dict)
        
        colors = theme.get('colors')
        self.assertEqual(colors['primary'], 'blue')
        self.assertEqual(colors['secondary'], 'green')
        
        layout = theme.get('layout')
        self.assertTrue(layout['sidebar'])
        self.assertEqual(layout['width'], 1200)

    def test_config_boolean_values(self):
        """Test handling of boolean values in config."""
        with open(self.config_path, "w") as f:
            f.write("""title: Test Site
debug: true
production: false
theme:
  sidebar: true
  search: false
""")
        
        config = Config(self.config_path)
        
        self.assertTrue(config.get('debug'))
        self.assertFalse(config.get('production'))
        
        theme = config.get('theme')
        self.assertTrue(theme['sidebar'])
        self.assertFalse(theme['search'])

    def test_config_list_values(self):
        """Test handling of list values in config."""
        with open(self.config_path, "w") as f:
            f.write("""title: Test Site
tags:
  - documentation
  - static-site
  - python
theme:
  nav:
    - text: Home
      link: /
    - text: Docs
      link: /docs/
""")
        
        config = Config(self.config_path)
        
        tags = config.get('tags')
        self.assertIsInstance(tags, list)
        self.assertEqual(len(tags), 3)
        self.assertIn('documentation', tags)
        
        nav = config.get('theme')['nav']
        self.assertIsInstance(nav, list)
        self.assertEqual(len(nav), 2)

if __name__ == '__main__':
    unittest.main()
