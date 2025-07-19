# Theme Customization

JinPress uses an **exclusive mode** theme system: use the default theme or create a complete custom theme.

## Theme System Overview

**Default Theme Mode** (Recommended):
- No `templates/` directory
- Uses built-in theme automatically
- Add custom static files to `static/`

**Custom Theme Mode** (Advanced):
- Create `templates/` directory
- Must provide complete template set
- Include all required static files

## File Structure

### Default Theme Mode

```
project-root/
├── docs/                    # Markdown files
├── static/                  # Custom static files → /static/
└── config.yml

# Output
dist/
├── assets/                  # Theme assets (from built-in theme)
│   ├── css/
│   └── js/
└── static/                  # User static files
```

### Custom Theme Mode

```
project-root/
├── docs/                    # Markdown files
├── templates/               # Custom theme (exclusive)
│   ├── base.html           # Required
│   ├── page.html           # Required
│   ├── nav.html            # Required
│   ├── sidebar.html        # Required
│   └── static/             # Theme static files
│       ├── css/
│       └── js/
├── static/                  # Additional user files
└── config.yml

# Output
dist/
├── assets/                  # Theme assets (from custom theme)
└── static/                  # User static files
```

## Template System

JinPress uses [minijinja](https://github.com/mitsuhiko/minijinja) templating engine.

### Required Templates

When creating a custom theme, you must provide:

1. **base.html** - Base HTML structure
2. **page.html** - Page content template
3. **nav.html** - Navigation template
4. **sidebar.html** - Sidebar template

### Template Variables

#### Page Variables
```html
{{ title }}              <!-- Page title -->
{{ description }}        <!-- Page description -->
{{ content }}            <!-- Page HTML content -->
{{ url }}               <!-- Page URL -->
{{ lastModified }}      <!-- Last modified timestamp -->
```

#### Site Variables
```html
{{ site.title }}         <!-- Site title -->
{{ site.description }}   <!-- Site description -->
{{ site.lang }}         <!-- Site language -->
{{ site.base }}         <!-- Base path -->
```

#### Theme Configuration
```html
{{ theme.nav }}          <!-- Navigation items -->
{{ theme.sidebar }}      <!-- Sidebar configuration -->
{{ theme.socialLinks }}  <!-- Social links -->
{{ theme.editLink }}     <!-- Edit link config -->
{{ theme.footer }}       <!-- Footer config -->
```

### Template Filters

#### url_for
Generate correct URLs with base path:

```html
<link rel="stylesheet" href="{{ '/assets/css/main.css' | url_for(site.base) }}">
<a href="{{ '/guide/' | url_for(site.base) }}">Guide</a>
```

#### format_date
Format timestamps:

```html
<span>Last updated: {{ lastModified | format_date('%B %d, %Y') }}</span>
```

## Static Files

### Theme Static Files
- **Location**: `templates/static/` (custom) or built-in theme
- **Output**: `dist/assets/`
- **Reference**: `/assets/` path

### User Static Files
- **Location**: `static/`
- **Output**: `dist/static/`
- **Reference**: `/static/` path

### Referencing Static Files

#### Theme Assets
```html
<!-- CSS -->
<link rel="stylesheet" href="{{ '/assets/css/main.css' | url_for(site.base) }}">

<!-- JavaScript -->
<script src="{{ '/assets/js/main.js' | url_for(site.base) }}"></script>

<!-- Images -->
<img src="{{ '/assets/images/logo.png' | url_for(site.base) }}" alt="Logo">
```

#### User Static Files
```html
<link rel="stylesheet" href="{{ '/static/custom.css' | url_for(site.base) }}">
<script src="{{ '/static/custom.js' | url_for(site.base) }}"></script>
```

## Creating a Custom Theme

### Step 1: Create Template Directory

```bash
mkdir templates
mkdir templates/static
mkdir templates/static/css
mkdir templates/static/js
```

### Step 2: Base Template

Create `templates/base.html`:

```html
<!DOCTYPE html>
<html lang="{{ site.lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if page.title != site.title %}{{ page.title }} | {{ site.title }}{% else %}{{ site.title }}{% endif %}</title>
    <meta name="description" content="{{ page.description or site.description }}">
    
    <link rel="stylesheet" href="{{ '/assets/css/main.css' | url_for(site.base) }}">
    <link rel="stylesheet" href="{{ '/assets/css/highlight.css' | url_for(site.base) }}">
</head>
<body>
    <div class="layout">
        {% include "nav.html" %}
        
        {% if theme.sidebar %}
        <aside class="sidebar">
            {% include "sidebar.html" %}
        </aside>
        {% endif %}
        
        <main class="content">
            {% block content %}{% endblock %}
        </main>
    </div>
    
    <script src="{{ '/assets/js/main.js' | url_for(site.base) }}"></script>
    <script src="{{ '/assets/js/search.js' | url_for(site.base) }}"></script>
</body>
</html>
```

### Step 3: Page Template

Create `templates/page.html`:

```html
{% extends "base.html" %}

{% block content %}
<article class="page">
    <header class="page-header">
        <h1>{{ title }}</h1>
        {% if description %}
        <p class="description">{{ description }}</p>
        {% endif %}
    </header>
    
    <div class="page-content">
        {{ content | safe }}
    </div>
    
    {% if theme.editLink and theme.editLink.pattern %}
    <div class="edit-link">
        <a href="{{ theme.editLink.pattern.replace(':path', page.url.strip('/') + '.md') }}" target="_blank">
            {{ theme.editLink.text }}
        </a>
    </div>
    {% endif %}
</article>
{% endblock %}
```

### Step 4: Navigation Template

Create `templates/nav.html`:

```html
<nav class="nav">
    <div class="nav-container">
        <a href="{{ '/' | url_for(site.base) }}" class="nav-title">
            {{ site.title }}
        </a>
        
        <ul class="nav-menu">
            {% for item in theme.nav %}
            <li>
                <a href="{{ item.link | url_for(site.base) }}">{{ item.text }}</a>
            </li>
            {% endfor %}
        </ul>
    </div>
</nav>
```

### Step 5: Sidebar Template

Create `templates/sidebar.html`:

```html
<div class="sidebar-content">
    {% for path, items in theme.sidebar.items() %}
    <div class="sidebar-group">
        {% for item in items %}
        <a href="{{ item.link | url_for(site.base) }}" class="sidebar-link">
            {{ item.text }}
        </a>
        {% endfor %}
    </div>
    {% endfor %}
</div>
```

### Step 6: Custom Styles

Create `templates/static/css/main.css`:

```css
/* Custom theme styles */
:root {
  --primary-color: #3498db;
  --text-color: #333;
  --background-color: #fff;
  --border-color: #e1e8ed;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: var(--text-color);
  background-color: var(--background-color);
  margin: 0;
  padding: 0;
}

.layout {
  display: flex;
  min-height: 100vh;
}

.nav {
  background-color: var(--primary-color);
  color: white;
  padding: 1rem;
}

.content {
  flex: 1;
  padding: 2rem;
  max-width: 800px;
}

.sidebar {
  width: 250px;
  background-color: #f8f9fa;
  padding: 1rem;
}

/* Responsive */
@media (max-width: 768px) {
  .layout {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
  }
}
```

## Best Practices

### Theme Development

1. **Start with default theme**: Copy built-in templates as starting point
2. **Test responsiveness**: Ensure mobile compatibility
3. **Maintain accessibility**: Use semantic HTML and ARIA labels
4. **Optimize performance**: Minimize CSS/JS file sizes

### File Organization

```
templates/
├── base.html              # Base layout
├── page.html              # Page template
├── nav.html               # Navigation
├── sidebar.html           # Sidebar
└── static/
    ├── css/
    │   ├── main.css       # Main styles
    │   └── highlight.css  # Syntax highlighting
    └── js/
        ├── main.js        # Main JavaScript
        └── search.js      # Search functionality
```

### CSS Architecture

```css
/* Use CSS custom properties for theming */
:root {
  --primary-color: #3498db;
  --secondary-color: #2c3e50;
  /* ... */
}

/* Component-based organization */
.nav { /* Navigation styles */ }
.sidebar { /* Sidebar styles */ }
.content { /* Content styles */ }
.page { /* Page-specific styles */ }
```

## Troubleshooting

### Template not found
- Ensure all required templates exist in `templates/`
- Check template file names match exactly

### Static files not loading
- Verify `templates/static/` directory structure
- Check file paths in templates use correct filters

### Styles not applying
- Confirm CSS files are in `templates/static/css/`
- Verify CSS syntax and selectors