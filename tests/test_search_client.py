#!/usr/bin/env python3
"""
Test client-side search functionality.
"""

import unittest
import re
from pathlib import Path

class TestClientSideSearch(unittest.TestCase):
    
    def test_search_js_exists(self):
        """Test that search.js file exists."""
        search_js_path = Path("jinpress/theme/default/static/js/search.js")
        self.assertTrue(search_js_path.exists(), "search.js file should exist")
        
        # Check file has content
        with open(search_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertGreater(len(content), 1000, "search.js should have substantial content")

    def test_search_js_has_required_functions(self):
        """Test that search.js contains required functions and classes."""
        search_js_path = Path("jinpress/theme/default/static/js/search.js")
        
        with open(search_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key components
        required_elements = [
            'class SearchIndex',
            'loadSearchIndex',
            'performSearch',
            'displaySearchResults',
            'createSearchResultItem',
            'hideSearchResults',
            'initSearch',
            'search-no-results',
            'search-result-item',
            'ArrowDown',
            'ArrowUp',
            'Enter',
            'Escape'
        ]
        
        for element in required_elements:
            self.assertIn(element, content, f"search.js should contain '{element}'")

    def test_search_js_handles_no_results(self):
        """Test that search.js handles no results scenario."""
        search_js_path = Path("jinpress/theme/default/static/js/search.js")
        
        with open(search_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for no results handling
        self.assertIn('No results found', content)
        self.assertIn('search-no-results', content)

    def test_search_js_has_keyboard_navigation(self):
        """Test that search.js includes keyboard navigation."""
        search_js_path = Path("jinpress/theme/default/static/js/search.js")
        
        with open(search_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for keyboard event handling
        keyboard_events = ['ArrowDown', 'ArrowUp', 'Enter', 'Escape']
        for event in keyboard_events:
            self.assertIn(event, content, f"search.js should handle {event} key")

    def test_search_js_loads_index_from_json(self):
        """Test that search.js loads search index from JSON."""
        search_js_path = Path("jinpress/theme/default/static/js/search.js")
        
        with open(search_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for JSON loading functionality
        self.assertIn('fetch(', content)
        self.assertIn('search-index.json', content)
        self.assertIn('response.json()', content)

    def test_search_js_has_search_algorithm(self):
        """Test that search.js implements a search algorithm."""
        search_js_path = Path("jinpress/theme/default/static/js/search.js")
        
        with open(search_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for search algorithm components
        search_components = [
            'tokenize',
            'search(',
            'toLowerCase',
            'split(',
            'filter(',
            'score'
        ]
        
        for component in search_components:
            self.assertIn(component, content, f"search.js should contain search component '{component}'")

    def test_search_js_creates_result_items(self):
        """Test that search.js creates proper result items."""
        search_js_path = Path("jinpress/theme/default/static/js/search.js")
        
        with open(search_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for result item creation
        result_elements = [
            'search-result-item',
            'search-result-title',
            'search-result-excerpt',
            'search-result-url',
            'createElement',
            'appendChild'
        ]
        
        for element in result_elements:
            self.assertIn(element, content, f"search.js should contain result element '{element}'")

    def test_search_js_handles_click_navigation(self):
        """Test that search.js handles click navigation to results."""
        search_js_path = Path("jinpress/theme/default/static/js/search.js")
        
        with open(search_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for click handling
        self.assertIn('addEventListener(\'click\'', content)
        self.assertIn('window.location.href', content)

    def test_search_index_file_path(self):
        """Test that search expects index at correct path."""
        search_js_path = Path("jinpress/theme/default/static/js/search.js")
        
        with open(search_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should look for search index at root
        self.assertIn('/search-index.json', content)

if __name__ == "__main__":
    unittest.main()