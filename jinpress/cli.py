"""
Command-line interface for JinPress.

Provides the main entry point for the jinpress command.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from .builder import Builder, BuildError
from .config import Config, ConfigError
from .scaffold import Scaffold, ScaffoldError
from .server import serve_site


@click.group()
@click.version_option(version="1.0.0", prog_name="jinpress")
def cli():
    """JinPress - A fast, lightweight Python static site generator."""
    pass


@cli.command()
@click.argument("project_name", required=False)
@click.option(
    "--dir", "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Target directory (defaults to current directory)"
)
def init(project_name: Optional[str], dir: Optional[Path]):
    """Initialize a new JinPress project."""
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
    "--clean/--no-clean",
    default=True,
    help="Clean output directory before building"
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to config file (defaults to config.yml)"
)
def build(clean: bool, config: Optional[Path]):
    """Build the static site."""
    project_root = Path.cwd()
    
    try:
        # Load configuration
        config_path = config or project_root / "config.yml"
        if not config_path.exists():
            click.echo("❌ Error: config.yml not found", err=True)
            click.echo("Run 'jinpress init' to create a new project", err=True)
            sys.exit(1)
        
        site_config = Config(config_path)
        
        # Build site
        builder = Builder(project_root, site_config)
        builder.build(clean=clean)
        
        # Show build info
        build_info = builder.get_build_info()
        click.echo(f"✅ Site built successfully!")
        click.echo(f"   Output: {build_info['output_dir']}")
        click.echo(f"   Title: {build_info['site_title']}")
        
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
    "--host", "-h",
    default="localhost",
    help="Server host (default: localhost)"
)
@click.option(
    "--port", "-p",
    default=8000,
    type=int,
    help="Server port (default: 8000)"
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to config file (defaults to config.yml)"
)
def serve(host: str, port: int, config: Optional[Path]):
    """Start development server with live reload."""
    project_root = Path.cwd()
    
    # Check if config exists
    config_path = config or project_root / "config.yml"
    if not config_path.exists():
        click.echo("❌ Error: config.yml not found", err=True)
        click.echo("Run 'jinpress init' to create a new project", err=True)
        sys.exit(1)
    
    try:
        serve_site(project_root, host, port)
    except KeyboardInterrupt:
        click.echo("\n👋 Server stopped")
    except Exception as e:
        click.echo(f"❌ Server error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to config file (defaults to config.yml)"
)
def info(config: Optional[Path]):
    """Show project information."""
    project_root = Path.cwd()
    
    # Check if config exists
    config_path = config or project_root / "config.yml"
    if not config_path.exists():
        click.echo("❌ Error: config.yml not found", err=True)
        click.echo("This doesn't appear to be a JinPress project", err=True)
        sys.exit(1)
    
    try:
        site_config = Config(config_path)
        builder = Builder(project_root, site_config)
        build_info = builder.get_build_info()
        
        click.echo("📋 JinPress Project Information")
        click.echo("=" * 40)
        click.echo(f"Project Root: {build_info['project_root']}")
        click.echo(f"Config File:  {build_info['config_file']}")
        click.echo(f"Docs Dir:     {build_info['docs_dir']}")
        click.echo(f"Output Dir:   {build_info['output_dir']}")
        click.echo()
        click.echo(f"Site Title:   {build_info['site_title']}")
        click.echo(f"Site Base:    {build_info['site_base']}")
        
        # Check if docs directory exists
        docs_dir = Path(build_info['docs_dir'])
        if docs_dir.exists():
            md_files = list(docs_dir.rglob("*.md"))
            click.echo(f"Markdown Files: {len(md_files)}")
        else:
            click.echo("Markdown Files: 0 (docs directory not found)")
        
        # Check if output directory exists
        output_dir = Path(build_info['output_dir'])
        if output_dir.exists():
            html_files = list(output_dir.rglob("*.html"))
            click.echo(f"Built Pages: {len(html_files)}")
        else:
            click.echo("Built Pages: 0 (run 'jinpress build' first)")
        
    except ConfigError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
