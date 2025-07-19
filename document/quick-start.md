# Quick Start

Get started with JinPress in minutes.

## Installation

```bash
pip install jinpress
```

## Create a New Project

```bash
jinpress init my-docs
cd my-docs
```

This creates the following structure:

```
my-docs/
├── docs/                # Markdown source files
│   ├── index.md
│   ├── about.md
│   └── guide/
├── static/              # Custom static files
├── config.yml           # Site configuration
└── .gitignore
```

## Development Server

Start the development server with live reload:

```bash
jinpress serve
```

Your site will be available at `http://localhost:8000`.

## Build for Production

Generate static files for deployment:

```bash
jinpress build
```

Built files are output to the `dist/` directory.

## Writing Content

### Basic Markdown

Create `.md` files in the `docs/` directory:

```markdown
---
title: "My Page"
description: "Page description"
---

# My Page

Content goes here.

## Code Blocks

```python
def hello():
    print("Hello, World!")
```

## Custom Containers

:::tip
This is a tip container.
:::

:::warning
This is a warning.
:::
```

### Front Matter

Each Markdown file can include YAML front matter:

```yaml
---
title: "Page Title"
description: "Page description for SEO"
date: "2025-01-19"
---
```

## Configuration

Edit `config.yml` to configure your site:

```yaml
site:
  title: "My Documentation"
  description: "Built with JinPress"
  lang: "en-US"
  base: "/"

themeConfig:
  nav:
    - text: "Home"
      link: "/"
    - text: "Guide"
      link: "/guide/"
```

## Next Steps

- Read the [Configuration Guide](./configuration.md) for detailed options
- Check [Markdown Features](./markdown-features.md) for supported syntax
- Learn [Theme Customization](./theme-customization.md) for styling
- See [Deployment Guide](./deployment.md) for publishing your site