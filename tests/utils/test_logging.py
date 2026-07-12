"""Test cases for logging utilities, including JSON format and rotation."""

from __future__ import annotations

import json
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pytest

from edgebook.core.config import settings
from edgebook.utils.logging import JSONFormatter, get_logger, logger, setup_logging


def test_logger_name() -> None:
    """Default logger should have the correct package name."""
    assert logger.name == "edgebook"


def test_json_formatter_formatting() -> None:
    """JSONFormatter should serialize log records to a single-line JSON string."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=10,
        msg="Test message with args %s",
        args=("hello",),
        exc_info=None,
    )

    formatted_str = formatter.format(record)
    data = json.loads(formatted_str)

    assert "timestamp" in data
    assert data["name"] == "test_logger"
    assert data["level"] == "INFO"
    assert data["message"] == "Test message with args hello"
    assert "exception" not in data


def test_json_formatter_exception_capture() -> None:
    """JSONFormatter should format exceptions correctly into the JSON payload."""
    formatter = JSONFormatter()
    try:
        raise ValueError("Simulated error")
    except ValueError:
        import sys

        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test_error",
        level=logging.ERROR,
        pathname="test_file.py",
        lineno=20,
        msg="An error occurred",
        args=(),
        exc_info=exc_info,
    )

    formatted_str = formatter.format(record)
    data = json.loads(formatted_str)

    assert data["level"] == "ERROR"
    assert data["message"] == "An error occurred"
    assert "exception" in data
    assert "ValueError: Simulated error" in data["exception"]


def test_setup_logging_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """setup_logging should configure JSON logging to stdout in production."""
    # Mock settings.ENV to production
    monkeypatch.setattr(settings, "ENV", "production")

    setup_logging(level="INFO")

    root_logger = logging.getLogger()
    assert len(root_logger.handlers) >= 1

    # The first handler (StreamHandler) should have a JSONFormatter
    console_handler = root_logger.handlers[0]
    assert isinstance(console_handler.formatter, JSONFormatter)


def test_setup_logging_file_rotation(tmp_path: Path) -> None:
    """setup_logging should add TimedRotatingFileHandler when log_file is set."""
    log_file_path = tmp_path / "logs" / "edgebook_rotate.log"

    # Configure logging
    setup_logging(level="INFO", log_file=log_file_path)

    root_logger = logging.getLogger()

    # Check that a TimedRotatingFileHandler was added
    file_handlers = [
        h for h in root_logger.handlers if isinstance(h, TimedRotatingFileHandler)
    ]
    assert len(file_handlers) == 1

    handler = file_handlers[0]
    assert handler.baseFilename == str(log_file_path.resolve())
    assert handler.when == "MIDNIGHT"
    assert handler.backupCount == 7

    # Log a message and check it writes to the file
    test_logger = get_logger("test_rotate")
    test_logger.info("Verifying file output writes correctly")

    # Close handlers to release file locks (important on Windows/macOS)
    for h in root_logger.handlers:
        h.close()

    assert log_file_path.exists()
    content = log_file_path.read_text(encoding="utf-8")
    assert "test_rotate - INFO - Verifying file output writes correctly" in content
