"""Custom container plugin for JinPress Markdown.

Supports tip, warning, danger, info, and details containers.
"""

from __future__ import annotations

# Container types and their default titles
CONTAINER_TYPES = {
    "tip": "TIP",
    "warning": "WARNING",
    "danger": "DANGER",
    "info": "INFO",
    "details": "Details",
}


def container_plugin(md):
    """Add custom container support to markdown-it.

    Syntax:
        ::: tip [title]
        Content here
        :::

        ::: details [title]
        Collapsible content
        :::

    Args:
        md: MarkdownIt instance.
    """

    def container_rule(state, startLine, endLine, silent):
        """Parse custom container blocks."""
        pos = state.bMarks[startLine] + state.tShift[startLine]
        maximum = state.eMarks[startLine]

        # Check for opening marker :::
        if pos + 3 > maximum:
            return False

        marker = state.src[pos : pos + 3]
        if marker != ":::":
            return False

        # Get the rest of the line (container type and optional title)
        params = state.src[pos + 3 : maximum].strip()

        if not params:
            return False

        # Parse container type and title
        parts = params.split(None, 1)
        container_type = parts[0].lower()

        if container_type not in CONTAINER_TYPES:
            return False

        title = parts[1] if len(parts) > 1 else CONTAINER_TYPES[container_type]

        if silent:
            return True

        # Find closing marker
        nextLine = startLine + 1
        found_close = False

        while nextLine < endLine:
            pos = state.bMarks[nextLine] + state.tShift[nextLine]
            maximum = state.eMarks[nextLine]

            if pos < maximum and state.src[pos : pos + 3] == ":::":
                # Check if it's just the closing marker
                rest = state.src[pos + 3 : maximum].strip()
                if not rest:
                    found_close = True
                    break

            nextLine += 1

        if not found_close:
            return False

        # Create tokens
        token = state.push("container_open", "div", 1)
        token.markup = ":::"
        token.block = True
        token.info = container_type
        token.meta = {"title": title}
        token.map = [startLine, nextLine + 1]

        # Parse content inside container
        old_parent = state.parentType
        old_line_max = state.lineMax
        state.parentType = "container"
        state.lineMax = nextLine

        # Tokenize the content
        state.md.block.tokenize(state, startLine + 1, nextLine)

        state.parentType = old_parent
        state.lineMax = old_line_max

        token = state.push("container_close", "div", -1)
        token.markup = ":::"
        token.block = True

        state.line = nextLine + 1
        return True

    def render_container_open(tokens, idx, options, env):
        """Render opening container tag."""
        token = tokens[idx]
        container_type = token.info
        title = token.meta.get("title", CONTAINER_TYPES.get(container_type, ""))

        if container_type == "details":
            return (
                f'<details class="custom-block details">\n'
                f"<summary>{_escape_html(title)}</summary>\n"
            )
        else:
            return (
                f'<div class="custom-block {container_type}">\n'
                f'<p class="custom-block-title">{_escape_html(title)}</p>\n'
            )

    def render_container_close(tokens, idx, options, env):
        """Render closing container tag."""
        # Find the corresponding open token to get the type
        open_idx = idx - 1
        while open_idx >= 0:
            if (
                tokens[open_idx].type == "container_open"
                and tokens[open_idx].level == tokens[idx].level
            ):
                break
            open_idx -= 1

        if open_idx >= 0 and tokens[open_idx].info == "details":
            return "</details>\n"
        return "</div>\n"

    # Register the block rule
    md.block.ruler.before("fence", "container", container_rule)

    # Register renderers
    md.renderer.rules["container_open"] = render_container_open
    md.renderer.rules["container_close"] = render_container_close


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
