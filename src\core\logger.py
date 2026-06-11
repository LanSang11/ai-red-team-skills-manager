"""Logging setup using loguru singleton pattern.

Usage:
    from src.core.logger import setup_logging, get_logger

    # Call once at startup
    setup_logging(log_file="path/to/log", debug=False)

    # Anywhere else
    logger = get_logger()
    logger.info("Hello")
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger as _loguru_logger


_configured = False


def setup_logging(
    log_file: Optional[str] = None,
    debug: bool = False,
):
    """Configure the global loguru logger. Safe to call multiple times (idempotent).

    Args:
        log_file: Path to log file. None to disable file logging.
        debug: Enable DEBUG level on console.

    Returns:
        The configured loguru logger instance.
    """
    global _configured
    if _configured:
        return _loguru_logger

    _loguru_logger.remove()

    level = "DEBUG" if debug else "INFO"
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Console handler
    _loguru_logger.add(sys.stderr, format=fmt, level=level, colorize=True)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _loguru_logger.add(
            str(log_path),
            format=fmt,
            level="DEBUG",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )

    _configured = True
    return _loguru_logger


def get_logger():
    """Get the configured loguru logger.

    If setup_logging() hasn't been called yet, returns the default loguru logger.
    """
    return _loguru_logger
