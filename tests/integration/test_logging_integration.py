"""Integration tests for logging module.

These tests verify that logging works correctly with actual file output
and across different configuration scenarios.
"""

import logging

import pytest

from vibe_coding.utils.logging import get_logger, setup_logging


class TestLoggingIntegration:
    """Integration tests for logging configuration."""

    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging properly configures handlers."""
        # Clear any existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers = []

        setup_logging(level="INFO")

        # Verify handlers exist
        assert len(root_logger.handlers) > 0
        assert root_logger.level == logging.INFO

    def test_setup_logging_with_file_output(self, tmp_path):
        """Test logging to actual file."""
        log_file = tmp_path / "test.log"

        setup_logging(level="INFO", log_file=log_file)
        logger = get_logger("test_integration")
        test_message = "Test log message"
        logger.info(test_message)

        # Close handlers to ensure file is written
        for handler in logging.getLogger().handlers:
            handler.close()
            logging.getLogger().removeHandler(handler)

        # Verify log file was created and contains message
        assert log_file.exists()
        log_content = log_file.read_text()
        assert test_message in log_content

    def test_get_logger_returns_configured_logger(self):
        """Test that get_logger returns properly configured logger."""
        setup_logging(level="DEBUG")
        logger = get_logger("test.module")

        assert logger.name == "test.module"
        assert logger.level == logging.NOTSET  # Inherits from root
        assert logger.parent.level == logging.DEBUG

    def test_log_levels_respected(self, tmp_path):
        """Test that different log levels work correctly."""
        log_file = tmp_path / "level_test.log"

        setup_logging(level="WARNING", log_file=log_file)
        logger = get_logger("level_test")

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Close handlers
        for handler in logging.getLogger().handlers:
            handler.close()
            logging.getLogger().removeHandler(handler)

        # Verify file content
        content = log_file.read_text()
        assert "Debug message" not in content  # Should not appear (level=WARNING)
        assert "Info message" not in content  # Should not appear (level=WARNING)
        assert "Warning message" in content
        assert "Error message" in content

    def test_custom_format_applied(self, tmp_path):
        """Test that custom format is applied to logs."""
        log_file = tmp_path / "format_test.log"
        custom_format = "%(levelname)s - %(message)s"

        setup_logging(level="INFO", log_file=log_file, format_string=custom_format)
        logger = get_logger("format_test")
        logger.info("Formatted message")

        # Close handlers
        for handler in logging.getLogger().handlers:
            handler.close()
            logging.getLogger().removeHandler(handler)

        content = log_file.read_text()
        # Should have our custom format
        assert "INFO - Formatted message" in content

    def test_multiple_loggers_work_independently(self, tmp_path):
        """Test that multiple loggers can write to same file."""
        log_file = tmp_path / "multi.log"

        setup_logging(level="INFO", log_file=log_file)
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        logger1.info("Message from logger1")
        logger2.info("Message from logger2")

        # Close handlers
        for handler in logging.getLogger().handlers:
            handler.close()
            logging.getLogger().removeHandler(handler)

        content = log_file.read_text()
        assert "module1" in content
        assert "module2" in content
        assert "Message from logger1" in content
        assert "Message from logger2" in content

    @pytest.mark.skip(reason="Complex logging setup with caplog")  # noqa: F821
    def test_logging_to_console_only(self, caplog):
        """Test that logging to console works (using pytest caplog)."""
        # Clear any existing handlers first
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

        setup_logging(level="INFO")

        # Reconfigure caplog to capture our logger
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="console_test"):
            logger = get_logger("console_test")
            logger.info("Console test message")

        assert "Console test message" in caplog.text
