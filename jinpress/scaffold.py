"""
Project scaffolding for JinPress.

Creates new JinPress projects with sample content and configuration.
"""

from pathlib import Path
from typing import Optional


class ScaffoldError(Exception):
    """Raised when there's an error during scaffolding."""
    pass


class Scaffold:
    """Project scaffolding for JinPress."""
    
    def __init__(self):
        """Initialize scaffolder."""
        pass
    
    def create_project(self, project_name: str, target_dir: Optional[Path] = None) -> Path:
        """
        Create a new JinPress project.
        
        Args:
            project_name: Name of the project
            target_dir: Target directory (defaults to current directory)
            
        Returns:
            Path to the created project directory
        """
        if target_dir is None:
            target_dir = Path.cwd()
        
        project_dir = target_dir / project_name
        
        # Check if directory already exists
        if project_dir.exists():
            raise ScaffoldError(f"Directory already exists: {project_dir}")
        
        # Create project structure
        self._create_directory_structure(project_dir)
        
        # Create configuration file
        self._create_config_file(project_dir, project_name)
        
        # Create sample content
        self._create_sample_content(project_dir)
        
        # Create gitignore
        self._create_gitignore(project_dir)
        
        return project_dir
    
    def _create_directory_structure(self, project_dir: Path) -> None:
        """Create the basic directory structure."""
        directories = [
            project_dir,
            project_dir / "docs",
            project_dir / "docs" / "guide",
            project_dir / "static",
            project_dir / "templates",
            project_dir / ".jinpress",
            project_dir / ".jinpress" / "cache",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _create_config_file(self, project_dir: Path, project_name: str) -> None:
        """Create the configuration file."""
        config_content = f"""site:
  title: "{project_name.replace('-', ' ').replace('_', ' ').title()}"
  description: "A JinPress documentation site"
  lang: "en-US"
  base: "/"

themeConfig:
  nav:
    - text: "Home"
      link: "/"
    - text: "Guide"
      link: "/guide/"
    - text: "About"
      link: "/about/"
  
  sidebar:
    "/guide/":
      - text: "Getting Started"
        link: "/guide/getting-started/"
      - text: "Configuration"
        link: "/guide/configuration/"
      - text: "Deployment"
        link: "/guide/deployment/"
  
  socialLinks:
    - icon: "github"
      link: "https://github.com/user/repo"
  
  editLink:
    pattern: "https://github.com/user/repo/edit/main/docs/:path"
    text: "Edit this page"
  
  footer:
    message: "Built with JinPress"
    copyright: "Copyright © 2025"
  
  lastUpdated: true
"""
        
        config_path = project_dir / "config.yml"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
    
    def _create_sample_content(self, project_dir: Path) -> None:
        """Create sample markdown content."""
        
        # Create index.md
        index_content = f"""---
title: "Welcome to JinPress"
description: "A fast, lightweight, and elegantly configured Python static site generator"
---

# Welcome to JinPress

JinPress is a fast, lightweight, and elegantly configured Python static site generator inspired by VitePress.

## Features

- **Python Native**: Built entirely in Python, no Node.js required
- **Configuration as Documentation**: Clear and intuitive `config.yml` structure  
- **Performance First**: Fast builds with minijinja and markdown-it-py
- **Sensible Defaults**: Beautiful, functional default theme out of the box
- **Progressive Customization**: From simple CSS overrides to complete template replacement

## Quick Start

Get started by exploring the [guide](/guide/getting-started/).

## Example Code

```python
from jinpress import Builder

# Build your site
builder = Builder(".")
builder.build()
```

:::tip
This is a tip container. You can use different types like `warning`, `danger`, and `info`.
:::

## What's Next?

- Read the [Getting Started Guide](/guide/getting-started/)
- Learn about [Configuration](/guide/configuration/)
- Explore [Deployment Options](/guide/deployment/)
"""
        
        index_path = project_dir / "docs" / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        # Create getting-started.md
        getting_started_content = """---
title: "Getting Started"
description: "Learn how to get started with JinPress"
---

# Getting Started

This guide will help you get started with JinPress.

## Installation

Install JinPress using pip:

```bash
pip install jinpress
```

## Create a New Project

Create a new JinPress project:

```bash
jinpress init my-docs
cd my-docs
```

## Project Structure

Your new project will have the following structure:

```
my-docs/
├── .jinpress/           # Cache and temporary files
├── docs/                # Markdown source files
│   ├── index.md
│   └── guide/
│       └── getting-started.md
├── static/              # Custom static files
├── templates/           # Custom template overrides
└── config.yml           # Site configuration
```

## Development Server

Start the development server:

```bash
jinpress serve
```

Your site will be available at `http://localhost:8000`.

## Building for Production

Build your site for production:

```bash
jinpress build
```

The built site will be in the `dist/` directory.

## Next Steps

- Learn about [Configuration](/guide/configuration/)
- Explore [Deployment Options](/guide/deployment/)
"""
        
        getting_started_path = project_dir / "docs" / "guide" / "getting-started.md"
        with open(getting_started_path, 'w', encoding='utf-8') as f:
            f.write(getting_started_content)
        
        # Create configuration.md
        config_content = """---
title: "Configuration"
description: "Learn how to configure your JinPress site"
---

# Configuration

JinPress uses a single `config.yml` file for all configuration.

## Site Configuration

```yaml
site:
  title: "My Site"
  description: "My awesome documentation site"
  lang: "en-US"
  base: "/"
```

## Theme Configuration

### Navigation

```yaml
themeConfig:
  nav:
    - text: "Home"
      link: "/"
    - text: "Guide"
      link: "/guide/"
```

### Sidebar

```yaml
themeConfig:
  sidebar:
    "/guide/":
      - text: "Getting Started"
        link: "/guide/getting-started/"
      - text: "Configuration"
        link: "/guide/configuration/"
```

### Social Links

```yaml
themeConfig:
  socialLinks:
    - icon: "github"
      link: "https://github.com/user/repo"
    - icon: "twitter"
      link: "https://twitter.com/user"
```

## Advanced Configuration

### Edit Links

```yaml
themeConfig:
  editLink:
    pattern: "https://github.com/user/repo/edit/main/docs/:path"
    text: "Edit this page"
```

### Footer

```yaml
themeConfig:
  footer:
    message: "Built with JinPress"
    copyright: "Copyright © 2025"
```
"""
        
        config_path = project_dir / "docs" / "guide" / "configuration.md"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # Create deployment.md
        deployment_content = """---
title: "Deployment"
description: "Learn how to deploy your JinPress site"
---

# Deployment

JinPress generates static HTML files that can be deployed to any static hosting service.

## GitHub Pages

1. Build your site:
   ```bash
   jinpress build
   ```

2. Push the `dist/` directory to your repository's `gh-pages` branch.

3. Enable GitHub Pages in your repository settings.

## Netlify

1. Connect your repository to Netlify.

2. Set the build command to:
   ```bash
   pip install jinpress && jinpress build
   ```

3. Set the publish directory to `dist/`.

## Vercel

1. Connect your repository to Vercel.

2. Set the build command to:
   ```bash
   pip install jinpress && jinpress build
   ```

3. Set the output directory to `dist/`.

## Custom Server

Upload the contents of the `dist/` directory to your web server.

Make sure to configure your server to serve `index.html` files for directory requests.
"""
        
        deployment_path = project_dir / "docs" / "guide" / "deployment.md"
        with open(deployment_path, 'w', encoding='utf-8') as f:
            f.write(deployment_content)
        
        # Create about.md
        about_content = """---
title: "About"
description: "About this JinPress site"
---

# About

This is a sample JinPress documentation site.

## What is JinPress?

JinPress is a fast, lightweight, and elegantly configured Python static site generator inspired by VitePress.

## Features

- Python-native implementation
- Beautiful default theme
- Fast builds
- Built-in search
- Mobile responsive
- Easy customization

## Getting Help

- Check the [documentation](/guide/)
- Visit the [GitHub repository](https://github.com/jinpress/jinpress)
- Join our community discussions
"""
        
        about_path = project_dir / "docs" / "about.md"
        with open(about_path, 'w', encoding='utf-8') as f:
            f.write(about_content)
    
    def _create_gitignore(self, project_dir: Path) -> None:
        """Create .gitignore file."""
        gitignore_content = """# JinPress
dist/
.jinpress/cache/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
        
        gitignore_path = project_dir / ".gitignore"
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
