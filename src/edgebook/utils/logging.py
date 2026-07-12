"""Logging utilities for Edgebook.

Example usage:
    >>> from edgebook.utils.logging import setup_logging, get_logger
    >>> setup_logging()
    >>> logger = get_logger(__name__)
    >>> logger.info("Application started")
"""

import json
import logging
import sys
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for production log indexing."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    log_file: Path | str | None = None,
    format_string: str | None = None,
) -> None:
    """Configure logging for the application.

    Sets up logging to both console and optional rotating file output.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        format_string: Custom format string (uses default if None)
    """
    from edgebook.core.config import settings

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers: list[logging.Handler] = []

    # Console output StreamHandler
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.ENV == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(format_string))
    handlers.append(console_handler)

    # Rotated file output handler
    if log_file:
        from logging.handlers import TimedRotatingFileHandler

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = TimedRotatingFileHandler(
            filename=str(log_path),
            when="MIDNIGHT",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing data")
    """
    return logging.getLogger(name)


# Default logger instance
logger = get_logger("edgebook")
