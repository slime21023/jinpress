#!/usr/bin/env python3
"""
Test script to verify markdown processing features.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from jinpress.renderer import Renderer

class TestMarkdownFeatures(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "source"
        self.source_dir.mkdir()
        self.renderer = Renderer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_code_block_syntax_highlighting(self):
        """Test code block with syntax highlighting."""
        with open(self.source_dir / "code_test.md", "w") as f:
            f.write("""# Code Test

```python
def hello_world():
    print("Hello, world!")
    return True
```

```javascript
function greet(name) {
    console.log(`Hello, ${name}!`);
}
```
""")
        
        html, metadata = self.renderer.render_markdown(self.source_dir / "code_test.md")
        self.assertIn('<div class="language-python">', html)
        self.assertIn('<div class="language-javascript">', html)

    def test_link_transformation(self):
        """Test link transformation for .md files."""
        with open(self.source_dir / "link_test.md", "w") as f:
            f.write("""# Link Test

[Internal Link](./other-page.md)
[Another Link](../parent/page.md)
[External Link](https://example.com)
""")
        
        html, metadata = self.renderer.render_markdown(self.source_dir / "link_test.md")
        self.assertIn('href="./other-page/"', html)
        self.assertIn('href="../parent/page/"', html)
        self.assertIn('href="https://example.com"', html)

    def test_custom_containers(self):
        """Test custom containers (tip, warning, danger, info)."""
        with open(self.source_dir / "container_test.md", "w") as f:
            f.write("""# Container Test

::: tip
This is a tip container.
:::

::: warning
This is a warning container.
:::

::: danger
This is a danger container.
:::

::: info
This is an info container.
:::
""")
        
        html, metadata = self.renderer.render_markdown(self.source_dir / "container_test.md")
        
        # Check for container classes or divs
        containers = ['tip', 'warning', 'danger', 'info']
        for container in containers:
            with self.subTest(container=container):
                # Check for various possible container formats
                container_found = (
                    f'class="{container}"' in html or 
                    f'<div class="container-{container}">' in html or
                    f'<div class="{container}">' in html
                )
                self.assertTrue(container_found, f"{container} container not found in HTML: {html}")

if __name__ == "__main__":
    unittest.main()