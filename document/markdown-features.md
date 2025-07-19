# Markdown Features

JinPress supports rich Markdown syntax and extensions for creating beautiful documentation.

## Front Matter

Add YAML front matter to define page metadata:

```markdown
---
title: "Page Title"
description: "Page description for SEO"
date: "2025-01-19"
author: "Author Name"
tags: ["tag1", "tag2"]
---

# Page Content

Your markdown content here.
```

## Basic Syntax

### Headers
```markdown
# H1 Header
## H2 Header
### H3 Header
#### H4 Header
##### H5 Header
###### H6 Header
```

### Text Formatting
```markdown
**Bold text**
*Italic text*
***Bold and italic***
~~Strikethrough~~
`Inline code`
```

### Links
```markdown
[Link text](https://example.com)
[Relative link](./other-page.md)
[Reference link][ref]

[ref]: https://example.com "Reference title"
```

### Images
```markdown
![Alt text](./images/example.jpg)
![Web image](https://example.com/image.jpg "Image title")
```

### Lists

**Unordered:**
```markdown
- Item 1
- Item 2
  - Sub-item 2.1
  - Sub-item 2.2
- Item 3
```

**Ordered:**
```markdown
1. First item
2. Second item
   1. Sub-item 2.1
   2. Sub-item 2.2
3. Third item
```

### Tables
```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |

| Left | Center | Right |
|:-----|:------:|------:|
| L    |   C    |     R |
```

### Blockquotes
```markdown
> This is a blockquote.
> 
> It can span multiple paragraphs.
> 
> > Nested blockquotes are also supported.
```

## Code Blocks

### Basic Code Blocks
````markdown
```
Plain code block
No syntax highlighting
```
````

### Syntax Highlighting
````markdown
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
```
````

### Supported Languages

JinPress uses Pygments for syntax highlighting, supporting 500+ languages:

- **Web**: `html`, `css`, `javascript`, `typescript`, `json`, `xml`
- **Python**: `python`, `python3`, `py`
- **Systems**: `c`, `cpp`, `rust`, `go`
- **JVM**: `java`, `kotlin`, `scala`
- **Scripts**: `bash`, `shell`, `powershell`
- **Data**: `sql`, `yaml`, `toml`, `csv`
- **Others**: `php`, `ruby`, `swift`, `r`, `matlab`

### Line Highlighting
````markdown
```python{1,3-5}
def example_function():
    # This line is highlighted (line 1)
    x = 1
    y = 2  # This line is highlighted (line 3)
    z = 3  # This line is highlighted (line 4)
    return x + y + z  # This line is highlighted (line 5)
```
````

## Custom Containers

### Tip Container
```markdown
:::tip
This is a tip container for helpful advice.
:::

:::tip Custom Title
You can add custom titles to containers.
:::
```

### Warning Container
```markdown
:::warning
This is a warning container for important notices.
:::
```

### Danger Container
```markdown
:::danger
This is a danger container for critical warnings.
:::
```

### Info Container
```markdown
:::info
This is an info container for additional information.
:::
```

### Details Container
```markdown
:::details Click to expand
This content is collapsed by default.
Users need to click to see it.

Can contain any Markdown content:

- List items
- **Bold text**
- `Code`

```python
def example():
    return "Hello, World!"
```
:::
```

## Link Processing

JinPress automatically processes `.md` file links:

```markdown
[Other page](./other-page.md)        → /other-page/
[Guide](../guide/index.md)          → /guide/
[Config](./guide/configuration.md)   → /guide/configuration/
```

### Anchor Links
```markdown
[Jump to section](#section-name)
[Jump to other page section](./other-page.md#section-name)
```

### External Links
```markdown
[External link](https://example.com)
```

## HTML Support

JinPress supports inline HTML in Markdown:

```markdown
<div class="custom-container">
  <h3>Custom HTML Container</h3>
  <p>You can use HTML tags in Markdown.</p>
</div>

<details>
  <summary>Click to expand</summary>
  <p>This uses HTML details element.</p>
</details>
```

## Best Practices

### File Organization
```
docs/
├── index.md              # Homepage
├── guide/                # Guide section
│   ├── index.md          # Guide homepage
│   ├── getting-started.md
│   └── advanced.md
├── api/                  # API documentation
│   ├── index.md
│   └── reference.md
└── examples/             # Examples
    ├── index.md
    └── basic.md
```

### Header Structure
```markdown
# Page Title (H1) - Use only once per page

## Main Section (H2)

### Subsection (H3)

#### Detail Section (H4)

##### Minor Section (H5)

###### Smallest Section (H6)
```

### Link Best Practices
```markdown
<!-- Good -->
[Configuration Guide](./configuration.md)
[GitHub Project](https://github.com/user/repo)

<!-- Avoid -->
[Click here](./configuration.md)
[https://github.com/user/repo](https://github.com/user/repo)
```

### Image Best Practices
```markdown
<!-- Provide alt text -->
![JinPress Architecture](./images/architecture.png)

<!-- Use relative paths -->
![Example Screenshot](../images/example.png)

<!-- Describe complex images -->
![System architecture showing frontend, backend, and database relationships](./images/architecture.png)
```

### Code Block Best Practices
````markdown
<!-- Specify language -->
```python
def hello():
    print("Hello, World!")
```

<!-- Add comments for clarity -->
```yaml
# config.yml
site:
  title: "My Site"  # Site title
  base: "/"          # Base path
```

<!-- Highlight important lines -->
```javascript{2,4-6}
function example() {
    const important = "This line is important";
    const normal = "Normal line";
    const highlight1 = "Highlighted line 1";
    const highlight2 = "Highlighted line 2";
    const highlight3 = "Highlighted line 3";
}
```
````

## Common Issues

### Chinese Characters
Ensure files use UTF-8 encoding:

```bash
# Check file encoding
file -bi filename.md

# Convert encoding if needed
iconv -f GB2312 -t UTF-8 filename.md > filename_utf8.md
```

### Broken Links
Check link paths:

```markdown
<!-- Correct relative paths -->
[Other page](./other-page.md)
[Parent directory](../index.md)

<!-- Common errors -->
[Wrong link](other-page)      # Missing extension
[Wrong link](/other-page.md)  # Absolute path may be incorrect
```

### Code Highlighting Issues
Verify language names:

````markdown
<!-- Correct -->
```python
print("Hello")
```

<!-- Incorrect -->
```py3  # Should use 'python'
print("Hello")
```
````

### Container Syntax
Check container syntax:

```markdown
<!-- Correct -->
:::tip
Content
:::

<!-- Incorrect -->
::tip  # Missing colon
Content
::
```