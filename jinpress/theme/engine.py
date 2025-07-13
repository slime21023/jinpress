"""
Theme engine for JinPress.

Handles template loading, rendering, and theme customization.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from minijinja import Environment, FileSystemLoader


class ThemeError(Exception):
    """Raised when there's an error in theme processing."""
    pass


class ThemeEngine:
    """Theme engine for JinPress sites."""
    
    def __init__(self, project_root: Path, theme_name: str = "default"):
        """
        Initialize theme engine.
        
        Args:
            project_root: Root directory of the JinPress project
            theme_name: Name of the theme to use
        """
        self.project_root = Path(project_root)
        self.theme_name = theme_name
        self.env = self._setup_environment()
    
    def _setup_environment(self) -> Environment:
        """Set up Jinja2 environment with proper template loading."""
        # Template search paths (in order of priority)
        template_paths = []
        
        # 1. User custom templates (highest priority)
        user_templates = self.project_root / "templates"
        if user_templates.exists():
            template_paths.append(str(user_templates))
        
        # 2. Default theme templates
        default_theme_path = Path(__file__).parent / "default" / "templates"
        if default_theme_path.exists():
            template_paths.append(str(default_theme_path))
        
        if not template_paths:
            raise ThemeError("No template directories found")
        
        # Create environment with FileSystemLoader
        loader = FileSystemLoader(template_paths)
        env = Environment(loader=loader)
        
        # Add custom filters and functions
        self._add_custom_filters(env)
        
        return env
    
    def _add_custom_filters(self, env: Environment) -> None:
        """Add custom Jinja2 filters and functions."""
        
        def url_for(path: str, base: str = "/") -> str:
            """Generate URL for a given path."""
            if path.startswith("http"):
                return path
            
            base = base.rstrip("/")
            path = path.lstrip("/")
            
            if not path:
                return base + "/"
            
            return f"{base}/{path}"
        
        def relative_url(from_path: str, to_path: str) -> str:
            """Generate relative URL from one path to another."""
            from_parts = from_path.strip("/").split("/") if from_path.strip("/") else []
            to_parts = to_path.strip("/").split("/") if to_path.strip("/") else []
            
            # Calculate relative path
            common_length = 0
            for i, (a, b) in enumerate(zip(from_parts, to_parts)):
                if a == b:
                    common_length = i + 1
                else:
                    break
            
            # Go up from current path
            up_levels = len(from_parts) - common_length
            relative_parts = [".."] * up_levels + to_parts[common_length:]
            
            if not relative_parts:
                return "./"
            
            return "/".join(relative_parts) + ("/" if to_path.endswith("/") else "")
        
        def format_date(timestamp: float, format_str: str = "%Y-%m-%d") -> str:
            """Format timestamp as date string."""
            import datetime
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt.strftime(format_str)
        
        # Register filters
        env.filters["url_for"] = url_for
        env.filters["relative_url"] = relative_url
        env.filters["format_date"] = format_date
    
    def render_page(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a page using the specified template.
        
        Args:
            template_name: Name of the template file
            context: Template context data
            
        Returns:
            Rendered HTML content
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            raise ThemeError(f"Error rendering template '{template_name}': {e}")
    
    def get_static_files(self) -> List[Path]:
        """
        Get list of static files from the theme.
        
        Returns:
            List of static file paths
        """
        static_files = []
        
        # Default theme static files
        default_static = Path(__file__).parent / "default" / "static"
        if default_static.exists():
            for file_path in default_static.rglob("*"):
                if file_path.is_file():
                    static_files.append(file_path)
        
        return static_files
    
    def copy_static_files(self, output_dir: Path) -> None:
        """
        Copy theme static files to output directory.
        
        Args:
            output_dir: Output directory for built site
        """
        import shutil
        
        static_files = self.get_static_files()
        theme_static_dir = Path(__file__).parent / "default" / "static"
        
        for file_path in static_files:
            # Calculate relative path from theme static directory
            relative_path = file_path.relative_to(theme_static_dir)
            
            # Create destination path
            dest_path = output_dir / "assets" / relative_path
            
            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(file_path, dest_path)
    
    def get_template_context(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare template context with theme-specific data.
        
        Args:
            page_data: Page data from renderer
            
        Returns:
            Complete template context
        """
        # Base context
        context = page_data.copy()
        
        # Add theme-specific helpers
        context.update({
            "theme": {
                "name": self.theme_name,
                "assets_base": "/assets/",
            }
        })
        
        return context
    
    def has_template(self, template_name: str) -> bool:
        """
        Check if a template exists.
        
        Args:
            template_name: Name of the template
            
        Returns:
            True if template exists, False otherwise
        """
        try:
            self.env.get_template(template_name)
            return True
        except:
            return False
