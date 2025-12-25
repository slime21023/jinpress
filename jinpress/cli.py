"""
Command-line interface for JinPress.

Provides the main entry point for the jinpress command.
Implements Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6.
"""

import sys
from pathlib import Path

import click

from . import __version__
from .builder import BuildError
from .config import ConfigError
from .logging_config import setup_logging
from .scaffold import Scaffold, ScaffoldError
from .server import serve_site

HELP_TEXT = """
JinPress - A fast, lightweight Python static site generator.

JinPress is inspired by VitePress and provides a Python-native solution
for building beautiful documentation sites with minimal configuration.

\b
Quick Start:
  jinpress init my-docs    Create a new project
  cd my-docs
  jinpress serve           Start development server
  jinpress build           Build for production

\b
Examples:
  jinpress init my-project --dir /path/to/dir
  jinpress serve --port 8080
  jinpress build --no-clean

For more information, visit: https://jinpress.dev
"""


@click.group(help=HELP_TEXT)
@click.version_option(
    version=__version__, prog_name="jinpress", message="%(prog)s version %(version)s"
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose logging for debugging"
)
@click.pass_context
def cli(ctx, verbose):
    """JinPress - A fast, lightweight Python static site generator."""
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)

    # Store verbose flag in context
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("project_name", required=False)
@click.option(
    "--dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Target directory (defaults to current directory)",
)
def init(project_name: str | None, dir: Path | None):
    """Initialize a new JinPress project.

    Creates a new project with default configuration and sample content.
    The project will include:
    - jinpress.yml configuration file
    - Sample documentation in docs/
    - Basic project structure
    """
    if not project_name:
        project_name = click.prompt("Project name")

    target_dir = dir or Path.cwd()

    try:
        scaffold = Scaffold()
        project_dir = scaffold.create_project(project_name, target_dir)

        click.echo(f"✅ Created JinPress project: {project_dir}")
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  cd {project_name}")
        click.echo("  jinpress serve")
        click.echo()
        click.echo("Happy documenting! 📚")

    except ScaffoldError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--clean/--no-clean", default=True, help="Clean output directory before building"
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to config file (defaults to jinpress.yml)",
)
def build(clean: bool, config: Path | None):
    """Build the static site.

    Builds the documentation site and outputs to the dist/ directory.
    All Markdown files in docs/ will be converted to HTML.
    """
    project_root = Path.cwd()

    try:
        # Load configuration (jinpress.yml or config.yml)
        if config:
            config_path = config
        else:
            config_path = project_root / "jinpress.yml"
            if not config_path.exists():
                config_path = project_root / "config.yml"

        if not config_path.exists():
            click.echo(
                "❌ Error: No configuration file found (jinpress.yml or config.yml)",
                err=True,
            )
            click.echo(
                "Run 'jinpress init <project-name>' to create a new project", err=True
            )
            sys.exit(1)

        # Use new ConfigManager and BuildEngine
        from .builder import BuildEngine
        from .config import ConfigManager

        config_manager = ConfigManager()
        jinpress_config = config_manager.load(project_root)

        # Validate configuration
        errors = config_manager.validate(jinpress_config)
        if errors:
            click.echo("❌ Configuration validation errors:", err=True)
            for error in errors:
                click.echo(f"   - {error}", err=True)
            sys.exit(1)

        # Build site
        engine = BuildEngine(project_root, jinpress_config)
        result = engine.build(clean=clean)

        if result.success:
            click.echo("✅ Site built successfully!")
            click.echo(f"   Pages: {result.pages_built}")
            click.echo(f"   Output: {engine.output_dir}")
            click.echo(f"   Duration: {result.duration_ms:.0f}ms")

            if result.warnings:
                click.echo()
                click.echo("⚠️  Warnings:")
                for warning in result.warnings:
                    click.echo(f"   - {warning}", err=True)
        else:
            click.echo("❌ Build failed with errors:", err=True)
            for error in result.errors:
                click.echo(f"   - {error}", err=True)
            sys.exit(1)

    except ConfigError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        sys.exit(1)
    except BuildError as e:
        click.echo(f"❌ Build error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--host", "-h", default="localhost", help="Server host (default: localhost)"
)
@click.option(
    "--port", "-p", default=3000, type=int, help="Server port (default: 3000)"
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to config file (defaults to jinpress.yml)",
)
@click.option(
    "--no-open", is_flag=True, default=False, help="Don't open browser automatically"
)
def serve(host: str, port: int, config: Path | None, no_open: bool):
    """Start development server with live reload.

    Starts a local development server with hot reload support.
    The server will automatically rebuild when files change.
    """
    project_root = Path.cwd()

    # Check if config exists (jinpress.yml or config.yml)
    if config:
        config_path = config
    else:
        config_path = project_root / "jinpress.yml"
        if not config_path.exists():
            config_path = project_root / "config.yml"

    if not config_path.exists():
        click.echo(
            "❌ Error: No configuration file found (jinpress.yml or config.yml)",
            err=True,
        )
        click.echo(
            "Run 'jinpress init <project-name>' to create a new project", err=True
        )
        sys.exit(1)

    try:
        serve_site(project_root, host, port, open_browser=not no_open)
    except KeyboardInterrupt:
        click.echo("\n👋 Server stopped")
    except Exception as e:
        click.echo(f"❌ Server error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to config file (defaults to jinpress.yml)",
)
def info(config: Path | None):
    """Show project information.

    Displays information about the current JinPress project including
    configuration, directories, and build status.
    """
    project_root = Path.cwd()

    # Check if config exists (jinpress.yml or config.yml)
    if config:
        config_path = config
    else:
        config_path = project_root / "jinpress.yml"
        if not config_path.exists():
            config_path = project_root / "config.yml"

    if not config_path.exists():
        click.echo(
            "❌ Error: No configuration file found (jinpress.yml or config.yml)",
            err=True,
        )
        click.echo("This doesn't appear to be a JinPress project", err=True)
        sys.exit(1)

    try:
        from .builder import BuildEngine
        from .config import ConfigManager

        config_manager = ConfigManager()
        jinpress_config = config_manager.load(project_root)
        engine = BuildEngine(project_root, jinpress_config)

        click.echo("📋 JinPress Project Information")
        click.echo("=" * 40)
        click.echo(f"Project Root: {project_root}")
        click.echo(f"Config File:  {config_path}")
        click.echo(f"Docs Dir:     {engine.docs_dir}")
        click.echo(f"Output Dir:   {engine.output_dir}")
        click.echo()
        click.echo(f"Site Title:   {jinpress_config.site.title}")
        click.echo(f"Site Base:    {jinpress_config.site.base}")
        click.echo(f"Language:     {jinpress_config.site.lang}")

        # Check if docs directory exists
        if engine.docs_dir.exists():
            md_files = list(engine.docs_dir.rglob("*.md"))
            click.echo(f"Markdown Files: {len(md_files)}")
        else:
            click.echo("Markdown Files: 0 (docs directory not found)")

        # Check if output directory exists
        if engine.output_dir.exists():
            html_files = list(engine.output_dir.rglob("*.html"))
            click.echo(f"Built Pages: {len(html_files)}")
        else:
            click.echo("Built Pages: 0 (run 'jinpress build' first)")

    except ConfigError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the jinpress CLI."""
    cli()


if __name__ == "__main__":
    cli()
