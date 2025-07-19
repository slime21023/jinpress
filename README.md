# JinPress

A fast, lightweight, and elegantly configured Python static site generator inspired by VitePress.

## Features

- **Python Native**: Built entirely in Python, no Node.js required
- **Zero Config**: Works out of the box with sensible defaults
- **Fast Builds**: Powered by minijinja and markdown-it-py
- **Live Reload**: Development server with instant updates
- **Syntax Highlighting**: Code blocks with Pygments
- **Built-in Search**: Client-side search functionality
- **Custom Containers**: Tip, warning, danger, and info boxes
- **Theme System**: Exclusive mode for complete customization

## Quick Start

### Installation

```bash
pip install jinpress
```

### Create a new project

```bash
jinpress init my-docs
cd my-docs
```

### Start development server

```bash
jinpress serve
```

Your site will be available at `http://localhost:8000` with live reload.

### Build for production

```bash
jinpress build
```

## CLI Commands

- `jinpress init [project-name]` - Create a new project
- `jinpress serve` - Start development server with live reload
- `jinpress build` - Build static site for production
- `jinpress info` - Show project information

## Project Structure

```
my-jinpress-project/
├── dist/                    # Built site output
├── docs/                    # Markdown source files
│   ├── index.md
│   ├── about.md
│   └── guide/
│       ├── index.md
│       ├── getting-started.md
│       ├── configuration.md
│       └── deployment.md
├── static/                  # Custom static files
├── templates/               # Custom template overrides (optional)
├── config.yml               # Site configuration
└── .gitignore
```

## Configuration

JinPress uses a single `config.yml` file for all configuration:

```yaml
site:
  title: "My Documentation"
  description: "A great documentation site"
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
```

## Markdown Features

JinPress supports enhanced markdown with:

- **Syntax highlighting** with Pygments
- **Custom containers** (tip, warning, danger, info)
- **Frontmatter** for page metadata
- **Table of contents** generation
- **Code block** enhancements

Example:

```markdown
:::tip
This is a tip container with custom styling.
:::

:::warning
This is a warning container.
:::
```

## Requirements

- Python 3.8+

## License

MIT License
