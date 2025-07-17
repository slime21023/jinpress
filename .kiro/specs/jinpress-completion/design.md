# Design Document

## Overview

This design document outlines the technical approach to complete the JinPress static site generator. The project has a solid architectural foundation but requires several critical fixes and missing components to be fully functional. The design focuses on fixing existing issues while maintaining the current architecture and ensuring all components work together seamlessly.

## Architecture

JinPress follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│       CLI       │───▶│     Builder     │───▶│   ThemeEngine   │
│   (cli.py)      │    │  (builder.py)   │    │ (theme/engine)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │    Renderer     │    │   Templates     │
                       │ (renderer.py)   │    │   & Assets      │
                       └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ SearchIndexer   │
                       │  (search.py)    │
                       └─────────────────┘
```

The architecture remains sound, but several components need fixes and enhancements.

## Components and Interfaces

### 1. CLI Module (cli.py)

**Current Issues:**
- Entry point mismatch in pyproject.toml
- Some error handling could be improved

**Design Changes:**
- Add `main()` function as entry point
- Ensure all commands work with proper error handling
- Maintain existing command structure

### 2. Renderer Module (renderer.py)

**Current Issues:**
- Method signature mismatches with tests
- Missing proper front matter extraction
- Incomplete markdown processing pipeline

**Design Changes:**
- Fix `render_markdown()` method to return tuple (html, metadata)
- Implement proper front matter extraction using existing YAML parsing
- Ensure code block rendering works with Pygments
- Fix link transformation for .md files

**Interface:**
```python
class Renderer:
    def render_markdown(self, file_path: Path) -> Tuple[str, Dict[str, Any]]
    def extract_front_matter(self, content: str) -> Tuple[Dict[str, Any], str]
    def process_file(self, file_path: Path, docs_dir: Path) -> Dict[str, Any]
```

### 3. Theme Engine (theme/engine.py)

**Current Issues:**
- Template loading may have path resolution issues
- Static file copying needs verification
- Template context preparation needs enhancement

**Design Changes:**
- Ensure proper template path resolution
- Verify static file copying works correctly
- Add missing CSS for syntax highlighting
- Enhance template context with all required data

### 4. Builder Module (builder.py)

**Current Issues:**
- Integration between components may have gaps
- Error handling could be more robust

**Design Changes:**
- Ensure proper integration between renderer, theme engine, and search indexer
- Add better error handling and logging
- Verify build process works end-to-end

### 5. Search Module (search.py)

**Current Issues:**
- Search index generation needs verification
- Client-side search implementation needs testing

**Design Changes:**
- Ensure search index is properly generated
- Verify JavaScript search functionality works
- Add proper error handling for missing search index

## Data Models

### Page Data Model
```python
{
    "title": str,
    "description": str,
    "content": str,  # Rendered HTML
    "frontmatter": Dict[str, Any],
    "url": str,
    "lastModified": float,
    "site": {
        "title": str,
        "description": str,
        "lang": str,
        "base": str,
    },
    "page": {
        "title": str,
        "description": str,
        "frontmatter": Dict[str, Any],
    },
    "theme": Dict[str, Any],  # Theme configuration
}
```

### Search Document Model
```python
{
    "title": str,
    "url": str,
    "content": str,  # Plain text content
    "description": str,
}
```

## Error Handling

### Error Types
- `ConfigError`: Configuration file issues
- `BuildError`: Build process failures
- `RendererError`: Markdown processing issues
- `ThemeError`: Theme loading/rendering issues
- `ScaffoldError`: Project creation issues

### Error Handling Strategy
- Graceful degradation where possible
- Clear error messages for users
- Proper logging for debugging
- Fail fast for critical errors

## Testing Strategy

### Unit Tests
- Fix existing test method signatures to match implementation
- Ensure all core functionality is tested
- Add tests for new/fixed functionality

### Integration Tests
- Test complete build process
- Test CLI commands end-to-end
- Test development server functionality

### Test Structure
```
tests/
├── test_builder.py      # Builder functionality
├── test_config.py       # Configuration loading
├── test_renderer.py     # Markdown rendering
├── test_theme.py        # Theme engine (new)
├── test_search.py       # Search functionality (new)
└── test_cli.py          # CLI commands (new)
```

## Implementation Plan

### Phase 1: Core Fixes
1. Fix CLI entry point
2. Fix renderer method signatures
3. Fix template loading issues
4. Add missing CSS for syntax highlighting

### Phase 2: Integration Testing
1. Test complete build process
2. Fix any integration issues
3. Ensure all CLI commands work

### Phase 3: Enhancement and Polish
1. Improve error handling
2. Add missing tests
3. Verify all features work as documented

## Dependencies

### Required Dependencies (already in pyproject.toml)
- `click`: CLI framework
- `minijinja`: Template engine
- `markdown-it-py`: Markdown processing
- `pyyaml`: YAML configuration
- `watchdog`: File watching
- `pygments`: Syntax highlighting
- `mdit-py-plugins`: Markdown extensions

### Missing Dependencies
- None identified - all required dependencies are present

## File Structure

The current file structure is well-organized and will be maintained:

```
jinpress/
├── __init__.py
├── __main__.py
├── cli.py              # CLI interface
├── config.py           # Configuration management
├── builder.py          # Site builder
├── renderer.py         # Markdown renderer
├── scaffold.py         # Project scaffolding
├── search.py           # Search indexing
├── server.py           # Development server
└── theme/
    ├── __init__.py
    ├── engine.py       # Theme engine
    └── default/        # Default theme
        ├── templates/  # HTML templates
        └── static/     # CSS, JS, assets
```

## Security Considerations

- Input validation for configuration files
- Safe file path handling to prevent directory traversal
- Proper HTML escaping in templates
- Safe YAML loading (already using `yaml.safe_load`)

## Performance Considerations

- Efficient file watching for development server
- Optimized search index generation
- Minimal template context preparation
- Proper caching where appropriate (already implemented with `.jinpress/cache/`)

## Compatibility

- Python 3.8+ support (as specified in pyproject.toml)
- Cross-platform compatibility (Windows, macOS, Linux)
- Modern browser support for generated sites