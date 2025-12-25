"""
Site builder for JinPress.

Orchestrates the build process for static site generation.
Integrates ConfigManager, TemplateEngine, and MarkdownProcessor.
"""

from __future__ import annotations

import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import Config, ConfigManager, JinPressConfig
from .markdown.processor import MarkdownProcessor, ProcessedPage
from .search import SearchIndexer
from .templates.engine import TemplateEngine
from .theme.engine import ThemeEngine

logger = logging.getLogger(__name__)


class BuildError(Exception):
    """Raised when there's an error during build process."""

    def __init__(self, message: str, file_path: Path | None = None):
        self.file_path = file_path
        if file_path:
            full_message = f"{message} (file: {file_path})"
        else:
            full_message = message
        super().__init__(full_message)


@dataclass
class BuildResult:
    """Result of a build operation."""

    success: bool
    pages_built: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


class BuildEngine:
    """
    Build engine for JinPress static site generation.

    Integrates ConfigManager, TemplateEngine, and MarkdownProcessor
    to provide a complete build pipeline.
    """

    def __init__(self, project_root: Path, config: JinPressConfig | None = None):
        """
        Initialize build engine.

        Args:
            project_root: Root directory of the JinPress project
            config: Site configuration (will load from project_root if None)
        """
        self.project_root = Path(project_root)

        # Load configuration
        if config is None:
            config_manager = ConfigManager()
            self.config = config_manager.load(self.project_root)
        else:
            self.config = config

        # Initialize directories
        self.docs_dir = self.project_root / "docs"
        self.static_dir = self.project_root / "static"
        self.output_dir = self.project_root / "dist"
        self.templates_dir = self.project_root / "templates"

        # Get theme templates directory
        theme_templates = Path(__file__).parent / "theme" / "default" / "templates"
        self.theme_templates_dir = theme_templates

        # Initialize processors
        self.markdown_processor = MarkdownProcessor(self.config.site.base)

        # Initialize template engine with user templates override
        user_templates = self.templates_dir if self.templates_dir.exists() else None
        self.template_engine = TemplateEngine(
            theme_dir=self.theme_templates_dir,
            user_templates_dir=user_templates,
            base_path=self.config.site.base,
        )

        # Initialize search indexer
        self.search_indexer = SearchIndexer()

        # Theme engine for static files
        self.theme_engine = ThemeEngine(self.project_root)

        # Track processed pages for navigation
        self._processed_pages: list[ProcessedPage] = []

    def build(self, clean: bool = True, incremental: bool = False) -> BuildResult:
        """
        Execute complete build process.

        Args:
            clean: Whether to clean output directory before building
            incremental: Whether to use incremental build (not yet implemented)

        Returns:
            BuildResult with build statistics
        """
        start_time = time.time()
        errors: list[str] = []
        warnings: list[str] = []
        pages_built = 0

        logger.info("Building JinPress site...")

        try:
            # Clean output directory if requested
            if clean:
                self._clean_output_dir()

            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Process all markdown files
            self._processed_pages = self._process_markdown_files(errors, warnings)
            pages_built = len(self._processed_pages)
            logger.info(f"Processed {pages_built} pages")

            # Generate HTML pages
            self._generate_pages(errors, warnings)

            # Copy static assets
            self._copy_static_assets()

            # Copy theme assets
            self._copy_theme_assets()

            # Generate search index
            self._generate_search_index()

            # Write GitHub Pages files
            self._write_github_pages_files()

            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"Site built successfully in {duration_ms:.2f}ms")

            return BuildResult(
                success=len(errors) == 0,
                pages_built=pages_built,
                errors=errors,
                warnings=warnings,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Build failed: {e}")
            errors.append(str(e))
            duration_ms = (time.time() - start_time) * 1000
            return BuildResult(
                success=False,
                pages_built=pages_built,
                errors=errors,
                warnings=warnings,
                duration_ms=duration_ms,
            )

    def _clean_output_dir(self) -> None:
        """Clean the output directory."""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            logger.debug(f"Cleaned output directory: {self.output_dir}")

    def _process_markdown_files(
        self, errors: list[str], warnings: list[str]
    ) -> list[ProcessedPage]:
        """
        Process all markdown files in the docs directory.

        Args:
            errors: List to append errors to
            warnings: List to append warnings to

        Returns:
            List of processed pages
        """
        if not self.docs_dir.exists():
            raise BuildError(f"Docs directory not found: {self.docs_dir}")

        processed_pages: list[ProcessedPage] = []

        # Find all markdown files
        for md_file in sorted(self.docs_dir.rglob("*.md")):
            try:
                page = self.markdown_processor.process_file(md_file, self.docs_dir)
                processed_pages.append(page)

                # Add to search index
                self._add_to_search_index(page)

            except Exception as e:
                warning_msg = f"Failed to process {md_file}: {e}"
                warnings.append(warning_msg)
                logger.warning(warning_msg)

        return processed_pages

    def _add_to_search_index(self, page: ProcessedPage) -> None:
        """Add a processed page to the search index."""
        # Convert ProcessedPage to the format expected by SearchIndexer
        file_info = {
            "title": page.title,
            "url_path": page.url_path,
            "description": page.description,
            "html_content": page.content_html,
        }
        self.search_indexer.add_document(file_info)

    def _generate_pages(self, errors: list[str], warnings: list[str]) -> None:
        """
        Generate HTML pages from processed markdown files.

        Args:
            errors: List to append errors to
            warnings: List to append warnings to
        """
        for page in self._processed_pages:
            try:
                self._generate_page(page)
            except Exception as e:
                warning_msg = f"Failed to generate page for {page.file_path}: {e}"
                warnings.append(warning_msg)
                logger.warning(warning_msg)

    def _generate_page(self, page: ProcessedPage) -> None:
        """
        Generate a single HTML page.

        Args:
            page: Processed page data
        """
        # Create page context
        context = self._create_page_context(page)

        # Render page using template engine
        html_content = self.template_engine.render("page.html", context)

        # Determine output path
        output_path = self._get_output_path(page.url_path)

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.debug(f"Generated: {output_path}")

    def _create_page_context(self, page: ProcessedPage) -> dict[str, Any]:
        """
        Create template context for a page.

        Args:
            page: Processed page data

        Returns:
            Template context dictionary
        """
        # Build sidebar items for current path
        sidebar_items = self._get_sidebar_items(page.url_path)

        # Build navigation items
        nav_items = self._get_nav_items()

        # Find prev/next pages
        prev_page, next_page = self._get_prev_next_pages(page)

        return {
            "site": {
                "title": self.config.site.title,
                "description": self.config.site.description,
                "lang": self.config.site.lang,
                "base": self.config.site.base,
            },
            "page": {
                "title": page.title,
                "description": page.description,
                "content": page.content_html,
                "toc": [
                    {"level": t.level, "text": t.text, "anchor": t.anchor}
                    for t in page.toc
                ],
                "url": page.url_path,
                "frontmatter": page.frontmatter,
                "last_modified": page.last_modified,
            },
            "theme": {
                "nav": nav_items,
                "sidebar": self.config.theme.sidebar,  # Pass full sidebar config (dict)
                "footer": self.config.theme.footer,
                "edit_link": self.config.theme.edit_link,
                "last_updated": self.config.theme.last_updated,
            },
            "nav": nav_items,
            "sidebar": sidebar_items,  # Filtered sidebar items for current path
            "prev_page": prev_page,
            "next_page": next_page,
            "base": (
                self.config.site.base.rstrip("/")
                if self.config.site.base != "/"
                else ""
            ),
        }

    def _get_nav_items(self) -> list[dict[str, str]]:
        """Get navigation items from config."""
        return self.config.theme.nav

    def _get_sidebar_items(self, current_path: str) -> list[dict[str, Any]]:
        """
        Get sidebar items for the current path.

        Args:
            current_path: Current page URL path

        Returns:
            List of sidebar items
        """
        sidebar_config = self.config.theme.sidebar

        # Find matching sidebar configuration
        for path_prefix, items in sidebar_config.items():
            if current_path.startswith(path_prefix):
                return items

        # Return empty list if no matching sidebar
        return []

    def _get_prev_next_pages(
        self, current_page: ProcessedPage
    ) -> tuple[dict[str, str] | None, dict[str, str] | None]:
        """
        Get previous and next pages for navigation.

        Args:
            current_page: Current page

        Returns:
            Tuple of (prev_page, next_page) dictionaries or None
        """
        # Find current page index
        current_idx = None
        for i, page in enumerate(self._processed_pages):
            if page.url_path == current_page.url_path:
                current_idx = i
                break

        if current_idx is None:
            return None, None

        prev_page = None
        next_page = None

        if current_idx > 0:
            prev = self._processed_pages[current_idx - 1]
            prev_page = {"title": prev.title, "url": prev.url_path}

        if current_idx < len(self._processed_pages) - 1:
            next_p = self._processed_pages[current_idx + 1]
            next_page = {"title": next_p.title, "url": next_p.url_path}

        return prev_page, next_page

    def _get_output_path(self, url_path: str) -> Path:
        """
        Get output file path for a given URL path.

        Args:
            url_path: URL path (e.g., "/guide/installation/")

        Returns:
            Output file path
        """
        # Remove base path prefix if present
        base = self.config.site.base.rstrip("/")
        if base and url_path.startswith(base):
            url_path = url_path[len(base) :]

        # Remove leading slash and ensure trailing slash
        clean_path = url_path.strip("/")

        if not clean_path:
            # Root page
            return self.output_dir / "index.html"

        # Create directory structure and index.html
        return self.output_dir / clean_path / "index.html"

    def _copy_static_assets(self) -> None:
        """Copy user static files to output directory."""
        if not self.static_dir.exists():
            return

        dest_dir = self.output_dir / "static"

        try:
            shutil.copytree(self.static_dir, dest_dir, dirs_exist_ok=True)
            logger.debug(f"Copied static files from {self.static_dir}")
        except Exception as e:
            logger.warning(f"Failed to copy static files: {e}")

    def _copy_theme_assets(self) -> None:
        """Copy theme assets to output directory."""
        try:
            self.theme_engine.copy_static_files(self.output_dir)
            logger.debug("Copied theme assets")
        except Exception as e:
            logger.warning(f"Failed to copy theme assets: {e}")

    def _generate_search_index(self) -> None:
        """Generate search index file."""
        try:
            search_index_path = self.output_dir / "search-index.json"
            self.search_indexer.generate_index(search_index_path)
            doc_count = self.search_indexer.get_document_count()
            logger.debug(f"Generated search index with {doc_count} documents")
        except Exception as e:
            logger.warning(f"Failed to generate search index: {e}")

    def _write_github_pages_files(self) -> None:
        """Write GitHub Pages support files."""
        # Write .nojekyll file
        nojekyll_path = self.output_dir / ".nojekyll"
        nojekyll_path.touch()
        logger.debug("Created .nojekyll file")

    def build_page(self, page: ProcessedPage) -> str:
        """
        Build a single page and return HTML content.

        Args:
            page: Processed page data

        Returns:
            Rendered HTML string
        """
        context = self._create_page_context(page)
        return self.template_engine.render("page.html", context)

    def get_build_info(self) -> dict[str, Any]:
        """
        Get information about the build configuration.

        Returns:
            Build information dictionary
        """
        return {
            "project_root": str(self.project_root),
            "docs_dir": str(self.docs_dir),
            "output_dir": str(self.output_dir),
            "site_title": self.config.site.title,
            "site_base": self.config.site.base,
        }


# URL path generation utilities
def generate_url_path(file_path: Path, docs_dir: Path, base_path: str = "/") -> str:
    """
    Generate clean URL path from file path.

    Args:
        file_path: Path to the Markdown file
        docs_dir: Root documentation directory
        base_path: Base URL path for the site

    Returns:
        Clean URL path (e.g., "/guide/getting-started/")
    """
    # Get relative path from docs directory
    try:
        rel_path = file_path.relative_to(docs_dir)
    except ValueError:
        rel_path = file_path

    # Convert to URL path
    url_path = str(rel_path).replace("\\", "/")

    # Remove .md extension
    if url_path.endswith(".md"):
        url_path = url_path[:-3]

    # Handle index files
    if url_path.endswith("/index") or url_path == "index":
        url_path = url_path.rsplit("index", 1)[0]

    # Ensure leading slash and trailing slash
    if not url_path.startswith("/"):
        url_path = "/" + url_path
    if not url_path.endswith("/"):
        url_path += "/"

    # Apply base path
    base = base_path.rstrip("/")
    if base and base != "/":
        url_path = base + url_path

    return url_path


def apply_base_path(url: str, base_path: str) -> str:
    """
    Apply base path prefix to a URL.

    Args:
        url: Original URL (e.g., "/assets/style.css")
        base_path: Base path to apply (e.g., "/my-project/")

    Returns:
        URL with base path applied (e.g., "/my-project/assets/style.css")
    """
    # Skip external URLs
    if url.startswith(("http://", "https://", "//", "#")):
        return url

    # Normalize base path
    base = base_path.rstrip("/")
    if not base or base == "/":
        return url

    # Ensure URL starts with /
    if not url.startswith("/"):
        url = "/" + url

    return base + url


# Legacy compatibility - keep the old Builder class
class Builder:
    """
    Legacy site builder for JinPress.

    This class is kept for backward compatibility.
    New code should use BuildEngine instead.
    """

    def __init__(self, project_root: Path, config: Config | None = None):
        """
        Initialize builder.

        Args:
            project_root: Root directory of the JinPress project
            config: Site configuration (will load from project_root if None)
        """
        self.project_root = Path(project_root)

        # Try to load config from jinpress.yml first, then config.yml
        if config is None:
            config_path = self.project_root / "jinpress.yml"
            if not config_path.exists():
                config_path = self.project_root / "config.yml"
            self.config = Config(config_path)
        else:
            self.config = config

        # Use the new BuildEngine internally
        config_manager = ConfigManager()
        try:
            jinpress_config = config_manager.load(self.project_root)
        except Exception:
            # Fall back to creating config from legacy Config object
            from .config import JinPressConfig, SiteConfig, ThemeConfig

            jinpress_config = JinPressConfig(
                site=SiteConfig(
                    title=self.config.get(
                        "site.title", self.config.get("title", "JinPress Site")
                    ),
                    description=self.config.get(
                        "site.description", self.config.get("description", "")
                    ),
                    lang=self.config.get("site.lang", self.config.get("lang", "zh-TW")),
                    base=self.config.get("site.base", self.config.get("base", "/")),
                ),
                theme=ThemeConfig(
                    nav=self.config.get("theme.nav", []),
                    sidebar=self.config.get("theme.sidebar", {}),
                    footer=self.config.get("theme.footer", {}),
                    edit_link=self.config.get("theme.edit_link"),
                    last_updated=self.config.get("theme.last_updated", True),
                ),
            )

        self._engine = BuildEngine(self.project_root, jinpress_config)

        # Expose directories for compatibility
        self.docs_dir = self._engine.docs_dir
        self.static_dir = self._engine.static_dir
        self.output_dir = self._engine.output_dir

        # Legacy components
        from .renderer import Renderer

        self.renderer = Renderer(self.config.get("site.base", "/"))
        self.theme_engine = self._engine.theme_engine
        self.search_indexer = self._engine.search_indexer

    def build(self, clean: bool = True) -> None:
        """
        Build the static site.

        Args:
            clean: Whether to clean output directory before building
        """
        result = self._engine.build(clean=clean)
        if not result.success:
            raise BuildError("; ".join(result.errors))

    def get_build_info(self) -> dict[str, Any]:
        """Get information about the build."""
        info = self._engine.get_build_info()
        info["config_file"] = str(self.config.config_path)
        return info
