#!/usr/bin/env python3
"""
Integration tests for JinPress CLI commands.

Tests the init, serve, and build commands end-to-end.
Requirements: 9.1, 9.2, 9.3
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from jinpress.cli import cli


class TestCLIInit(unittest.TestCase):
    """Integration tests for the 'init' command (Requirement 9.1)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_creates_project(self):
        """Test that init command creates a new project with correct structure."""
        result = self.runner.invoke(cli, ["init", "my-docs"])

        self.assertEqual(result.exit_code, 0, f"Init failed: {result.output}")
        self.assertIn("Created JinPress project", result.output)

        # Verify project structure
        project_dir = Path(self.test_dir) / "my-docs"
        self.assertTrue(project_dir.exists())
        self.assertTrue((project_dir / "docs").exists())
        self.assertTrue((project_dir / "jinpress.yml").exists())
        self.assertTrue((project_dir / "docs" / "index.md").exists())

    def test_init_creates_github_actions_workflow(self):
        """Test that init creates GitHub Actions workflow template."""
        result = self.runner.invoke(cli, ["init", "my-docs"])

        self.assertEqual(result.exit_code, 0)

        workflow_path = (
            Path(self.test_dir) / "my-docs" / ".github" / "workflows" / "deploy.yml"
        )
        self.assertTrue(workflow_path.exists())

        content = workflow_path.read_text()
        self.assertIn("Deploy JinPress Site", content)
        self.assertIn("jinpress build", content)

    def test_init_with_custom_directory(self):
        """Test init with custom target directory."""
        custom_dir = Path(self.test_dir) / "custom"
        custom_dir.mkdir()

        result = self.runner.invoke(cli, ["init", "my-docs", "--dir", str(custom_dir)])

        self.assertEqual(result.exit_code, 0)
        self.assertTrue((custom_dir / "my-docs").exists())

    def test_init_existing_directory_fails(self):
        """Test that init fails when directory already exists."""
        # Create the directory first
        (Path(self.test_dir) / "existing-project").mkdir()

        result = self.runner.invoke(cli, ["init", "existing-project"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error", result.output)

    def test_init_prompts_for_name(self):
        """Test that init prompts for project name if not provided."""
        result = self.runner.invoke(cli, ["init"], input="prompted-project\n")

        self.assertEqual(result.exit_code, 0)
        self.assertTrue((Path(self.test_dir) / "prompted-project").exists())


class TestCLIBuild(unittest.TestCase):
    """Integration tests for the 'build' command (Requirement 9.3)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
        self.original_cwd = os.getcwd()

        # Create a project first
        os.chdir(self.test_dir)
        self.runner.invoke(cli, ["init", "test-project"])
        self.project_dir = Path(self.test_dir) / "test-project"
        os.chdir(self.project_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_build_creates_output(self):
        """Test that build command creates output directory with HTML files."""
        result = self.runner.invoke(cli, ["build"])

        self.assertEqual(result.exit_code, 0, f"Build failed: {result.output}")
        self.assertIn("Site built successfully", result.output)

        # Verify output
        dist_dir = self.project_dir / "dist"
        self.assertTrue(dist_dir.exists())
        self.assertTrue((dist_dir / "index.html").exists())

    def test_build_creates_search_index(self):
        """Test that build creates search index file."""
        result = self.runner.invoke(cli, ["build"])

        self.assertEqual(result.exit_code, 0)

        search_index = self.project_dir / "dist" / "search-index.json"
        self.assertTrue(search_index.exists())

    def test_build_creates_nojekyll(self):
        """Test that build creates .nojekyll file for GitHub Pages."""
        result = self.runner.invoke(cli, ["build"])

        self.assertEqual(result.exit_code, 0)

        nojekyll = self.project_dir / "dist" / ".nojekyll"
        self.assertTrue(nojekyll.exists())

    def test_build_clean_option(self):
        """Test that build --no-clean preserves existing files."""
        # First build
        self.runner.invoke(cli, ["build"])

        # Add a custom file to dist
        custom_file = self.project_dir / "dist" / "custom.txt"
        custom_file.write_text("custom content")

        # Build with --no-clean
        result = self.runner.invoke(cli, ["build", "--no-clean"])

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(custom_file.exists())

    def test_build_clean_removes_old_files(self):
        """Test that build with clean removes old files."""
        # First build
        self.runner.invoke(cli, ["build"])

        # Add a custom file to dist
        custom_file = self.project_dir / "dist" / "custom.txt"
        custom_file.write_text("custom content")

        # Build with clean (default)
        result = self.runner.invoke(cli, ["build"])

        self.assertEqual(result.exit_code, 0)
        self.assertFalse(custom_file.exists())

    def test_build_without_config_fails(self):
        """Test that build fails without configuration file."""
        # Remove config file
        (self.project_dir / "jinpress.yml").unlink()

        result = self.runner.invoke(cli, ["build"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error", result.output)

    def test_build_reports_page_count(self):
        """Test that build reports the number of pages built."""
        result = self.runner.invoke(cli, ["build"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Pages:", result.output)


class TestCLIServe(unittest.TestCase):
    """Integration tests for the 'serve' command (Requirement 9.2)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
        self.original_cwd = os.getcwd()

        # Create a project first
        os.chdir(self.test_dir)
        self.runner.invoke(cli, ["init", "test-project"])
        self.project_dir = Path(self.test_dir) / "test-project"
        os.chdir(self.project_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_serve_without_config_fails(self):
        """Test that serve fails without configuration file."""
        # Remove config file
        (self.project_dir / "jinpress.yml").unlink()

        result = self.runner.invoke(cli, ["serve", "--no-open"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error", result.output)


class TestCLIHelp(unittest.TestCase):
    """Integration tests for CLI help and version options."""

    def setUp(self):
        self.runner = CliRunner()

    def test_help_option(self):
        """Test that --help displays usage information (Requirement 9.4)."""
        result = self.runner.invoke(cli, ["--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("JinPress", result.output)
        self.assertIn("init", result.output)
        self.assertIn("serve", result.output)
        self.assertIn("build", result.output)

    def test_version_option(self):
        """Test that --version displays version information (Requirement 9.5)."""
        result = self.runner.invoke(cli, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("jinpress", result.output.lower())

    def test_init_help(self):
        """Test init command help."""
        result = self.runner.invoke(cli, ["init", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Initialize", result.output)

    def test_build_help(self):
        """Test build command help."""
        result = self.runner.invoke(cli, ["build", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Build", result.output)

    def test_serve_help(self):
        """Test serve command help."""
        result = self.runner.invoke(cli, ["serve", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("development server", result.output.lower())


class TestCLIErrorHandling(unittest.TestCase):
    """Integration tests for CLI error handling (Requirement 9.6)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_build_invalid_config_shows_error(self):
        """Test that invalid config shows descriptive error message."""
        # Create project with invalid config
        project_dir = Path(self.test_dir) / "bad-project"
        project_dir.mkdir()
        (project_dir / "docs").mkdir()

        # Create invalid YAML config
        config_path = project_dir / "jinpress.yml"
        config_path.write_text("site:\n  title: [invalid yaml")

        os.chdir(project_dir)
        result = self.runner.invoke(cli, ["build"])

        self.assertNotEqual(result.exit_code, 0)
        # Check for error indication (case-insensitive)
        self.assertIn("error", result.output.lower())


if __name__ == "__main__":
    unittest.main()
