"""
Template Engine for JinPress.

Provides a Layout-first template architecture using minijinja.
Supports template inheritance, user template overrides, and custom filters.
"""

import datetime
from collections.abc import Callable
from pathlib import Path


class TemplateError(Exception):
    """Raised when there's an error in template processing."""

    pass


class TemplateEngine:
    """
    Template engine with Layout-first architecture.

    Supports:
    - minijinja as the template engine
    - User template overrides (user templates take priority)
    - Template inheritance (extends) and block overrides
    - Custom filters for URL generation, date formatting, etc.
    """

    def __init__(
        self,
        theme_dir: Path,
        user_templates_dir: Path | None = None,
        base_path: str = "/",
    ):
        """
        Initialize template engine.

        Args:
            theme_dir: Path to the theme templates directory
            user_templates_dir: Optional path to user custom templates directory
            base_path: Base URL path for the site (default: "/")
        """
        self.theme_dir = Path(theme_dir)
        self.user_templates_dir = (
            Path(user_templates_dir) if user_templates_dir else None
        )
        self.base_path = base_path.rstrip("/") if base_path != "/" else ""

        # Import minijinja here to allow for better error handling
        try:
            from minijinja import Environment
        except ImportError as err:
            raise TemplateError(
                "minijinja is required but not installed. "
                "Install it with: pip install minijinja"
            ) from err

        self.env = Environment(loader=self._create_loader())
        self._register_filters()
        self._register_globals()

    def _create_loader(self) -> Callable[[str], str | None]:
        """
        Create template loader function.

        User templates take priority over theme templates.

        Returns:
            Template loader function
        """

        def loader(name: str) -> str | None:
            """Load template from user directory first, then theme directory."""
            # Priority 1: User templates directory
            if self.user_templates_dir:
                user_path = self.user_templates_dir / name
                if user_path.exists() and user_path.is_file():
                    return user_path.read_text(encoding="utf-8")

            # Priority 2: Theme templates directory
            theme_path = self.theme_dir / name
            if theme_path.exists() and theme_path.is_file():
                return theme_path.read_text(encoding="utf-8")

            return None

        return loader

    def _register_filters(self) -> None:
        """Register custom minijinja filters."""
        self.env.add_filter("url_for", self._filter_url_for)
        self.env.add_filter("asset_url", self._filter_asset_url)
        self.env.add_filter("format_date", self._filter_format_date)
        self.env.add_filter("relative_url", self._filter_relative_url)
        self.env.add_filter("safe", self._filter_safe)

    def _register_globals(self) -> None:
        """Register global variables and functions."""
        # Globals can be added here if needed
        pass

    def _filter_url_for(self, path: str, base: str | None = None) -> str:
        """
        Generate URL for a given path.

        Args:
            path: The path to generate URL for
            base: Optional base path override

        Returns:
            Full URL path
        """
        if path.startswith(("http://", "https://", "//")):
            return path

        effective_base = base.rstrip("/") if base else self.base_path
        path = path.lstrip("/")

        if not path:
            return effective_base + "/" if effective_base else "/"

        return f"{effective_base}/{path}"

    def _filter_asset_url(self, path: str) -> str:
        """
        Generate URL for static assets.

        Args:
            path: Asset path relative to assets directory

        Returns:
            Full asset URL
        """
        path = path.lstrip("/")
        if not path.startswith("assets/"):
            path = f"assets/{path}"
        return self._filter_url_for(path)

    def _filter_format_date(
        self,
        timestamp: float,
        format_str: str = "%Y-%m-%d",
    ) -> str:
        """
        Format timestamp as date string.

        Args:
            timestamp: Unix timestamp
            format_str: Date format string

        Returns:
            Formatted date string
        """
        try:
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt.strftime(format_str)
        except (ValueError, TypeError, OSError):
            return ""

    def _filter_relative_url(self, from_path: str, to_path: str) -> str:
        """
        Generate relative URL from one path to another.

        Args:
            from_path: Source path
            to_path: Target path

        Returns:
            Relative URL
        """
        from_parts = from_path.strip("/").split("/") if from_path.strip("/") else []
        to_parts = to_path.strip("/").split("/") if to_path.strip("/") else []

        # Find common prefix length
        common_length = 0
        for i, (a, b) in enumerate(zip(from_parts, to_parts, strict=False)):
            if a == b:
                common_length = i + 1
            else:
                break

        # Calculate relative path
        up_levels = len(from_parts) - common_length
        relative_parts = [".."] * up_levels + to_parts[common_length:]

        if not relative_parts:
            return "./"

        result = "/".join(relative_parts)
        if to_path.endswith("/"):
            result += "/"

        return result

    def _filter_safe(self, value: str) -> str:
        """
        Mark string as safe (no escaping).

        Uses minijinja's Markup class to prevent auto-escaping.

        Args:
            value: String value

        Returns:
            Markup object that won't be escaped
        """
        from minijinja import Markup

        return Markup(value)

    def render(self, template_name: str, context: dict[str, object]) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Template context data

        Returns:
            Rendered HTML string

        Raises:
            TemplateError: If template rendering fails
        """
        try:
            return self.env.render_template(template_name, **context)
        except Exception as e:
            raise TemplateError(
                f"Error rendering template '{template_name}': {e}"
            ) from e

    def has_template(self, template_name: str) -> bool:
        """
        Check if a template exists.

        Args:
            template_name: Name of the template

        Returns:
            True if template exists, False otherwise
        """
        # Check user templates first
        if self.user_templates_dir:
            user_path = self.user_templates_dir / template_name
            if user_path.exists() and user_path.is_file():
                return True

        # Check theme templates
        theme_path = self.theme_dir / template_name
        return theme_path.exists() and theme_path.is_file()

    def get_template_source(self, template_name: str) -> str | None:
        """
        Get the source path of a template.

        Useful for debugging which template is being used.

        Args:
            template_name: Name of the template

        Returns:
            Path to the template file, or None if not found
        """
        # Check user templates first
        if self.user_templates_dir:
            user_path = self.user_templates_dir / template_name
            if user_path.exists() and user_path.is_file():
                return str(user_path)

        # Check theme templates
        theme_path = self.theme_dir / template_name
        if theme_path.exists() and theme_path.is_file():
            return str(theme_path)

        return None

    def list_templates(self) -> list[str]:
        """
        List all available templates.

        Returns:
            List of template names (user templates override theme templates)
        """
        templates = set()

        # Add theme templates
        if self.theme_dir.exists():
            for path in self.theme_dir.rglob("*.html"):
                rel_path = path.relative_to(self.theme_dir)
                templates.add(str(rel_path).replace("\\", "/"))

        # Add user templates (these will override theme templates with same name)
        if self.user_templates_dir and self.user_templates_dir.exists():
            for path in self.user_templates_dir.rglob("*.html"):
                rel_path = path.relative_to(self.user_templates_dir)
                templates.add(str(rel_path).replace("\\", "/"))

        return sorted(templates)
