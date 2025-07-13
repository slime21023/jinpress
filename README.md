# JinPress

A fast, lightweight, and elegantly configured Python static site generator inspired by VitePress.

## Features

- **Python Native**: Built entirely in Python, no Node.js required
- **Configuration as Documentation**: Clear and intuitive `config.yml` structure
- **Performance First**: Fast builds with minijinja and markdown-it-py
- **Sensible Defaults**: Beautiful, functional default theme out of the box
- **Progressive Customization**: From simple CSS overrides to complete template replacement

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

### Build for production

```bash
jinpress build
```

## Project Structure

```
my-jinpress-project/
├── .jinpress/               # Cache and temporary files
├── dist/                    # Built site output
├── docs/                    # Markdown source files
│   ├── index.md
│   └── guide/
│       └── getting-started.md
├── static/                  # Custom static files
├── templates/               # Custom template overrides
└── config.yml               # Site configuration
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
  
  sidebar:
    "/guide/":
      - text: "Getting Started"
        link: "/guide/getting-started"
  
  socialLinks:
    - icon: "github"
      link: "https://github.com/user/repo"
```

## License

MIT License
