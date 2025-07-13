"""
Search indexer for JinPress.

Generates search index from processed content for client-side search.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .renderer import Renderer


class SearchIndexer:
    """Search index generator for JinPress sites."""
    
    def __init__(self):
        """Initialize search indexer."""
        self.documents = []
    
    def add_document(self, file_info: Dict[str, Any]) -> None:
        """
        Add a document to the search index.
        
        Args:
            file_info: Processed file information from renderer
        """
        # Extract clean text content for indexing
        content = self._extract_text_content(file_info["html_content"])
        
        # Create search document
        doc = {
            "title": file_info["title"],
            "url": file_info["url_path"],
            "content": content,
            "description": file_info["description"],
        }
        
        self.documents.append(doc)
    
    def _extract_text_content(self, html_content: str) -> str:
        """
        Extract plain text from HTML content for indexing.
        
        Args:
            html_content: HTML content
            
        Returns:
            Plain text content
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
        
        return text.strip()
    
    def generate_index(self, output_path: Path) -> None:
        """
        Generate and save search index to file.
        
        Args:
            output_path: Path to save the search index JSON file
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write search index
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, separators=(',', ':'))
    
    def clear(self) -> None:
        """Clear all documents from the index."""
        self.documents.clear()
    
    def get_document_count(self) -> int:
        """Get the number of documents in the index."""
        return len(self.documents)
