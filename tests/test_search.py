#!/usr/bin/env python3
"""
Test search indexing functionality.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from jinpress.search import SearchIndexer
from jinpress.renderer import Renderer

class TestSearchIndexer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "source"
        self.source_dir.mkdir()
        self.output_dir = Path(self.test_dir) / "output"
        self.output_dir.mkdir()
        self.indexer = SearchIndexer()
        self.renderer = Renderer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_search_indexer_initialization(self):
        """Test that search indexer initializes correctly."""
        indexer = SearchIndexer()
        self.assertEqual(indexer.get_document_count(), 0)
        self.assertEqual(len(indexer.documents), 0)

    def test_add_document_to_index(self):
        """Test adding a document to the search index."""
        # Create a test markdown file
        test_file = self.source_dir / "test.md"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("""---
title: Test Document
description: This is a test document
---

# Test Document

This is the content of the test document. It contains some **bold text** and *italic text*.

## Section 2

More content here with a [link](https://example.com).
""")
        
        # Process the file with renderer
        html, metadata = self.renderer.render_markdown(test_file)
        
        # Create file info structure
        file_info = {
            "title": metadata.get("title", "Test Document"),
            "description": metadata.get("description", "This is a test document"),
            "url_path": "/test/",
            "html_content": html,
        }
        
        # Add to search index
        self.indexer.add_document(file_info)
        
        # Verify document was added
        self.assertEqual(self.indexer.get_document_count(), 1)
        
        # Check document structure
        doc = self.indexer.documents[0]
        self.assertEqual(doc["title"], "Test Document")
        self.assertEqual(doc["url"], "/test/")
        self.assertEqual(doc["description"], "This is a test document")
        self.assertIn("content", doc)
        
        # Check that HTML tags were stripped from content
        self.assertNotIn("<h1>", doc["content"])
        self.assertNotIn("<strong>", doc["content"])
        self.assertIn("Test Document", doc["content"])
        self.assertIn("bold text", doc["content"])

    def test_html_content_extraction(self):
        """Test that HTML content is properly extracted to plain text."""
        html_content = """
        <h1>Main Title</h1>
        <p>This is a paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
        </ul>
        <code>some code</code>
        """
        
        plain_text = self.indexer._extract_text_content(html_content)
        
        # Should not contain HTML tags
        self.assertNotIn("<h1>", plain_text)
        self.assertNotIn("<p>", plain_text)
        self.assertNotIn("<strong>", plain_text)
        self.assertNotIn("<em>", plain_text)
        self.assertNotIn("<ul>", plain_text)
        self.assertNotIn("<li>", plain_text)
        self.assertNotIn("<code>", plain_text)
        
        # Should contain the text content
        self.assertIn("Main Title", plain_text)
        self.assertIn("bold", plain_text)
        self.assertIn("italic", plain_text)
        self.assertIn("List item 1", plain_text)
        self.assertIn("some code", plain_text)

    def test_generate_search_index_file(self):
        """Test generating search index JSON file."""
        # Add some test documents
        test_docs = [
            {
                "title": "Document 1",
                "description": "First test document",
                "url_path": "/doc1/",
                "html_content": "<h1>Document 1</h1><p>Content of document 1</p>",
            },
            {
                "title": "Document 2", 
                "description": "Second test document",
                "url_path": "/doc2/",
                "html_content": "<h1>Document 2</h1><p>Content of document 2</p>",
            }
        ]
        
        for doc_info in test_docs:
            self.indexer.add_document(doc_info)
        
        # Generate index file
        index_path = self.output_dir / "search.json"
        self.indexer.generate_index(index_path)
        
        # Verify file was created
        self.assertTrue(index_path.exists())
        
        # Verify file content
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        self.assertEqual(len(index_data), 2)
        
        # Check first document
        doc1 = index_data[0]
        self.assertEqual(doc1["title"], "Document 1")
        self.assertEqual(doc1["url"], "/doc1/")
        self.assertEqual(doc1["description"], "First test document")
        self.assertIn("Document 1", doc1["content"])
        self.assertIn("Content of document 1", doc1["content"])
        
        # Check second document
        doc2 = index_data[1]
        self.assertEqual(doc2["title"], "Document 2")
        self.assertEqual(doc2["url"], "/doc2/")
        self.assertEqual(doc2["description"], "Second test document")

    def test_search_index_json_format(self):
        """Test that search index JSON is properly formatted."""
        # Add a document with special characters
        file_info = {
            "title": "Special Characters: éñ中文",
            "description": "Document with unicode characters",
            "url_path": "/special/",
            "html_content": "<p>Content with special chars: éñ中文 & symbols!</p>",
        }
        
        self.indexer.add_document(file_info)
        
        # Generate index
        index_path = self.output_dir / "search.json"
        self.indexer.generate_index(index_path)
        
        # Read and verify JSON
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            index_data = json.loads(content)
        
        # Should preserve unicode characters
        doc = index_data[0]
        self.assertEqual(doc["title"], "Special Characters: éñ中文")
        self.assertIn("éñ中文", doc["content"])
        
        # JSON should be compact (no newlines between records)
        self.assertNotIn("\n", content)
        # Note: Content may have spaces from HTML tag removal, which is expected

    def test_clear_search_index(self):
        """Test clearing the search index."""
        # Add some documents
        file_info = {
            "title": "Test Document",
            "description": "Test",
            "url_path": "/test/",
            "html_content": "<p>Test content</p>",
        }
        
        self.indexer.add_document(file_info)
        self.assertEqual(self.indexer.get_document_count(), 1)
        
        # Clear index
        self.indexer.clear()
        self.assertEqual(self.indexer.get_document_count(), 0)
        self.assertEqual(len(self.indexer.documents), 0)

    def test_multiple_documents_indexing(self):
        """Test indexing multiple documents with different content types."""
        # Create multiple test files
        files_data = [
            ("home.md", "# Home\nWelcome to the home page."),
            ("about.md", "# About\nThis is the about page with some information."),
            ("contact.md", "# Contact\nGet in touch with us at contact@example.com"),
        ]
        
        for filename, content in files_data:
            test_file = self.source_dir / filename
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Process and add to index
            html, metadata = self.renderer.render_markdown(test_file)
            file_info = {
                "title": filename.replace(".md", "").title(),
                "description": f"Description for {filename}",
                "url_path": f"/{filename.replace('.md', '')}/",
                "html_content": html,
            }
            self.indexer.add_document(file_info)
        
        # Verify all documents were indexed
        self.assertEqual(self.indexer.get_document_count(), 3)
        
        # Generate and verify index
        index_path = self.output_dir / "search.json"
        self.indexer.generate_index(index_path)
        
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        self.assertEqual(len(index_data), 3)
        
        # Check that each document has the expected structure
        for doc in index_data:
            self.assertIn("title", doc)
            self.assertIn("url", doc)
            self.assertIn("content", doc)
            self.assertIn("description", doc)
            self.assertTrue(len(doc["content"]) > 0)

    def test_search_index_directory_creation(self):
        """Test that search index creates necessary directories."""
        # Try to create index in nested directory that doesn't exist
        nested_path = self.output_dir / "assets" / "js" / "search.json"
        
        # Add a document
        file_info = {
            "title": "Test",
            "description": "Test",
            "url_path": "/test/",
            "html_content": "<p>Test</p>",
        }
        self.indexer.add_document(file_info)
        
        # Generate index (should create directories)
        self.indexer.generate_index(nested_path)
        
        # Verify file and directories were created
        self.assertTrue(nested_path.exists())
        self.assertTrue(nested_path.parent.exists())
        
        # Verify content
        with open(nested_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        self.assertEqual(len(index_data), 1)

if __name__ == "__main__":
    unittest.main()