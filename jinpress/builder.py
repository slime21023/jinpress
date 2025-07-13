"""
Site builder for JinPress.

Orchestrates the build process for static site generation.
"""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .renderer import Renderer
from .search import SearchIndexer
from .theme.engine import ThemeEngine


class BuildError(Exception):
    """Raised when there's an error during build process."""
    pass


class Builder:
    """Main site builder for JinPress."""
    
    def __init__(self, project_root: Path, config: Optional[Config] = None):
        """
        Initialize builder.
        
        Args:
            project_root: Root directory of the JinPress project
            config: Site configuration (will load from project_root if None)
        """
        self.project_root = Path(project_root)
        self.config = config or Config(self.project_root / "config.yml")
        self.renderer = Renderer(self.config.base)
        self.theme_engine = ThemeEngine(self.project_root)
        self.search_indexer = SearchIndexer()
        
        # Directories
        self.docs_dir = self.project_root / "docs"
        self.static_dir = self.project_root / "static"
        self.output_dir = self.project_root / "dist"
        self.cache_dir = self.project_root / ".jinpress" / "cache"
    
    def build(self, clean: bool = True) -> None:
        """
        Build the static site.
        
        Args:
            clean: Whether to clean output directory before building
        """
        print("Building JinPress site...")
        
        # Clean output directory if requested
        if clean:
            self._clean_output_dir()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process markdown files
        processed_files = self._process_markdown_files()
        print(f"Processed {len(processed_files)} pages")
        
        # Generate pages
        self._generate_pages(processed_files)
        
        # Copy static files
        self._copy_static_files()
        
        # Copy theme assets
        self._copy_theme_assets()
        
        # Generate search index
        self._generate_search_index()
        
        print(f"Site built successfully in {self.output_dir}")
    
    def _clean_output_dir(self) -> None:
        """Clean the output directory."""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
    
    def _process_markdown_files(self) -> List[Dict[str, Any]]:
        """
        Process all markdown files in the docs directory.
        
        Returns:
            List of processed file information
        """
        if not self.docs_dir.exists():
            raise BuildError(f"Docs directory not found: {self.docs_dir}")
        
        processed_files = []
        
        # Find all markdown files
        for md_file in self.docs_dir.rglob("*.md"):
            try:
                file_info = self.renderer.process_file(md_file, self.docs_dir)
                processed_files.append(file_info)
                
                # Add to search index
                self.search_indexer.add_document(file_info)
                
            except Exception as e:
                print(f"Warning: Failed to process {md_file}: {e}")
        
        return processed_files
    
    def _generate_pages(self, processed_files: List[Dict[str, Any]]) -> None:
        """
        Generate HTML pages from processed markdown files.
        
        Args:
            processed_files: List of processed file information
        """
        for file_info in processed_files:
            try:
                self._generate_page(file_info)
            except Exception as e:
                print(f"Warning: Failed to generate page for {file_info['file_path']}: {e}")
    
    def _generate_page(self, file_info: Dict[str, Any]) -> None:
        """
        Generate a single HTML page.
        
        Args:
            file_info: Processed file information
        """
        # Prepare template context
        page_data = self.renderer.get_page_data(file_info, self.config)
        context = self.theme_engine.get_template_context(page_data)
        
        # Render page
        html_content = self.theme_engine.render_page("page.html", context)
        
        # Determine output path
        output_path = self._get_output_path(file_info["url_path"])
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _get_output_path(self, url_path: str) -> Path:
        """
        Get output file path for a given URL path.
        
        Args:
            url_path: URL path (e.g., "/guide/installation/")
            
        Returns:
            Output file path
        """
        # Remove leading slash and ensure trailing slash
        clean_path = url_path.strip("/")
        
        if not clean_path:
            # Root page
            return self.output_dir / "index.html"
        
        # Create directory structure and index.html
        return self.output_dir / clean_path / "index.html"
    
    def _copy_static_files(self) -> None:
        """Copy user static files to output directory."""
        if not self.static_dir.exists():
            return
        
        dest_dir = self.output_dir / "static"
        
        try:
            shutil.copytree(self.static_dir, dest_dir, dirs_exist_ok=True)
            print(f"Copied static files from {self.static_dir}")
        except Exception as e:
            print(f"Warning: Failed to copy static files: {e}")
    
    def _copy_theme_assets(self) -> None:
        """Copy theme assets to output directory."""
        try:
            self.theme_engine.copy_static_files(self.output_dir)
            print("Copied theme assets")
        except Exception as e:
            print(f"Warning: Failed to copy theme assets: {e}")
    
    def _generate_search_index(self) -> None:
        """Generate search index file."""
        try:
            search_index_path = self.output_dir / "search-index.json"
            self.search_indexer.generate_index(search_index_path)
            print(f"Generated search index with {self.search_indexer.get_document_count()} documents")
        except Exception as e:
            print(f"Warning: Failed to generate search index: {e}")
    
    def get_build_info(self) -> Dict[str, Any]:
        """
        Get information about the build.
        
        Returns:
            Build information dictionary
        """
        return {
            "project_root": str(self.project_root),
            "docs_dir": str(self.docs_dir),
            "output_dir": str(self.output_dir),
            "config_file": str(self.config.config_path),
            "site_title": self.config.title,
            "site_base": self.config.base,
        }
