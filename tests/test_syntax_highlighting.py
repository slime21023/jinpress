#!/usr/bin/env python3
"""
Test syntax highlighting CSS and functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from jinpress.renderer import Renderer

class TestSyntaxHighlighting(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "source"
        self.source_dir.mkdir()
        self.renderer = Renderer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_highlight_css_exists(self):
        """Test that highlight.css file exists in theme."""
        css_path = Path("jinpress/theme/default/static/css/highlight.css")
        self.assertTrue(css_path.exists(), "highlight.css file should exist")
        
        # Check that the file has content
        with open(css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertGreater(len(content), 100, "CSS file should have substantial content")
        self.assertIn('.highlight', content, "CSS should contain highlight classes")
        self.assertIn('color:', content, "CSS should contain color definitions")

    def test_python_syntax_highlighting(self):
        """Test Python code syntax highlighting."""
        with open(self.source_dir / "python_test.md", "w") as f:
            f.write("""# Python Test

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
print(fibonacci(10))
```
""")
        
        html, metadata = self.renderer.render_markdown(self.source_dir / "python_test.md")
        
        # Check for syntax highlighting elements
        self.assertIn('<div class="language-python">', html)
        self.assertIn('class="highlight"', html)
        
        # Check for Python-specific highlighting
        self.assertIn('def', html)  # Should be highlighted as keyword
        self.assertIn('return', html)  # Should be highlighted as keyword

    def test_javascript_syntax_highlighting(self):
        """Test JavaScript code syntax highlighting."""
        with open(self.source_dir / "js_test.md", "w") as f:
            f.write("""# JavaScript Test

```javascript
function calculateSum(a, b) {
    const result = a + b;
    console.log(`Sum: ${result}`);
    return result;
}

// Call the function
calculateSum(5, 3);
```
""")
        
        html, metadata = self.renderer.render_markdown(self.source_dir / "js_test.md")
        
        # Check for syntax highlighting elements
        self.assertIn('<div class="language-javascript">', html)
        self.assertIn('class="highlight"', html)
        
        # Check for JavaScript-specific content
        self.assertIn('function', html)
        self.assertIn('const', html)

    def test_multiple_language_highlighting(self):
        """Test multiple programming languages in one document."""
        with open(self.source_dir / "multi_lang_test.md", "w") as f:
            f.write("""# Multi-Language Test

Python:
```python
print("Hello from Python!")
```

JavaScript:
```javascript
console.log("Hello from JavaScript!");
```

HTML:
```html
<h1>Hello from HTML!</h1>
```

CSS:
```css
.hello {
    color: blue;
}
```
""")
        
        html, metadata = self.renderer.render_markdown(self.source_dir / "multi_lang_test.md")
        
        # Check that all languages are properly highlighted
        languages = ['python', 'javascript', 'html', 'css']
        for lang in languages:
            with self.subTest(language=lang):
                self.assertIn(f'<div class="language-{lang}">', html)

if __name__ == "__main__":
    unittest.main()