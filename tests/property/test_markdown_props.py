"""
Property-based tests for MarkdownProcessor.

Feature: jinpress-rewrite
"""

import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from jinpress.markdown import MarkdownProcessor

# Strategies for generating valid YAML-safe values
yaml_safe_text = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S", "Zs"),
        blacklist_characters="\x00\n\r\t",
    ),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip() and not x.startswith("-") and ":" not in x)

yaml_safe_value = st.one_of(
    yaml_safe_text,
    st.integers(min_value=-1000, max_value=1000),
    st.booleans(),
)


@st.composite
def frontmatter_dict_strategy(draw):
    """Generate valid YAML front matter dictionaries."""
    # Generate simple key-value pairs that are YAML-safe
    keys = draw(
        st.lists(
            st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz_",
                min_size=1,
                max_size=20,
            ),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )

    result = {}
    for key in keys:
        value = draw(yaml_safe_value)
        result[key] = value

    return result


@settings(max_examples=100)
@given(frontmatter=frontmatter_dict_strategy())
def test_frontmatter_round_trip(frontmatter):
    """
    Feature: jinpress-rewrite, Property 4: Front Matter Round-Trip
    Validates: Requirements 4.2, 4.8

    For any valid YAML front matter dictionary, serializing to YAML string
    then parsing SHALL produce an equivalent dictionary.
    """
    processor = MarkdownProcessor()

    # Serialize frontmatter to YAML format
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

    # Create markdown content with front matter
    content = f"---\n{yaml_str}---\n\n# Test Content\n"

    # Extract frontmatter
    extracted, body = processor.extract_frontmatter(content)

    # Property: Extracted frontmatter SHALL be equivalent to original
    assert extracted == frontmatter, (
        f"Round-trip failed:\nOriginal: {frontmatter}\nExtracted: {extracted}"
    )


# Strategies for generating markdown links
md_filename = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=30,
).filter(lambda x: x.strip() and not x.startswith("-"))

relative_path = st.one_of(
    md_filename.map(lambda x: f"{x}.md"),
    md_filename.map(lambda x: f"./{x}.md"),
    st.tuples(md_filename, md_filename).map(lambda t: f"{t[0]}/{t[1]}.md"),
    st.just("index.md"),
    md_filename.map(lambda x: f"{x}/index.md"),
)


@settings(max_examples=100)
@given(md_link=relative_path)
def test_markdown_link_transformation(md_link):
    """
    Feature: jinpress-rewrite, Property 5: Markdown 連結轉換
    Validates: Requirements 4.7

    For any Markdown content containing relative links to .md files,
    processing SHALL transform them to clean URL paths
    (removing .md extension and adding trailing slash).
    """
    processor = MarkdownProcessor()

    # Transform the link
    transformed = processor._transform_md_link(md_link)

    # Property 1: Transformed link SHALL NOT end with .md
    assert not transformed.endswith(".md"), (
        f"Link still ends with .md:\nOriginal: {md_link}\nTransformed: {transformed}"
    )

    # Property 2: Transformed link SHALL end with /
    assert transformed.endswith("/"), (
        f"Link does not end with /:\nOriginal: {md_link}\nTransformed: {transformed}"
    )

    # Property 3: index.md links SHALL be handled specially
    if md_link == "index.md":
        # Root index.md should become just /
        assert transformed == "/", (
            f"Root index.md should become /:\n"
            f"Original: {md_link}\n"
            f"Transformed: {transformed}"
        )
    elif md_link.endswith("/index.md"):
        # Directory index.md should become directory path without "index"
        # e.g., "foo/index.md" -> "foo/" but "index/index.md" -> "index/"
        assert not transformed.endswith("index/"), (
            f"index.md should be removed from path:\n"
            f"Original: {md_link}\n"
            f"Transformed: {transformed}"
        )


# Strategies for generating headings
heading_text = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "Zs"),
        blacklist_characters="\n\r\t#",
    ),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip())

heading_level = st.integers(min_value=1, max_value=6)


@st.composite
def heading_strategy(draw):
    """Generate a markdown heading."""
    level = draw(heading_level)
    text = draw(heading_text)
    return (level, text, "#" * level + " " + text)


@st.composite
def headings_list_strategy(draw):
    """Generate a list of markdown headings."""
    headings = draw(st.lists(heading_strategy(), min_size=1, max_size=10))
    return headings


@settings(max_examples=100)
@given(headings=headings_list_strategy())
def test_toc_extraction_correctness(headings):
    """
    Feature: jinpress-rewrite, Property 6: TOC 提取正確性
    Validates: Requirements 4.6

    For any Markdown content containing headings, the extracted TOC structure
    SHALL correctly reflect the heading hierarchy and order.
    """
    processor = MarkdownProcessor()

    # Build markdown content from headings
    content = "\n\n".join(h[2] for h in headings)

    # Extract TOC
    toc = processor.extract_toc(content)

    # Property 1: Number of TOC items SHALL equal number of headings
    assert len(toc) == len(headings), (
        f"TOC count mismatch:\nExpected: {len(headings)}\nGot: {len(toc)}"
    )

    # Property 2: TOC items SHALL preserve heading order
    for i, (level, text, _) in enumerate(headings):
        assert toc[i].level == level, (
            f"Level mismatch at index {i}:\nExpected: {level}\nGot: {toc[i].level}"
        )
        # Note: The processor normalizes whitespace in heading text
        # so we compare stripped versions
        assert toc[i].text == text.strip(), (
            f"Text mismatch at index {i}:\nExpected: {text.strip()}\nGot: {toc[i].text}"
        )

    # Property 3: Each TOC item SHALL have a valid anchor
    for item in toc:
        assert item.anchor, f"Empty anchor for heading: {item.text}"
        # Anchor should be URL-safe (lowercase, no spaces)
        assert item.anchor == item.anchor.lower(), (
            f"Anchor not lowercase: {item.anchor}"
        )
        assert " " not in item.anchor, f"Anchor contains space: {item.anchor}"
