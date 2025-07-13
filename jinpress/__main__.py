"""
Entry point for running JinPress as a module.

This allows users to run JinPress using:
    python -m jinpress
"""

from .cli import cli

if __name__ == "__main__":
    cli()
