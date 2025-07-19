# Deployment

JinPress generates static files that can be deployed to any static hosting platform.

## Build for Production

First, build your site:

```bash
jinpress build
```

This generates all static files in the `dist/` directory.

## GitHub Pages

### GitHub Actions (Recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install jinpress
    
    - name: Build site
      run: jinpress build
    
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      if: github.ref == 'refs/heads/main'
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./dist
```

### Configure GitHub Pages

1. Go to repository Settings → Pages
2. Select "Deploy from a branch"
3. Choose `gh-pages` branch and `/ (root)` folder
4. Save settings

### Custom Domain

Add a `CNAME` file to `static/` directory:

```
# static/CNAME
yourdomain.com
```

## Netlify

### Git Integration

1. Login to [Netlify](https://netlify.com)
2. Click "New site from Git"
3. Connect your repository
4. Configure build settings:
   - **Build command**: `pip install jinpress && jinpress build`
   - **Publish directory**: `dist`

### Netlify Configuration

Create `netlify.toml`:

```toml
[build]
  command = "pip install jinpress && jinpress build"
  publish = "dist"

[build.environment]
  PYTHON_VERSION = "3.11"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 404

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000"
```

## Vercel

### Git Integration

1. Login to [Vercel](https://vercel.com)
2. Click "New Project"
3. Import your Git repository
4. Configure settings:
   - **Framework Preset**: Other
   - **Build Command**: `pip install jinpress && jinpress build`
   - **Output Directory**: `dist`

### Vercel Configuration

Create `vercel.json`:

```json
{
  "buildCommand": "pip install jinpress && jinpress build",
  "outputDirectory": "dist",
  "installCommand": "pip install jinpress",
  "routes": [
    {
      "src": "/assets/(.*)",
      "headers": {
        "cache-control": "public, max-age=31536000, immutable"
      }
    },
    {
      "handle": "filesystem"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

## Cloudflare Pages

### Git Integration

1. Login to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Go to Pages → Create a project
3. Connect your Git repository
4. Configure build settings:
   - **Build command**: `pip install jinpress && jinpress build`
   - **Build output directory**: `dist`
   - **Environment variables**: `PYTHON_VERSION=3.11`

## Firebase Hosting

### Setup

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and initialize
firebase login
firebase init hosting
```

### Configuration

Edit `firebase.json`:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "/assets/**",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

### Deploy

```bash
jinpress build
firebase deploy
```

## Custom Server

### Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /path/to/your/dist;
    index index.html;

    # Handle SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
        application/json;
}
```

### Apache

Create `.htaccess` in the `dist/` directory:

```apache
RewriteEngine On

# Handle SPA routing
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]

# Cache settings
<IfModule mod_expires.c>
    ExpiresActive on
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpg "access plus 1 year"
</IfModule>

# Gzip compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/javascript
</IfModule>
```

## Docker Deployment

### Dockerfile

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app
COPY . .

RUN pip install jinpress
RUN jinpress build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  jinpress-site:
    build: .
    ports:
      - "80:80"
    restart: unless-stopped
```

## Performance Optimization

### Image Optimization

```bash
# Install optimization tools
npm install -g imagemin-cli imagemin-webp imagemin-mozjpeg imagemin-pngquant

# Optimize images
imagemin static/images/* --out-dir=static/images/optimized --plugin=mozjpeg --plugin=pngquant
```

### Resource Compression

Enable gzip compression on your server for better performance.

### CDN Configuration

Use a CDN to serve static assets faster:

```yaml
# config.yml - if implementing CDN support
site:
  title: "My Site"
  base: "/"
  cdn: "https://cdn.example.com"  # Custom CDN domain
```

## Monitoring

### Google Analytics

Add to your custom theme's `base.html`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Sitemap Generation

Create a simple sitemap generator:

```python
# sitemap.py
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime

def generate_sitemap():
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    base_url = 'https://yourdomain.com'
    dist_dir = Path('dist')
    
    for html_file in dist_dir.rglob('*.html'):
        url = ET.SubElement(urlset, 'url')
        
        # Generate URL
        relative_path = html_file.relative_to(dist_dir)
        if relative_path.name == 'index.html':
            if relative_path.parent == Path('.'):
                loc_text = base_url + '/'
            else:
                loc_text = base_url + '/' + str(relative_path.parent) + '/'
        
        loc = ET.SubElement(url, 'loc')
        loc.text = loc_text
        
        lastmod = ET.SubElement(url, 'lastmod')
        lastmod.text = datetime.now().strftime('%Y-%m-%d')
    
    tree = ET.ElementTree(urlset)
    tree.write('dist/sitemap.xml', encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    generate_sitemap()
```

## Troubleshooting

### Common Issues

1. **Path problems**: Ensure `site.base` is configured correctly
2. **404 errors**: Configure server for SPA routing
3. **Asset loading failures**: Check static file paths
4. **Cache issues**: Clear browser cache or check CDN settings

### Debug Tips

```bash
# Test locally
cd dist
python -m http.server 8000

# Check build output
jinpress build --verbose
ls -la dist/

# Validate HTML
# Use HTML validators to check generated HTML
```