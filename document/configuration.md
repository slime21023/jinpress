# Configuration

JinPress uses a single `config.yml` file for all configuration.

## Basic Structure

```yaml
site:
  title: "Site Title"
  description: "Site description"
  lang: "en-US"
  base: "/"

themeConfig:
  nav: []
  sidebar: {}
  socialLinks: []
  editLink: {}
  footer: {}
  lastUpdated: true
```

## Site Configuration

### site.title
- **Type**: `string`
- **Default**: `"JinPress Site"`
- **Description**: Site title for browser title and page headers

### site.description
- **Type**: `string`
- **Default**: `"A JinPress documentation site"`
- **Description**: Site description for SEO meta tags

### site.lang
- **Type**: `string`
- **Default**: `"en-US"`
- **Description**: Site language for HTML `lang` attribute

### site.base
- **Type**: `string`
- **Default**: `"/"`
- **Description**: Base path for deployment to subdirectories

```yaml
site:
  base: "/"              # Deploy to root
  base: "/docs/"         # Deploy to /docs/ subdirectory
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
    - text: "API"
      link: "/api/"
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
    
    "/api/":
      - text: "API Overview"
        link: "/api/"
      - text: "Reference"
        link: "/api/reference/"
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

**Supported icons**: `github`, `twitter`, `discord`, `linkedin`, `facebook`, `instagram`, `youtube`

### Edit Link

```yaml
themeConfig:
  editLink:
    pattern: "https://github.com/user/repo/edit/main/docs/:path"
    text: "Edit this page"
```

The `:path` placeholder is replaced with the file path.

### Footer

```yaml
themeConfig:
  footer:
    message: "Built with JinPress"
    copyright: "Copyright © 2025"
```

### Last Updated

```yaml
themeConfig:
  lastUpdated: true   # Show last updated time
```

## Complete Example

```yaml
site:
  title: "My Documentation"
  description: "Comprehensive documentation site"
  lang: "en-US"
  base: "/"

themeConfig:
  nav:
    - text: "Home"
      link: "/"
    - text: "Guide"
      link: "/guide/"
    - text: "API"
      link: "/api/"
  
  sidebar:
    "/guide/":
      - text: "Quick Start"
        link: "/guide/getting-started/"
      - text: "Configuration"
        link: "/guide/configuration/"
      - text: "Deployment"
        link: "/guide/deployment/"
    
    "/api/":
      - text: "Overview"
        link: "/api/"
      - text: "Reference"
        link: "/api/reference/"
  
  socialLinks:
    - icon: "github"
      link: "https://github.com/user/repo"
  
  editLink:
    pattern: "https://github.com/user/repo/edit/main/docs/:path"
    text: "Edit this page"
  
  footer:
    message: "Built with ❤️ and JinPress"
    copyright: "Copyright © 2025"
  
  lastUpdated: true
```

## Validation

JinPress validates configuration on startup:

- Required fields must be strings
- Navigation items must have `text` and `link` fields
- Structure types must match (arrays, objects)

## Environment-Specific Config

Use different config files for different environments:

```bash
jinpress serve --config config.dev.yml
jinpress build --config config.prod.yml
```