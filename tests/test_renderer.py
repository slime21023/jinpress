import unittest
import tempfile
import shutil
from pathlib import Path
from jinpress.renderer import Renderer, RendererError

class TestRenderer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "source"
        self.source_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_render_markdown(self):
        renderer = Renderer(self.source_dir)
        with open(self.source_dir / "test.md", "w") as f:
            f.write("# Hello")
        html, metadata = renderer.render_markdown(self.source_dir / "test.md")
        self.assertEqual(html.strip(), "<h1>Hello</h1>")

    def test_render_markdown_with_front_matter(self):
        renderer = Renderer(self.source_dir)
        with open(self.source_dir / "test.md", "w") as f:
            f.write("---\ntitle: Test Title\n---\n# Hello")
        html, metadata = renderer.render_markdown(self.source_dir / "test.md")
        self.assertEqual(html.strip(), "<h1>Hello</h1>")
        self.assertEqual(metadata.get("title"), "Test Title")

    def test_render_markdown_with_links(self):
        renderer = Renderer(self.source_dir)
        with open(self.source_dir / "test.md", "w") as f:
            f.write("[Link](./test.md)")
        html, metadata = renderer.render_markdown(self.source_dir / "test.md")
        self.assertIn('<a href="./test/">Link</a>', html.strip())

    def test_render_code_block(self):
        renderer = Renderer(self.source_dir)
        with open(self.source_dir / "test.md", "w") as f:
            f.write("```python\nprint('Hello, world!')\n```")
        html, metadata = renderer.render_markdown(self.source_dir / "test.md")
        self.assertIn('<div class="language-python">', html.strip())

    def test_render_invalid_markdown(self):
        renderer = Renderer(self.source_dir)
        # Test with non-existent file
        with self.assertRaises(RendererError):
            renderer.render_markdown(self.source_dir / "nonexistent.md")

if __name__ == '__main__':
    unittest.main()