"""
JinPress template engine module.

Provides Layout-first template architecture using minijinja.
"""

from .engine import TemplateEngine, TemplateError

__all__ = ["TemplateEngine", "TemplateError"]
