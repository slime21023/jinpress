"""
Project scaffolding for JinPress.

Creates new JinPress projects with sample content and configuration.
"""

from pathlib import Path


class ScaffoldError(Exception):
    """Raised when there's an error during scaffolding."""

    pass


class ScaffoldTemplates:
    """Static templates and content for scaffolding."""

    @staticmethod
    def get_config_template(project_name: str) -> str:
        """Get configuration file template (jinpress.yml format)."""
        title = project_name.replace("-", " ").replace("_", " ").title()
        return f'''# JinPress Configuration
# See https://jinpress.dev/guide/configuration/ for more options

site:
  title: "{title}"
  description: "A JinPress documentation site"
  lang: "zh-TW"
  base: "/"

theme:
  nav:
    - text: "首頁"
      link: "/"
    - text: "指南"
      link: "/guide/"
    - text: "關於"
      link: "/about/"
  
  sidebar:
    "/guide/":
      - text: "快速開始"
        link: "/guide/getting-started/"
      - text: "配置"
        link: "/guide/configuration/"
      - text: "部署"
        link: "/guide/deployment/"
    "/":
      - text: "首頁"
        link: "/"
      - text: "關於"
        link: "/about/"
  
  footer:
    message: "Built with JinPress"
    copyright: "Copyright © 2025"
  
  edit_link:
    pattern: "https://github.com/user/repo/edit/main/docs/:path"
    text: "編輯此頁"
  
  last_updated: true
'''

    @staticmethod
    def get_github_actions_template(project_name: str) -> str:
        """Get GitHub Actions workflow template for deploying to GitHub Pages."""
        return """# GitHub Actions workflow for deploying JinPress site to GitHub Pages
name: Deploy JinPress Site

on:
  # Runs on pushes targeting the default branch
  push:
    branches: ["main"]
  
  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

# Sets permissions of the GITHUB_TOKEN to allow deployment to GitHub Pages
permissions:
  contents: read
  pages: write
  id-token: write

# Allow only one concurrent deployment, skipping runs queued between the run in-progress and latest queued.
# However, do NOT cancel in-progress runs as we want to allow these production deployments to complete.
concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  # Build job
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install jinpress
      
      - name: Build site
        run: jinpress build
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

  # Deployment job
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""

    @staticmethod
    def get_gitignore_template() -> str:
        """Get .gitignore file template."""
        return """# JinPress
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

    @staticmethod
    def get_content_templates() -> dict[str, str]:
        """Get all markdown content templates."""
        return {
            "index.md": """---
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
""",
            "guide/index.md": """---
title: "Guide"
description: "JinPress documentation guide"
---

# Guide

Welcome to the JinPress guide! Here you'll find comprehensive documentation to help you get the most out of JinPress.

## Getting Started

New to JinPress? Start with our [Getting Started](/guide/getting-started/) guide to learn the basics.

## Configuration

Learn how to configure your JinPress site in the [Configuration](/guide/configuration/) section.

## Deployment

Ready to deploy your site? Check out our [Deployment](/guide/deployment/) guide for various hosting options.

## Quick Navigation

- [Getting Started](/guide/getting-started/) - Learn the basics
- [Configuration](/guide/configuration/) - Customize your site
- [Deployment](/guide/deployment/) - Deploy your site

---

Choose a topic from the sidebar to dive deeper into JinPress documentation.
""",
            "guide/getting-started.md": """---
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
""",
            "guide/configuration.md": """---
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
""",
            "guide/deployment.md": """---
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
""",
            "about.md": """---
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
""",
        }


class Scaffold:
    """Project scaffolding for JinPress."""

    def __init__(self):
        """Initialize scaffolder."""
        pass

    def create_project(self, project_name: str, target_dir: Path | None = None) -> Path:
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

        # Create GitHub Actions workflow
        self._create_github_actions_workflow(project_dir, project_name)

        return project_dir

    def _create_directory_structure(self, project_dir: Path) -> None:
        """Create the basic directory structure."""
        directories = [
            project_dir,
            project_dir / "docs",
            project_dir / "docs" / "guide",
            project_dir / "static",
            project_dir / ".jinpress",
            project_dir / ".jinpress" / "cache",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _create_config_file(self, project_dir: Path, project_name: str) -> None:
        """Create the configuration file (jinpress.yml)."""
        config_content = ScaffoldTemplates.get_config_template(project_name)
        config_path = project_dir / "jinpress.yml"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)

    def _create_sample_content(self, project_dir: Path) -> None:
        """Create sample markdown content."""
        content_templates = ScaffoldTemplates.get_content_templates()

        for file_path, content in content_templates.items():
            full_path = project_dir / "docs" / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    def _create_gitignore(self, project_dir: Path) -> None:
        """Create .gitignore file."""
        gitignore_content = ScaffoldTemplates.get_gitignore_template()
        gitignore_path = project_dir / ".gitignore"
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(gitignore_content)

    def _create_github_actions_workflow(
        self, project_dir: Path, project_name: str
    ) -> None:
        """Create GitHub Actions workflow for deploying to GitHub Pages."""
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        workflow_content = ScaffoldTemplates.get_github_actions_template(project_name)
        workflow_path = workflows_dir / "deploy.yml"
        with open(workflow_path, "w", encoding="utf-8") as f:
            f.write(workflow_content)
