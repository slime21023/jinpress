# Troubleshooting

Common issues and solutions when using JinPress.

## Installation Issues

### Python Version Incompatible

**Error:**
```
ERROR: Package 'jinpress' requires a different Python: 3.7.0 not in '>=3.8'
```

**Solution:**
```bash
# Check Python version
python --version

# Upgrade to Python 3.8+
# Using pyenv (recommended)
pyenv install 3.11.0
pyenv global 3.11.0

# Or system package manager
# Ubuntu/Debian
sudo apt update && sudo apt install python3.11

# macOS
brew install python@3.11
```

### pip Installation Failed

**Error:**
```
ERROR: Could not install packages due to an EnvironmentError
```

**Solution:**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Use user installation
pip install --user jinpress

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install jinpress
```

### Command Not Found

**Error:**
```bash
jinpress: command not found
```

**Solution:**
```bash
# Check installation
pip show jinpress

# Use module execution
python -m jinpress

# Check PATH
echo $PATH

# Find installation path
python -c "import jinpress; print(jinpress.__file__)"
```

## Configuration Issues

### YAML Syntax Error

**Error:**
```
❌ Configuration error: Invalid YAML in config file
```

**Solution:**
```bash
# Validate YAML syntax
python -c "
import yaml
try:
    with open('config.yml') as f:
        yaml.safe_load(f)
    print('YAML syntax is correct')
except yaml.YAMLError as e:
    print(f'YAML error: {e}')
"
```

**Common YAML errors:**
```yaml
# Indentation issues
site:
  title: "Title"    # Correct: 2 spaces
    base: "/"       # Wrong: 4 spaces

# Quote issues
title: "Title with: colon"  # Correct
title: Title with: colon    # Wrong

# List format
nav:
  - text: "Home"    # Correct
    link: "/"
  -text: "Wrong"    # Wrong: missing space
```

### Configuration Field Error

**Error:**
```
❌ Configuration error: site.title must be a string
```

**Solution:**
```yaml
# Check data types
site:
  title: "My Site"        # String ✓
  # title: 123            # Number ✗
  # title: true           # Boolean ✗

themeConfig:
  nav: []                 # Array ✓
  # nav: "wrong"          # String ✗
  
  sidebar: {}             # Object ✓
  # sidebar: []           # Array ✗
```

## Build Issues

### Markdown Processing Error

**Error:**
```
WARNING: Failed to process file.md: Invalid YAML front matter
```

**Solution:**
```markdown
<!-- Check front matter format -->
---
title: "Correct Title"
description: "Description"
---

