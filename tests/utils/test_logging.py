"""Test cases for the logging utility."""

from edgebook.utils.logging import logger


def test_logger_name():
    assert logger.name == "edgebook"
