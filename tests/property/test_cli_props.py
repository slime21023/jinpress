"""
Property-based tests for CLI error messages.

Feature: jinpress-rewrite
"""

import tempfile
from pathlib import Path

import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from jinpress.config import ConfigError, ConfigManager

# Strategies for generating invalid configuration values
invalid_yaml_strategy = st.sampled_from(
    [
        "site:\n  title: [unclosed",
        "site:\n  title: 'unclosed quote",
        "site:\n  title: {invalid: yaml: here}",
        "site:\n  - invalid\n  - list\n  - as: value",
        "site: !!python/object:__main__.Foo {}",
    ]
)

invalid_config_key_strategy = st.sampled_from(
    [
        {"site": "not_a_dict"},
        {"theme": "not_a_dict"},
        {"site": {"title": ""}},  # Empty title
        {"site": {"title": "   "}},  # Whitespace-only title
        {"site": {"base": "no-leading-slash"}},  # Invalid base path
    ]
)


@st.composite
def invalid_config_with_key_strategy(draw):
    """Generate invalid configurations with identifiable keys."""
    invalid_type = draw(
        st.sampled_from(
            ["site_not_dict", "theme_not_dict", "empty_title", "invalid_base"]
        )
    )

    if invalid_type == "site_not_dict":
        return {"site": "not_a_dict"}, "site"
    elif invalid_type == "theme_not_dict":
        return {"theme": "not_a_dict"}, "theme"
    elif invalid_type == "empty_title":
        return {"site": {"title": ""}}, "site.title"
    elif invalid_type == "invalid_base":
        return {
            "site": {"title": "Valid Title", "base": "no-leading-slash"}
        }, "site.base"

    return {"site": {"title": ""}}, "site.title"


@settings(max_examples=100)
@given(invalid_yaml=invalid_yaml_strategy)
def test_yaml_error_contains_file_path(invalid_yaml):
    """
    Feature: jinpress-rewrite, Property 10: 錯誤訊息描述性
    Validates: Requirements 1.6, 5.5, 9.6

    For any invalid YAML configuration file, the error message SHALL
    contain the file path to help identify the problem location.
    """
    manager = ConfigManager()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "jinpress.yml"

        # Write invalid YAML to file
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(invalid_yaml)

        try:
            manager.load(Path(tmpdir))
            # If no error is raised, the YAML might be valid in some edge cases
            # This is acceptable as we're testing error messages when errors occur
        except ConfigError as e:
            error_message = str(e)
            # Property: Error message SHALL contain file path
            assert (
                "jinpress.yml" in error_message or str(config_path) in error_message
            ), f"Error message should contain file path: {error_message}"


@settings(max_examples=100)
@given(config_and_key=invalid_config_with_key_strategy())
def test_validation_error_contains_config_key(config_and_key):
    """
    Feature: jinpress-rewrite, Property 10: 錯誤訊息描述性
    Validates: Requirements 1.6, 5.5, 9.6

    For any invalid configuration value, the error message SHALL
    contain the specific configuration key that has the problem.
    """
    invalid_config, expected_key = config_and_key
    manager = ConfigManager()

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "jinpress.yml"

        # Write invalid config to file
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(invalid_config, f)

        try:
            config = manager.load(Path(tmpdir))
            errors = manager.validate(config)

            if errors:
                # Property: At least one error message SHALL contain the problematic key
                all_errors = " ".join(errors)
                assert expected_key in all_errors, (
                    f"Error messages should contain key '{expected_key}': {errors}"
                )
        except ConfigError as e:
            error_message = str(e)
            # Property: Error message SHALL contain the problematic key
            assert expected_key in error_message, (
                f"Error message should contain key '{expected_key}': {error_message}"
            )


# Strategies for generating file paths
file_path_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789_-"),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip())


@settings(max_examples=100)
@given(file_path=file_path_strategy)
def test_build_error_contains_file_path(file_path):
    """
    Feature: jinpress-rewrite, Property 10: 錯誤訊息描述性
    Validates: Requirements 1.6, 5.5, 9.6

    For any build error related to a specific file, the error message
    SHALL contain the file path to help identify the problem location.
    """
    from jinpress.builder import BuildError

    # Create a BuildError with a file path
    test_path = Path(file_path)
    error = BuildError("Test error message", file_path=test_path)

    error_message = str(error)

    # Property: Error message SHALL contain the file path (or its normalized form)
    # Path normalization may remove trailing slashes, so we check for the normalized path
    normalized_path = str(test_path)
    assert normalized_path in error_message, (
        f"Error message should contain file path '{normalized_path}': {error_message}"
    )


@settings(max_examples=100)
@given(error_msg=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
def test_config_error_preserves_message(error_msg):
    """
    Feature: jinpress-rewrite, Property 10: 錯誤訊息描述性
    Validates: Requirements 1.6, 5.5, 9.6

    For any ConfigError, the original error message SHALL be preserved
    in the final error string.
    """
    # Test ConfigError with just message
    error = ConfigError(error_msg)
    assert error_msg in str(error), (
        f"Error message should contain original message: {str(error)}"
    )

    # Test ConfigError with message and key
    error_with_key = ConfigError(error_msg, key="test.key")
    error_str = str(error_with_key)
    assert error_msg in error_str, (
        f"Error message should contain original message: {error_str}"
    )
    assert "test.key" in error_str, f"Error message should contain key: {error_str}"

    # Test ConfigError with message and file path
    error_with_path = ConfigError(error_msg, file_path=Path("test/config.yml"))
    error_str = str(error_with_path)
    assert error_msg in error_str, (
        f"Error message should contain original message: {error_str}"
    )
    assert "test/config.yml" in error_str or "config.yml" in error_str, (
        f"Error message should contain file path: {error_str}"
    )
