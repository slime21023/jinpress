"""
JinPress - A fast, lightweight, and elegantly configured Python static site generator.

Inspired by VitePress, JinPress provides a Python-native solution for building
beautiful documentation sites with minimal configuration.
"""

__version__ = "0.9.0"
__author__ = "KevinChueh"
__email__ = "slime21023@gmail.com"
__license__ = "MIT"

from .builder import Builder
from .config import Config
from .renderer import Renderer
from .scaffold import Scaffold
from .search import SearchIndexer
from .server import DevServer, serve_site
from .theme.engine import ThemeEngine

__all__ = [
    "Builder",
    "Config",
    "Renderer",
    "Scaffold",
    "SearchIndexer",
    "DevServer",
    "serve_site",
    "ThemeEngine",
    "__version__",
]
