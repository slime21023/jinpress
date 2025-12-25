"""JinPress Markdown Processor module.

Handles Markdown parsing, front matter extraction, and content transformation.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

from jinpress.markdown.containers import container_plugin


@dataclass
class TocItem:
    """Table of Contents item."""

    level: int
    text: str
    anchor: str
    children: list[TocItem] = field(default_factory=list)


@dataclass
class ProcessedPage:
    """Processed Markdown page data."""

    title: str
    description: str
    content_html: str
    frontmatter: dict[str, any]
    toc: list[TocItem]
    raw_content: str
    file_path: Path
    url_path: str
    last_modified: float


class MarkdownProcessor:
    """Markdown processor with front matter, TOC, and syntax highlighting support."""

    def __init__(self, base_path: str = "/"):
        """Initialize the Markdown processor.

        Args:
            base_path: Base URL path for link generation.
        """
        self.base_path = base_path.rstrip("/") + "/" if base_path != "/" else "/"
        self._setup_parser()

    def _setup_parser(self):
        """Set up markdown-it-py parser with plugins."""
        self.md = MarkdownIt("commonmark", {"html": True, "typographer": True})
        self.md.enable("table")
        self.md.enable("strikethrough")

        # Add front matter plugin
        self.md.use(front_matter_plugin)

        # Add anchors plugin for heading anchors
        self.md.use(anchors_plugin, permalink=True, permalinkSymbol="🔗")

        # Add custom container plugin
        self.md.use(container_plugin)

        # Store original fence renderer for code highlighting
        self._original_fence = self.md.renderer.rules.get("fence")
        self.md.renderer.rules["fence"] = self._render_fence

        # Store original link renderer for .md link transformation
        self._original_link_open = self.md.renderer.rules.get("link_open")
        self.md.renderer.rules["link_open"] = self._render_link_open

    def _render_fence(self, tokens, idx, options, env):
        """Custom fence renderer with Pygments syntax highlighting."""
        token = tokens[idx]
        code = token.content
        lang = token.info.strip() if token.info else ""

        if lang:
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except ClassNotFound:
                try:
                    lexer = guess_lexer(code)
                except ClassNotFound:
                    lexer = None
        else:
            lexer = None

        if lexer:
            formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
            highlighted = highlight(code, lexer, formatter)
            return f'<div class="code-block" data-lang="{lang}">{highlighted}</div>'
        else:
            escaped_code = self._escape_html(code)
            return f'<pre><code class="language-{lang}">{escaped_code}</code></pre>'

    def _render_link_open(self, tokens, idx, options, env):
        """Custom link renderer to transform .md links to clean URLs."""
        token = tokens[idx]

        # Get href from attrs (attrs is now a dictionary)
        href = token.attrs.get("href") if isinstance(token.attrs, dict) else None
        if href is None and hasattr(token, "attrGet"):
            href = token.attrGet("href")

        if href:
            transformed_href = self._transform_md_link(href)
            # Update the href attribute
            if isinstance(token.attrs, dict):
                token.attrs["href"] = transformed_href
            else:
                token.attrSet("href", transformed_href)

        # Render the token
        return self.md.renderer.renderToken(tokens, idx, options, env)

    def _transform_md_link(self, href: str) -> str:
        """Transform .md links to clean URLs.

        Args:
            href: Original href value.

        Returns:
            Transformed href with .md replaced by clean URL.
        """
        # Skip external links and anchors
        if href.startswith(("http://", "https://", "mailto:", "#")):
            return href

        # Handle relative .md links
        if href.endswith(".md"):
            # Remove .md extension and add trailing slash
            clean_path = href[:-3]
            # Handle index.md specially
            if clean_path.endswith("/index") or clean_path == "index":
                clean_path = clean_path.rsplit("index", 1)[0]
            if not clean_path.endswith("/"):
                clean_path += "/"
            return clean_path

        return href

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def process_file(self, file_path: Path, docs_dir: Path) -> ProcessedPage:
        """Process a single Markdown file.

        Args:
            file_path: Path to the Markdown file.
            docs_dir: Root documentation directory.

        Returns:
            ProcessedPage with all extracted data.
        """
        content = file_path.read_text(encoding="utf-8")
        frontmatter, body = self.extract_frontmatter(content)

        # Extract TOC before rendering
        toc = self.extract_toc(body)

        # Render Markdown to HTML
        content_html = self.md.render(body)

        # Transform any remaining .md links in HTML
        content_html = self.transform_links(content_html)

        # Generate URL path
        url_path = self._generate_url_path(file_path, docs_dir)

        # Get title from frontmatter or first heading
        title = frontmatter.get("title", "")
        if not title and toc:
            title = toc[0].text
        if not title:
            title = file_path.stem.replace("-", " ").replace("_", " ").title()

        # Get description from frontmatter
        description = frontmatter.get("description", "")

        # Get last modified time
        last_modified = os.path.getmtime(file_path)

        return ProcessedPage(
            title=title,
            description=description,
            content_html=content_html,
            frontmatter=frontmatter,
            toc=toc,
            raw_content=content,
            file_path=file_path,
            url_path=url_path,
            last_modified=last_modified,
        )

    def extract_frontmatter(self, content: str) -> tuple[dict[str, any], str]:
        """Extract YAML front matter from content.

        Args:
            content: Raw Markdown content.

        Returns:
            Tuple of (frontmatter dict, remaining content).
        """
        # Match YAML front matter at the start of the file
        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, content, re.DOTALL)

        if match:
            yaml_content = match.group(1)
            try:
                frontmatter = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = content[match.end() :]
            return frontmatter, body

        return {}, content

    def extract_toc(self, content: str) -> list[TocItem]:
        """Extract table of contents from Markdown content.

        Args:
            content: Markdown content (without front matter).

        Returns:
            List of TocItem representing the heading hierarchy.
        """
        # Match ATX-style headings (# Heading)
        heading_pattern = r"^(#{1,6})\s+(.+?)(?:\s+#*)?$"

        toc_items: list[TocItem] = []

        for line in content.split("\n"):
            match = re.match(heading_pattern, line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                # Generate anchor from text
                anchor = self._generate_anchor(text)

                toc_item = TocItem(level=level, text=text, anchor=anchor)
                toc_items.append(toc_item)

        return self._build_toc_hierarchy(toc_items)

    def _generate_anchor(self, text: str) -> str:
        """Generate URL-safe anchor from heading text.

        Args:
            text: Heading text.

        Returns:
            URL-safe anchor string.
        """
        # Remove special characters and convert to lowercase
        anchor = text.lower()
        # Replace spaces with hyphens
        anchor = re.sub(r"\s+", "-", anchor)
        # Remove non-alphanumeric characters except hyphens
        anchor = re.sub(r"[^\w\-]", "", anchor)
        # Remove consecutive hyphens
        anchor = re.sub(r"-+", "-", anchor)
        # Strip leading/trailing hyphens
        anchor = anchor.strip("-")
        return anchor

    def _build_toc_hierarchy(self, items: list[TocItem]) -> list[TocItem]:
        """Build hierarchical TOC structure from flat list.

        Args:
            items: Flat list of TocItem.

        Returns:
            Hierarchical list of TocItem with children populated.
        """
        if not items:
            return []

        # For simplicity, return flat list with level info
        # A more complex implementation could build nested structure
        return items

    def _generate_url_path(self, file_path: Path, docs_dir: Path) -> str:
        """Generate clean URL path from file path.

        Args:
            file_path: Path to the Markdown file.
            docs_dir: Root documentation directory.

        Returns:
            Clean URL path.
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
        if self.base_path != "/":
            url_path = self.base_path.rstrip("/") + url_path

        return url_path

    def transform_links(self, html: str) -> str:
        """Transform .md links in HTML to clean URLs.

        Args:
            html: HTML content.

        Returns:
            HTML with transformed links.
        """
        # Pattern to match href attributes with .md links
        pattern = r'href="([^"]*\.md)"'

        def replace_link(match):
            href = match.group(1)
            transformed = self._transform_md_link(href)
            return f'href="{transformed}"'

        return re.sub(pattern, replace_link, html)
