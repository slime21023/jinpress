"""
Property-based tests for BuildEngine.

Feature: jinpress-rewrite
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from jinpress.builder import apply_base_path, generate_url_path
from jinpress.search import SearchIndexer

# Strategies for generating valid file paths
filename_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=20,
).filter(lambda x: x.strip() and not x.startswith("-") and not x.startswith("_"))

# Strategy for directory names
dirname_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=15,
).filter(lambda x: x.strip() and not x.startswith("-") and not x.startswith("_"))


@st.composite
def markdown_file_path_strategy(draw):
    """Generate valid markdown file paths."""
    # Decide if it's a nested path or root level
    depth = draw(st.integers(min_value=0, max_value=3))

    parts = []
    for _ in range(depth):
        parts.append(draw(dirname_strategy))

    # Add filename
    filename = draw(filename_strategy)

    # Decide if it's an index file
    is_index = draw(st.booleans())
    if is_index:
        parts.append("index.md")
    else:
        parts.append(f"{filename}.md")

    return "/".join(parts)


# Strategy for base paths
base_path_strategy = st.sampled_from(
    ["/", "/docs/", "/my-project/", "/v1/", "/api/docs/"]
)


@settings(max_examples=100)
@given(file_path_str=markdown_file_path_strategy())
def test_url_path_generation(file_path_str):
    """
    Feature: jinpress-rewrite, Property 7: URL 路徑生成
    Validates: Requirements 5.2

    For any Markdown file path, the generated URL path SHALL conform to
    clean URL format (ending with /, not containing .html or .md extension).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_dir = Path(tmpdir) / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Create the file path
        file_path = docs_dir / file_path_str

        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create the file
        file_path.write_text("# Test\n\nContent", encoding="utf-8")

        # Generate URL path
        url_path = generate_url_path(file_path, docs_dir)

        # Property 1: URL path SHALL end with /
        assert url_path.endswith("/"), (
            f"URL path does not end with /:\nFile: {file_path_str}\nURL: {url_path}"
        )

        # Property 2: URL path SHALL NOT contain .md extension
        assert ".md" not in url_path, (
            f"URL path contains .md extension:\nFile: {file_path_str}\nURL: {url_path}"
        )

        # Property 3: URL path SHALL NOT contain .html extension
        assert ".html" not in url_path, (
            f"URL path contains .html extension:\n"
            f"File: {file_path_str}\n"
            f"URL: {url_path}"
        )

        # Property 4: URL path SHALL start with /
        assert url_path.startswith("/"), (
            f"URL path does not start with /:\nFile: {file_path_str}\nURL: {url_path}"
        )

        # Property 5: index.md files SHALL not have "index" in URL
        if file_path_str.endswith("index.md"):
            assert "index" not in url_path, (
                f"URL path contains 'index' for index.md file:\n"
                f"File: {file_path_str}\n"
                f"URL: {url_path}"
            )


@settings(max_examples=100)
@given(
    url=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_/.",
        min_size=1,
        max_size=50,
    ).map(lambda x: "/" + x.lstrip("/")),
    base_path=base_path_strategy,
)
def test_base_path_prefix(url, base_path):
    """
    Feature: jinpress-rewrite, Property 8: Base 路徑前綴
    Validates: Requirements 8.1, 8.4

    For any configured base path and any resource link, the build output
    SHALL include the correct base prefix for all absolute paths.
    """
    result = apply_base_path(url, base_path)

    # Normalize base path for comparison
    normalized_base = base_path.rstrip("/")

    # Property 1: Result SHALL start with base path (if base is not /)
    if normalized_base and normalized_base != "/":
        assert result.startswith(normalized_base), (
            f"Result does not start with base path:\n"
            f"URL: {url}\n"
            f"Base: {base_path}\n"
            f"Result: {result}"
        )

    # Property 2: Original path content SHALL be preserved after base
    if normalized_base and normalized_base != "/":
        # The original URL should appear after the base
        expected_suffix = url if url.startswith("/") else "/" + url
        path_preserved = (
            result.endswith(expected_suffix) or result == normalized_base + url
        )
        assert path_preserved, (
            f"Original path not preserved:\n"
            f"URL: {url}\n"
            f"Base: {base_path}\n"
            f"Result: {result}"
        )


