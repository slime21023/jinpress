"""
Logging configuration for JinPress.

Provides centralized logging setup with appropriate levels and formatting.
"""

import logging
import sys


def setup_logging(level: str = "INFO", format_style: str = "simple") -> None:
    """
    Set up logging configuration for JinPress.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_style: Format style ('simple', 'detailed', 'json')
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Choose format based on style
    if format_style == "detailed":
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    elif format_style == "json":
        log_format = (
            '{"timestamp": "%(asctime)s", "logger": "%(name)s", '
            '"level": "%(levelname)s", "file": "%(filename)s", '
            '"line": %(lineno)d, "message": "%(message)s"}'
        )
    else:  # simple
        log_format = "%(levelname)s: %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,  # Override any existing configuration
    )

    # Set specific loggers to appropriate levels
    logging.getLogger("jinpress").setLevel(numeric_level)

    # Suppress noisy third-party loggers
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("markdown_it").setLevel(logging.WARNING)
    logging.getLogger("mdit_py_plugins").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    Change the log level for all JinPress loggers.

    Args:
        level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger("jinpress").setLevel(numeric_level)

    # Also update root logger
    logging.getLogger().setLevel(numeric_level)


def enable_debug_logging() -> None:
    """Enable debug logging for troubleshooting."""
    set_log_level("DEBUG")

    # Also enable debug for some third-party libraries when debugging
    logging.getLogger("watchdog").setLevel(logging.INFO)


def disable_debug_logging() -> None:
    """Disable debug logging and return to INFO level."""
    set_log_level("INFO")

    # Return third-party loggers to WARNING
    logging.getLogger("watchdog").setLevel(logging.WARNING)