<!-- Common errors -->
---
title: [Wrong format    # Missing closing bracket
description: Contains: colon without quotes
---

<!-- Fixed -->
---
title: "Correct Format"
description: "Contains: colon with quotes"
---
```

### Template Error

**Error:**
```
❌ Build error: Error rendering template 'page.html': template not found
```

**Solution:**
```bash
# Check template files
ls -la templates/

# If using custom theme, ensure all required files exist
templates/
├── base.html
├── page.html
├── nav.html
├── sidebar.html
└── static/

# If not using custom theme, remove templates directory
rm -rf templates/
```

### Static Files Error

**Error:**
```
WARNING: Failed to copy static files: Permission denied
```

**Solution:**
```bash
# Check file permissions
ls -la static/

# Fix permissions
chmod -R 644 static/
chmod 755 static/

# Check disk space
df -h

# Check target directory
ls -la dist/
```

## Development Server Issues

### Port Already in Use

**Error:**
```
❌ Server error: Port 8000 is already in use
```

**Solution:**
```bash
# Use different port
jinpress serve --port 3000

# Find process using port
# Linux/Mac
lsof -i :8000
netstat -tulpn | grep :8000

# Windows
netstat -ano | findstr :8000

# Kill process
kill -9 <PID>
```

### Live Reload Not Working

**Issue:** File changes don't trigger rebuild

**Solution:**
```bash
# Check file system limits (Linux)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Manual rebuild
jinpress build

# Use verbose mode to see what's being watched
jinpress serve --verbose
```

### Memory Issues

**Error:**
```
MemoryError: Unable to allocate memory
```

**Solution:**
```bash
# Check memory usage
free -h  # Linux
top      # View processes

# Add swap space (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Optimize Python memory usage
export PYTHONHASHSEED=0
export PYTHONOPTIMIZE=1
```

## Content Issues

### Character Encoding Problems

**Issue:** Non-English characters display as garbled text

**Solution:**
```bash
# Check file encoding
file -bi docs/*.md

# Convert to UTF-8
iconv -f GB2312 -t UTF-8 file.md > file_utf8.md

# Set environment variables
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Broken Links

**Issue:** Internal links return 404

**Solution:**
```markdown
<!-- Correct link formats -->
[Correct link](./other-page.md)
[Correct link](../guide/index.md)

<!-- Common errors -->
[Wrong link](other-page)        # Missing extension
[Wrong link](/other-page.md)    # Absolute path
[Wrong link](./Other-Page.md)   # Case mismatch

<!-- Check if file exists -->
ls -la docs/other-page.md
```

### Images Not Loading

**Issue:** Images don't display

**Solution:**
```markdown
<!-- Check image paths -->
![Correct path](./images/example.png)
![Correct path](../static/images/example.png)

<!-- Check if file exists -->
ls -la static/images/example.png

<!-- Check file permissions -->
chmod 644 static/images/example.png
```

## Search Issues

### Search Index Not Generated

**Issue:** Search functionality doesn't work

**Solution:**
```bash
# Check search index file
ls -la dist/search-index.json

# Check index content
cat dist/search-index.json | python -m json.tool

# Force rebuild
jinpress build --clean
```

### Search Results Inaccurate

**Issue:** Search returns irrelevant results

**Solution:**
```bash
# Check indexed content
python -c "
import json
with open('dist/search-index.json') as f:
    data = json.load(f)
    for doc in data['documents']:
        print(f'Title: {doc[\"title\"]}')
        print(f'Content: {doc[\"content\"][:100]}...')
        print('---')
"
```

## Deployment Issues

### GitHub Pages Build Failed

**Issue:** GitHub Actions build fails

**Solution:**
```yaml
# Check .github/workflows/deploy.yml
name: Deploy to GitHub Pages
on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'  # Ensure correct version
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install jinpress
    
    - name: Build site
      run: jinpress build
    
    - name: Deploy
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./dist
```

### Asset Loading Failed

**Issue:** CSS/JS files don't load after deployment

**Solution:**
```yaml
# Check base path configuration
site:
  base: "/"              # Root deployment
  # base: "/my-project/" # Subdirectory deployment

# Check generated HTML
grep -r "assets/" dist/
```

## Performance Issues

### Slow Build Times

**Issue:** Large projects take too long to build

**Solution:**
```bash
# Use incremental build
jinpress build --no-clean

# Check file count
find docs/ -name "*.md" | wc -l

# Optimize images
find static/ -name "*.jpg" -o -name "*.png" | xargs ls -lh

# Consider splitting large files
```

### High Memory Usage

**Issue:** Build process uses too much memory

**Solution:**
```bash
# Monitor memory usage
top -p $(pgrep -f jinpress)

# Set memory limits
export PYTHONHASHSEED=0
ulimit -v 1000000  # Limit virtual memory

# Consider project splitting
```

## Debug Tools

### Log Analysis

```bash
# Enable verbose logging
jinpress build --verbose 2>&1 | tee build.log

# Analyze errors
grep -i error build.log
grep -i warning build.log
```

### File Inspection

```bash
# Check project structure
tree -a -I '.git|__pycache__|*.pyc'

# Check file encoding
find docs/ -name "*.md" -exec file -bi {} \;

# Check permissions
find . -type f -not -perm 644 -ls
find . -type d -not -perm 755 -ls
```

### Network Issues

```bash
# Test connectivity
ping github.com
curl -I https://pypi.org/simple/jinpress/

# Check DNS
nslookup pypi.org
```

## Getting Help

### Bug Reports

When reporting issues, include:

```
**Environment:**
- OS: 
- Python version: 
- JinPress version: 

**Steps to reproduce:**
1. 
2. 
3. 

**Expected behavior:**


**Actual behavior:**


**Error messages:**
```

### Diagnostic Information

```bash
# Collect system info
python --version
pip show jinpress
uname -a  # Linux/Mac
systeminfo  # Windows

# Collect project info
jinpress info
ls -la
cat config.yml
```

### Debug Commands

```bash
# Complete debug workflow
jinpress info                    # Check project info
jinpress build --verbose        # Verbose build
python -m http.server 8000      # Test output (in dist/ directory)
```

Most issues can be resolved by carefully reading error messages and checking configuration files. Don't hesitate to seek community help if problems persist.