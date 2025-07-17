"""
Markdown renderer and content processor for JinPress.

Handles markdown parsing, front matter extraction, and content transformation.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound


class RendererError(Exception):
    """Raised when there's an error in rendering."""
    pass


class JinPressRenderer(RendererHTML):
    """Custom renderer for JinPress with enhanced features."""
    
    def __init__(self, base_path: str = "/"):
        super().__init__()
        self.base_path = str(base_path).rstrip("/") + "/"
    
    def fence(self, tokens, idx, options, env):
        """Render code blocks with syntax highlighting."""
        token = tokens[idx]
        info = token.info.strip() if token.info else ""
        lang = info.split()[0] if info else ""
        
        # Extract line highlighting info
        highlight_lines = []
        if "{" in info and "}" in info:
            match = re.search(r'\{([^}]+)\}', info)
            if match:
                highlight_spec = match.group(1)
                # Parse line numbers (e.g., "1,3-5,7")
                for part in highlight_spec.split(","):
                    if "-" in part:
                        start, end = map(int, part.split("-"))
                        highlight_lines.extend(range(start, end + 1))
                    else:
                        highlight_lines.append(int(part))
        
        # Get code content
        code = token.content
        
        # Apply syntax highlighting
        if lang:
            try:
                lexer = get_lexer_by_name(lang)
                formatter = HtmlFormatter(
                    cssclass="highlight",
                    linenos=True,
                    hl_lines=highlight_lines
                )
                highlighted = highlight(code, lexer, formatter)
                return f'<div class="language-{lang}">{highlighted}</div>'
            except ClassNotFound:
                pass
        
        # Fallback for unknown languages
        import html
        escaped_code = html.escape(code)
        return f'<pre><code class="language-{lang}">{escaped_code}</code></pre>'


