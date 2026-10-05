"""
Logging setup using Python's standard logging library with console and rotating file support.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_initialized = False


def setup_logger(
    name: str = "app",
    log_level: str = "INFO",
    log_file: Optional[str] = "logs/crawler.log",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> logging.Logger:
    """
    Configures and returns the central logger instance.

    Args:
        name: Name of the logger.
        log_level: Severity level (DEBUG, INFO, WARNING, ERROR).
        log_file: Path to rotating log file.
        max_bytes: Max size before rotation.
        backup_count: Number of rotated backups.

    Returns:
        Configured logger instance.
    """
    global _initialized
    logger = logging.getLogger(name)

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    if _initialized and logger.handlers:
        return logger

    logger.handlers.clear()

    # Console formatter
    console_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_format)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_format = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s [%(filename)s:%(lineno)d] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler = RotatingFileHandler(
                filename=str(log_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(file_format)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not initialize file logging: {e}")

    logger.propagate = False
    _initialized = True
    return logger


def get_logger(module_name: Optional[str] = None) -> logging.Logger:
    """Returns a named logger child of the main application logger."""
    base_name = "app"
    if module_name:
        return logging.getLogger(f"{base_name}.{module_name}")
    return logging.getLogger(base_name)
