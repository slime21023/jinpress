# CLI Reference

Complete command-line interface reference for JinPress.

## Global Options

- `--verbose` / `-v`: Enable verbose output
- `--help`: Show help information

## Commands

### jinpress init

Create a new JinPress project.

```bash
jinpress init [PROJECT_NAME] [OPTIONS]
```

**Options:**
- `--dir PATH`: Target directory (default: current directory)

**Examples:**
```bash
jinpress init my-docs
jinpress init my-docs --dir /path/to/projects
```

### jinpress build

Build the static site.

```bash
jinpress build [OPTIONS]
```

**Options:**
- `--no-clean`: Skip cleaning output directory
- `--config PATH`: Custom config file path

**Examples:**
```bash
jinpress build
jinpress build --no-clean
jinpress build --config custom-config.yml
```

### jinpress serve

Start development server with live reload.

```bash
jinpress serve [OPTIONS]
```

**Options:**
- `--host HOST`: Bind address (default: 127.0.0.1)
- `--port PORT`: Port number (default: 8000)
- `--config PATH`: Custom config file path

**Examples:**
```bash
jinpress serve
jinpress serve --host 0.0.0.0 --port 3000
```

### jinpress info

Display project information.

```bash
jinpress info [OPTIONS]
```

**Options:**
- `--config PATH`: Custom config file path

## Build Process

1. **Clean output directory** (if enabled)
2. **Process Markdown files**:
   - Extract front matter
   - Render Markdown to HTML
   - Apply syntax highlighting
3. **Generate HTML pages** using templates
4. **Copy static files**:
   - User files → `dist/static/`
   - Theme assets → `dist/assets/`
5. **Generate search index** → `dist/search-index.json`

## Development Server Features

- **Live reload**: Auto-rebuild on file changes
- **Error handling**: Build errors shown in terminal
- **File watching**: Monitors `docs/`, `config.yml`, `static/`, `templates/`

## Common Errors

### Configuration not found
```
❌ Error: config.yml not found
Run 'jinpress init' to create a new project
```

### Invalid YAML
```
❌ Configuration error: Invalid YAML in config file
```

### Build errors
```
❌ Build error: Docs directory not found
```

### Port in use
```
❌ Server error: Port 8000 is already in use
```

**Solution:** Use a different port with `--port 3000`