@settings(max_examples=100)
@given(
    external_url=st.sampled_from(
        [
            "https://example.com",
            "http://test.org/path",
            "//cdn.example.com/file.js",
            "#anchor",
            "#section-1",
        ]
    ),
    base_path=base_path_strategy,
)
def test_base_path_skips_external_urls(external_url, base_path):
    """
    Feature: jinpress-rewrite, Property 8: Base 路徑前綴 (external URLs)
    Validates: Requirements 8.1, 8.4

    External URLs and anchors SHALL NOT have base path applied.
    """
    result = apply_base_path(external_url, base_path)

    # Property: External URLs SHALL remain unchanged
    assert result == external_url, (
        f"External URL was modified:\n"
        f"URL: {external_url}\n"
        f"Base: {base_path}\n"
        f"Result: {result}"
    )


# Strategies for search index testing
page_title_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz ",
    min_size=1,
    max_size=30,
).filter(lambda x: x.strip())

page_content_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz ",
    min_size=1,
    max_size=100,
).filter(lambda x: x.strip())

url_path_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=20,
).map(lambda x: "/" + x.strip("-_") + "/")


@st.composite
def page_info_strategy(draw):
    """Generate valid page information for search indexing."""
    title = draw(page_title_strategy)
    content = draw(page_content_strategy)
    desc_strategy = st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", max_size=50)
    return {
        "title": title,
        "url_path": draw(url_path_strategy),
        "description": draw(desc_strategy),
        "html_content": f"<h1>{title}</h1><p>{content}</p>",
    }


@st.composite
def pages_list_strategy(draw):
    """Generate a list of pages for search indexing."""
    num_pages = draw(st.integers(min_value=1, max_value=5))
    pages = []
    urls_seen = set()

    for i in range(num_pages):
        title = draw(page_title_strategy)
        content = draw(page_content_strategy)
        # Generate unique URL
        url = f"/page{i}/"
        urls_seen.add(url)
        pages.append(
            {
                "title": title,
                "url_path": url,
                "description": f"Description {i}",
                "html_content": f"<h1>{title}</h1><p>{content}</p>",
            }
        )

    return pages


@settings(max_examples=100)
@given(pages=pages_list_strategy())
def test_search_index_completeness(pages):
    """
    Feature: jinpress-rewrite, Property 9: 搜尋索引完整性
    Validates: Requirements 7.1, 7.2

    For any set of built pages, the generated search index SHALL contain
    each page's URL, title, and content summary.
    """
    indexer = SearchIndexer()

    # Add all pages to the index
    for page in pages:
        indexer.add_document(page)

    # Get the index data
    index_data = indexer.get_index_data()

    # Property 1: Index SHALL contain same number of documents as pages
    assert len(index_data) == len(pages), (
        f"Index document count mismatch:\n"
        f"Expected: {len(pages)}\n"
        f"Got: {len(index_data)}"
    )

    # Property 2: Each document SHALL have required fields
    for doc in index_data:
        assert "url" in doc, f"Document missing 'url' field: {doc}"
        assert "title" in doc, f"Document missing 'title' field: {doc}"
        assert "content" in doc, f"Document missing 'content' field: {doc}"
        assert "headings" in doc, f"Document missing 'headings' field: {doc}"

    # Property 3: All page URLs SHALL be in the index
    indexed_urls = {doc["url"] for doc in index_data}
    for page in pages:
        assert page["url_path"] in indexed_urls, (
            f"Page URL not found in index:\n"
            f"URL: {page['url_path']}\n"
            f"Indexed URLs: {indexed_urls}"
        )

    # Property 4: All page titles SHALL be in the index
    indexed_titles = {doc["title"] for doc in index_data}
    for page in pages:
        assert page["title"] in indexed_titles, (
            f"Page title not found in index:\n"
            f"Title: {page['title']}\n"
            f"Indexed titles: {indexed_titles}"
        )
