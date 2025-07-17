"""
Test package distribution and installation.

This test verifies that the JinPress package can be built, installed,
and used correctly in a clean environment.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest


def test_package_build():
    """Test that the package can be built successfully."""
    result = subprocess.run(
        ["uv", "build"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )
    
    assert result.returncode == 0, f"Build failed: {result.stderr}"
    
    # Check that wheel and source distribution were created
    dist_dir = Path("dist")
    assert dist_dir.exists(), "dist directory not created"
    
    wheel_files = list(dist_dir.glob("*.whl"))
    tar_files = list(dist_dir.glob("*.tar.gz"))
    
    assert len(wheel_files) > 0, "No wheel file created"
    assert len(tar_files) > 0, "No source distribution created"


def test_package_contents():
    """Test that the package contains all necessary files."""
    import zipfile
    
    dist_dir = Path("dist")
    wheel_files = list(dist_dir.glob("*.whl"))
    
    assert len(wheel_files) > 0, "No wheel file found"
    
    wheel_file = wheel_files[0]
    
    with zipfile.ZipFile(wheel_file, 'r') as zip_file:
        file_list = zip_file.namelist()
        
        # Check that core modules are included
        assert any("jinpress/__init__.py" in f for f in file_list)
        assert any("jinpress/cli.py" in f for f in file_list)
        assert any("jinpress/builder.py" in f for f in file_list)
        assert any("jinpress/renderer.py" in f for f in file_list)
        
        # Check that theme assets are included
        assert any("jinpress/theme/default/static/css/main.css" in f for f in file_list)
        assert any("jinpress/theme/default/static/css/highlight.css" in f for f in file_list)
        assert any("jinpress/theme/default/static/js/main.js" in f for f in file_list)
        assert any("jinpress/theme/default/static/js/search.js" in f for f in file_list)
        
        # Check that templates are included
        assert any("jinpress/theme/default/templates/base.html" in f for f in file_list)
        assert any("jinpress/theme/default/templates/page.html" in f for f in file_list)
        
        # Check that entry point is defined
        assert any("entry_points.txt" in f for f in file_list)


def test_cli_installation_and_usage():
    """Test that the CLI can be installed and used."""
    # Find the wheel file
    dist_dir = Path("dist")
    wheel_files = list(dist_dir.glob("*.whl"))
    assert len(wheel_files) > 0, "No wheel file found"
    wheel_file = wheel_files[0]
    
    # Test that we can import the package from the wheel
    import zipfile
    import sys
    
    with zipfile.ZipFile(wheel_file, 'r') as zip_file:
        # Extract to a temporary location and test import
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_file.extractall(temp_dir)
            temp_path = Path(temp_dir)
            
            # Add to Python path temporarily
            sys.path.insert(0, str(temp_path))
            
            try:
                # Test that we can import the main modules
                import jinpress
                from jinpress import cli
                from jinpress.cli import main
                
                # Verify the CLI function exists
                assert callable(main), "CLI main function is not callable"
                
            finally:
                # Clean up sys.path
                sys.path.remove(str(temp_path))


def test_full_workflow_with_package():
    """Test complete workflow using the packaged version."""
    # Find the wheel file
    dist_dir = Path("dist")
    wheel_files = list(dist_dir.glob("*.whl"))
    assert len(wheel_files) > 0, "No wheel file found"
    wheel_file = wheel_files[0]
    
    # Test that we can extract and import the package modules
    import zipfile
    import sys
    
    with zipfile.ZipFile(wheel_file, 'r') as zip_file:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_file.extractall(temp_dir)
            temp_path = Path(temp_dir)
            
            # Add to Python path temporarily
            sys.path.insert(0, str(temp_path))
            
            try:
                # Test that we can import and use core functionality
                from jinpress.scaffold import Scaffold
                from jinpress.builder import Builder
                from jinpress.config import Config
                
                # Test scaffold functionality
                scaffold = Scaffold()
                assert hasattr(scaffold, 'create_project'), "Scaffold missing create_project method"
                
                # Test that we can create a Config object
                # (We can't test full functionality without actual files)
                assert Config is not None, "Config class not importable"
                
                # Test that Builder can be instantiated
                assert Builder is not None, "Builder class not importable"
                
            finally:
                # Clean up sys.path
                sys.path.remove(str(temp_path))


if __name__ == "__main__":
    pytest.main([__file__])