class Renderer:
    """Main content renderer for JinPress."""
    
    def __init__(self, base_path: str = "/"):
        """
        Initialize renderer.
        
        Args:
            base_path: Base path for the site
        """
        self.base_path = base_path
        self.md = self._setup_markdown()
    
    def _setup_markdown(self) -> MarkdownIt:
        """Set up markdown-it with plugins and custom renderer."""
        md = MarkdownIt("commonmark", {
            "html": True,
            "linkify": True,
            "typographer": True,
        })
        
        # Add plugins
        md.use(front_matter_plugin)
        
        # Add container plugins
        md.use(container_plugin, name="tip")
        md.use(container_plugin, name="warning") 
        md.use(container_plugin, name="danger")
        md.use(container_plugin, name="info")
        md.use(container_plugin, name="details")
        
        # Set custom renderer
        md.renderer = JinPressRenderer(self.base_path)
        
        # Add link transformation rule
        md.add_render_rule("link_open", self._render_link_open)
        
        # Add container render rules
        md.add_render_rule("container_tip_open", self._render_container_open)
        md.add_render_rule("container_tip_close", self._render_container_close)
        md.add_render_rule("container_warning_open", self._render_container_open)
        md.add_render_rule("container_warning_close", self._render_container_close)
        md.add_render_rule("container_danger_open", self._render_container_open)
        md.add_render_rule("container_danger_close", self._render_container_close)
        md.add_render_rule("container_info_open", self._render_container_open)
        md.add_render_rule("container_info_close", self._render_container_close)
        md.add_render_rule("container_details_open", self._render_container_open)
        md.add_render_rule("container_details_close", self._render_container_close)
        
        return md
    
    def _render_link_open(self, tokens, idx, options, env):
        """Custom link renderer to handle .md file links."""
        token = tokens[idx]
        
        # Get href attribute
        href = token.attrs.get("href")
        if href:
            # Transform .md links to pretty URLs
            if href.endswith(".md"):
                # Remove .md extension and ensure trailing slash
                new_href = href[:-3]
                if not new_href.endswith("/"):
                    new_href += "/"
                token.attrs["href"] = new_href
            
            # Handle relative links (keep as is for now)
            elif href.startswith("./") or href.startswith("../"):
                # Keep relative paths as they are
                pass
        
        # Render the link opening tag
        attrs = []
        for key, value in token.attrs.items():
            attrs.append(f'{key}="{value}"')
        
        attrs_str = " " + " ".join(attrs) if attrs else ""
        return f"<a{attrs_str}>"
    
    def _render_container_open(self, tokens, idx, options, env):
        """Custom container opening renderer."""
        token = tokens[idx]
        info = token.info.strip() if token.info else ""
        container_type = info.split()[0] if info else "container"
        return f'<div class="container-{container_type}">\n'
    
    def _render_container_close(self, tokens, idx, options, env):
        """Custom container closing renderer."""
        return '</div>\n'
    
    def _render_container(self, tokens, idx, options, env):
        """Custom container renderer for tip, warning, danger, info containers."""
        token = tokens[idx]
        info = token.info.strip() if token.info else ""
        
        if token.nesting == 1:
            # Opening tag
            container_type = info.split()[0] if info else "container"
            return f'<div class="container-{container_type}">\n'
        else:
            # Closing tag
            return '</div>\n'
    
    def extract_front_matter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Extract YAML front matter from markdown content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Tuple of (front_matter_dict, content_without_front_matter)
        """
        front_matter = {}
        
        # Check for front matter
        if content.startswith("---\n"):
            try:
                # Find the end of front matter
                end_match = re.search(r'\n---\n', content)
                if end_match:
                    front_matter_text = content[4:end_match.start()]
                    content = content[end_match.end():]
                    front_matter = yaml.safe_load(front_matter_text) or {}
            except yaml.YAMLError as e:
                raise RendererError(f"Invalid YAML front matter: {e}")
        
        return front_matter, content
    
    def render_markdown(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Render markdown file to HTML with metadata extraction.
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            Tuple of (rendered_html, metadata_dict)
        """
        if not file_path.exists():
            raise RendererError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except Exception as e:
            raise RendererError(f"Error reading file {file_path}: {e}")
        
        # Extract front matter
        front_matter, content = self.extract_front_matter(raw_content)
        
        # Render markdown to HTML
        html = self.md.render(content)
        
        return html, front_matter
    
    def process_file(self, file_path: Path, docs_dir: Path) -> Dict[str, Any]:
        """
        Process a markdown file and extract all necessary information.
        
        Args:
            file_path: Path to the markdown file
            docs_dir: Base docs directory
            
        Returns:
            Dictionary containing processed file information
        """
        if not file_path.exists():
            raise RendererError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except Exception as e:
            raise RendererError(f"Error reading file {file_path}: {e}")
        
        # Extract front matter
        front_matter, content = self.extract_front_matter(raw_content)
        
        # Render markdown to HTML
        html_content = self.md.render(content)
        
        # Calculate relative path from docs directory
        relative_path = file_path.relative_to(docs_dir)
        
        # Generate URL path
        url_path = self._generate_url_path(relative_path)
        
        # Extract title from front matter or content
        title = front_matter.get("title")
        if not title:
            title = self._extract_title_from_content(content)
        
        # Extract description
        description = front_matter.get("description", "")
        if not description:
            description = self._extract_description_from_content(content)
        
        return {
            "file_path": file_path,
            "relative_path": relative_path,
            "url_path": url_path,
            "title": title,
            "description": description,
            "front_matter": front_matter,
            "raw_content": raw_content,
            "markdown_content": content,
            "html_content": html_content,
            "last_modified": file_path.stat().st_mtime,
        }
    
    def _generate_url_path(self, relative_path: Path) -> str:
        """Generate URL path from file path."""
        # Convert path to URL format
        url_parts = list(relative_path.parts)
        
        # Handle index files
        if relative_path.name == "index.md":
            if len(url_parts) == 1:
                # Root index.md -> /
                return "/"
            else:
                # Nested index.md -> /path/to/dir/
                return "/" + "/".join(url_parts[:-1]) + "/"
        
        # Regular files: remove .md extension and add trailing slash
        if relative_path.suffix == ".md":
            url_parts[-1] = relative_path.stem
        
        return "/" + "/".join(url_parts) + "/"
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract title from markdown content (first h1)."""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return "Untitled"
    
    def _extract_description_from_content(self, content: str) -> str:
        """Extract description from markdown content (first paragraph)."""
        lines = content.split('\n')
        description_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and headers
            if not line or line.startswith('#'):
                continue
            # Stop at code blocks or other special content
            if line.startswith('```') or line.startswith(':::'):
                break
            description_lines.append(line)
            # Stop after first paragraph (when we hit an empty line)
            if len(description_lines) > 0:
                break
        
        description = ' '.join(description_lines)
        # Truncate if too long
        if len(description) > 160:
            description = description[:157] + "..."
        
        return description
    
    def get_page_data(self, file_info: Dict[str, Any], config: Any) -> Dict[str, Any]:
        """
        Generate complete page data for template rendering.
        
        Args:
            file_info: Processed file information
            config: Site configuration
            
        Returns:
            Complete page data for template
        """
        return {
            "title": file_info["title"],
            "description": file_info["description"],
            "content": file_info["html_content"],
            "frontmatter": file_info["front_matter"],
            "url": file_info["url_path"],
            "lastModified": file_info["last_modified"],
            "site": {
                "title": config.title,
                "description": config.description,
                "lang": config.lang,
                "base": config.base,
            },
            "page": {
                "title": file_info["title"],
                "description": file_info["description"],
                "frontmatter": file_info["front_matter"],
            },
            "theme": config.theme_config,
        }
