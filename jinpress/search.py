"""
Search indexer for JinPress.

Generates search index from processed content for client-side search.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SearchDocument:
    """A document in the search index."""

    url: str
    title: str
    content: str
    headings: list[str]
    description: str = ""


class SearchIndexer:
    """
    Search index generator for JinPress sites.

    Generates JSON search index containing page titles, content, and headings
    for client-side search functionality.
    """

    def __init__(self):
        """Initialize search indexer."""
        self.documents: list[SearchDocument] = []

    def add_document(self, file_info: dict[str, Any]) -> None:
        """
        Add a document to the search index.

        Args:
            file_info: Processed file information containing:
                - title: Page title
                - url_path: URL path for the page
                - description: Page description
                - html_content: HTML content of the page
                - headings (optional): List of heading texts
        """
        # Extract clean text content for indexing
        content = self._extract_text_content(file_info.get("html_content", ""))

        # Extract headings from HTML if not provided
        headings = file_info.get("headings", [])
        if not headings:
            headings = self._extract_headings(file_info.get("html_content", ""))

        # Create search document
        doc = SearchDocument(
            url=file_info.get("url_path", ""),
            title=file_info.get("title", ""),
            content=content,
            headings=headings,
            description=file_info.get("description", ""),
        )

        self.documents.append(doc)

    def add_page(
        self,
        url: str,
        title: str,
        content: str,
        headings: list[str] | None = None,
        description: str = "",
    ) -> None:
        """
        Add a page to the search index.

        Args:
            url: URL path for the page
            title: Page title
            content: Plain text content (or HTML to be extracted)
            headings: List of heading texts
            description: Page description
        """
        # Extract text if content looks like HTML
        if "<" in content and ">" in content:
            content = self._extract_text_content(content)

        doc = SearchDocument(
            url=url,
            title=title,
            content=content,
            headings=headings or [],
            description=description,
        )

        self.documents.append(doc)

    def _extract_text_content(self, html_content: str) -> str:
        """
        Extract plain text from HTML content for indexing.

        Args:
            html_content: HTML content

        Returns:
            Plain text content
        """
        if not html_content:
            return ""

        # Remove script and style elements
        text = re.sub(r"<script[^>]*>.*?</script>", " ", html_content, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&quot;", '"')

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _extract_headings(self, html_content: str) -> list[str]:
        """
        Extract heading texts from HTML content.

        Args:
            html_content: HTML content

        Returns:
            List of heading texts
        """
        if not html_content:
            return []

        headings = []

        # Match h1-h6 tags and extract text
        pattern = r"<h[1-6][^>]*>(.*?)</h[1-6]>"
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            # Remove any nested tags and clean up
            text = re.sub(r"<[^>]+>", "", match)
            text = text.strip()
            if text:
                headings.append(text)

        return headings

    def generate_index(self, output_path: Path) -> None:
        """
        Generate and save search index to file.

        Args:
            output_path: Path to save the search index JSON file
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert documents to JSON-serializable format
        index_data = []
        for doc in self.documents:
            index_data.append(
                {
                    "url": doc.url,
                    "title": doc.title,
                    "content": doc.content,
                    "headings": doc.headings,
                    "description": doc.description,
                }
            )

        # Write search index
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, separators=(",", ":"))

    def get_index_data(self) -> list[dict[str, Any]]:
        """
        Get the search index data as a list of dictionaries.

        Returns:
            List of document dictionaries
        """
        return [
            {
                "url": doc.url,
                "title": doc.title,
                "content": doc.content,
                "headings": doc.headings,
                "description": doc.description,
            }
            for doc in self.documents
        ]

    def clear(self) -> None:
        """Clear all documents from the index."""
        self.documents.clear()

    def get_document_count(self) -> int:
        """Get the number of documents in the index."""
        return len(self.documents)
