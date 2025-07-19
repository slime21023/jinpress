#!/usr/bin/env python3
"""
Test project scaffolding functionality.
"""

import unittest
import tempfile
import shutil
import yaml
from pathlib import Path
from jinpress.scaffold import Scaffold, ScaffoldError
from jinpress.config import Config

class TestScaffold(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = Path(self.test_dir)
        self.scaffold = Scaffold()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scaffold_initialization(self):
        """Test that Scaffold initializes correctly."""
        scaffold = Scaffold()
        self.assertIsInstance(scaffold, Scaffold)

    def test_create_project_basic(self):
        """Test creating a basic project."""
        project_name = "test-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Check that project directory was created
        expected_dir = self.target_dir / project_name
        self.assertEqual(project_dir, expected_dir)
        self.assertTrue(project_dir.exists())
        self.assertTrue(project_dir.is_dir())

    def test_create_project_directory_structure(self):
        """Test that proper directory structure is created."""
        project_name = "test-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Check required directories
        expected_dirs = [
            "docs",
            "docs/guide",
            "static",
            ".jinpress",
            ".jinpress/cache",
        ]
        
        for dir_name in expected_dirs:
            dir_path = project_dir / dir_name
            self.assertTrue(dir_path.exists(), f"Directory {dir_name} should exist")
            self.assertTrue(dir_path.is_dir(), f"{dir_name} should be a directory")

    def test_create_project_config_file(self):
        """Test that configuration file is created correctly."""
        project_name = "my-awesome-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Check config file exists
        config_path = project_dir / "config.yml"
        self.assertTrue(config_path.exists(), "config.yml should exist")
        self.assertTrue(config_path.is_file(), "config.yml should be a file")
        
        # Check config content
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # Parse YAML to ensure it's valid
        try:
            config_data = yaml.safe_load(config_content)
        except yaml.YAMLError as e:
            self.fail(f"Config file should contain valid YAML: {e}")
        
        # Check basic structure
        self.assertIn('site', config_data)
        self.assertIn('themeConfig', config_data)
        
        # Check site configuration
        site_config = config_data['site']
        self.assertEqual(site_config['title'], "My Awesome Project")
        self.assertEqual(site_config['lang'], "en-US")
        self.assertEqual(site_config['base'], "/")
        
        # Check theme configuration
        theme_config = config_data['themeConfig']
        self.assertIn('nav', theme_config)
        self.assertIn('sidebar', theme_config)
        self.assertIn('footer', theme_config)

    def test_create_project_sample_content(self):
        """Test that sample content is created correctly."""
        project_name = "test-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Check required markdown files
        expected_files = [
            "docs/index.md",
            "docs/guide/getting-started.md",
            "docs/guide/configuration.md",
            "docs/guide/deployment.md",
            "docs/about.md",
        ]
        
        for file_path in expected_files:
            full_path = project_dir / file_path
            self.assertTrue(full_path.exists(), f"File {file_path} should exist")
            self.assertTrue(full_path.is_file(), f"{file_path} should be a file")
            
            # Check that files have content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertGreater(len(content), 100, f"{file_path} should have substantial content")

    def test_create_project_index_content(self):
        """Test that index.md has proper content and front matter."""
        project_name = "test-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        index_path = project_dir / "docs" / "index.md"
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for front matter
        self.assertTrue(content.startswith("---\n"), "Index should have front matter")
        
        # Check for key content
        self.assertIn("Welcome to JinPress", content)
        self.assertIn("Python Native", content)
        self.assertIn("```python", content)  # Code block
        self.assertIn(":::tip", content)     # Container

    def test_create_project_gitignore(self):
        """Test that .gitignore file is created correctly."""
        project_name = "test-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        gitignore_path = project_dir / ".gitignore"
        self.assertTrue(gitignore_path.exists(), ".gitignore should exist")
        
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for important ignore patterns
        expected_patterns = [
            "dist/",
            ".jinpress/cache/",
            "__pycache__/",
            "*.py[cod]",
            "venv/",
            ".DS_Store",
        ]
        
        for pattern in expected_patterns:
            self.assertIn(pattern, content, f"Gitignore should contain {pattern}")

    def test_create_project_existing_directory(self):
        """Test that creating project in existing directory raises error."""
        project_name = "test-project"
        
        # Create the directory first
        existing_dir = self.target_dir / project_name
        existing_dir.mkdir()
        
        # Should raise ScaffoldError
        with self.assertRaises(ScaffoldError) as context:
            self.scaffold.create_project(project_name, self.target_dir)
        
        self.assertIn("Directory already exists", str(context.exception))

    def test_create_project_default_target_dir(self):
        """Test creating project with default target directory."""
        project_name = "test-project"
        
        # Change to test directory
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(self.target_dir)
            
            project_dir = self.scaffold.create_project(project_name)
            
            # Should create in current directory
            expected_dir = self.target_dir / project_name
            self.assertEqual(project_dir, expected_dir)
            self.assertTrue(project_dir.exists())
            
        finally:
            os.chdir(original_cwd)

    def test_create_project_name_formatting(self):
        """Test that project names are formatted correctly in config."""
        test_cases = [
            ("my-project", "My Project"),
            ("my_project", "My Project"),
            ("my-awesome_project", "My Awesome Project"),
            ("simple", "Simple"),
        ]
        
        for project_name, expected_title in test_cases:
            with self.subTest(project_name=project_name):
                project_dir = self.scaffold.create_project(project_name, self.target_dir)
                
                config_path = project_dir / "config.yml"
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                self.assertEqual(config_data['site']['title'], expected_title)
                
                # Clean up for next iteration
                shutil.rmtree(project_dir)

    def test_config_file_is_valid(self):
        """Test that generated config file can be loaded by Config class."""
        project_name = "test-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        config_path = project_dir / "config.yml"
        
        # Should be able to load with Config class
        try:
            config = Config(config_path)
            
            # Check that basic properties are accessible
            self.assertEqual(config.get('site', {}).get('title'), "Test Project")
            self.assertEqual(config.get('site', {}).get('lang'), "en-US")
            self.assertIsInstance(config.get('themeConfig'), dict)
            
        except Exception as e:
            self.fail(f"Generated config should be loadable by Config class: {e}")

    def test_sample_content_has_valid_front_matter(self):
        """Test that all sample content files have valid front matter."""
        project_name = "test-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Check all markdown files
        markdown_files = list((project_dir / "docs").rglob("*.md"))
        self.assertGreater(len(markdown_files), 0, "Should have markdown files")
        
        for md_file in markdown_files:
            with self.subTest(file=md_file.name):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if content.startswith("---\n"):
                    # Extract front matter
                    try:
                        end_match = content.find("\n---\n", 4)
                        if end_match != -1:
                            front_matter_text = content[4:end_match]
                            yaml.safe_load(front_matter_text)
                    except yaml.YAMLError as e:
                        self.fail(f"Invalid front matter in {md_file.name}: {e}")

    def test_project_structure_completeness(self):
        """Test that created project has all necessary components for building."""
        project_name = "test-project"
        project_dir = self.scaffold.create_project(project_name, self.target_dir)
        
        # Check that we can create a Builder with this project
        try:
            from jinpress.builder import Builder
            builder = Builder(project_dir)
            
            # Should be able to get build info
            build_info = builder.get_build_info()
            self.assertIsInstance(build_info, dict)
            
        except Exception as e:
            self.fail(f"Created project should be buildable: {e}")

if __name__ == "__main__":
    unittest.main()