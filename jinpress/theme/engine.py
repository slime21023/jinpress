"""
Theme engine for JinPress.

Handles template loading, rendering, and theme customization.
"""

from pathlib import Path
from typing import Any

from minijinja import Environment


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
        """Set up minijinja environment with proper template loading."""
        template_paths = self._get_template_paths()

        if not template_paths:
            raise ThemeError("No template directories found")

        env = Environment(loader=self._create_template_loader(template_paths))
        self._add_custom_filters(env)

        return env

    def _get_template_paths(self) -> list[str]:
        """Get template search paths - user templates OR default templates."""
        # 1. Check for user custom templates first
        user_templates = self.project_root / "templates"
        if user_templates.exists() and user_templates.is_dir():
            return [str(user_templates)]

        # 2. Fall back to default theme templates
        default_theme_path = Path(__file__).parent / "default" / "templates"
        if default_theme_path.exists() and default_theme_path.is_dir():
            return [str(default_theme_path)]

        # 3. No valid template directory found
        return []

    def _create_template_loader(self, template_paths: list[str]):
        """Create a template loader function for the given paths."""

        def template_loader(name: str) -> str | None:
            """Load template from the first available path."""
            for template_path in template_paths:
                template_file = Path(template_path) / name
                if template_file.is_file():
                    return template_file.read_text(encoding="utf-8")
            return None

        return template_loader

    def _add_custom_filters(self, env: Environment) -> None:
        """Add custom minijinja filters and functions."""

        def url_for(path: str, base: str = "/") -> str:
            """Generate URL for a given path."""
            if path.startswith("http"):
                return path

            # Handle None base
            if base is None:
                base = "/"

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
            for i, (a, b) in enumerate(zip(from_parts, to_parts, strict=False)):
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
        env.add_filter("url_for", url_for)
        env.add_filter("relative_url", relative_url)
        env.add_filter("format_date", format_date)

    def render_page(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render a page using the specified template.

        Args:
            template_name: Name of the template file
            context: Template context data

        Returns:
            Rendered HTML content
        """
        try:
            return self.env.render_template(template_name, **context)
        except Exception as e:
            raise ThemeError(f"Error rendering template '{template_name}': {e}") from e

    def get_static_files(self) -> list[Path]:
        """
        Get list of static files from the theme (exclusive mode).

        Returns:
            List of static file paths
        """
        static_files = []

        # 1. Check for user custom theme static files first
        user_static = self.project_root / "templates" / "static"
        if user_static.exists() and user_static.is_dir():
            for file_path in user_static.rglob("*"):
                if file_path.is_file():
                    static_files.append(file_path)
            return static_files

        # 2. Fall back to default theme static files
        default_static = Path(__file__).parent / "default" / "static"
        if default_static.exists():
            for file_path in default_static.rglob("*"):
                if file_path.is_file():
                    static_files.append(file_path)

        return static_files

    def copy_static_files(self, output_dir: Path) -> None:
        """
        Copy theme static files to output directory (exclusive mode).

        Args:
            output_dir: Output directory for built site
        """
        import shutil

        static_files = self.get_static_files()
        if not static_files:
            return

        # Determine the source static directory
        user_static = self.project_root / "templates" / "static"
        if user_static.exists() and user_static.is_dir():
            # Using user custom theme static files
            theme_static_dir = user_static
        else:
            # Using default theme static files
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

    def get_template_context(self, page_data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare template context with theme-specific data.

        Args:
            page_data: Page data from renderer

        Returns:
            Complete template context
        """
        # Base context
        context = page_data.copy()

        # Preserve existing theme config and add theme-specific helpers
        if "theme" in context:
            context["theme"].update(
                {
                    "name": self.theme_name,
                    "assets_base": "/assets/",
                }
            )
        else:
            context["theme"] = {
                "name": self.theme_name,
                "assets_base": "/assets/",
            }

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
            # Try to render the template with empty context to check if it exists
            self.env.render_template(template_name, {})
            return True
        except Exception:
            # Check if template exists by trying to load it directly
            template_paths = [
                self.project_root / "templates",
                Path(__file__).parent / "default" / "templates",
            ]
            for template_path in template_paths:
                if template_path.exists() and (template_path / template_name).is_file():
                    return True
            return False
