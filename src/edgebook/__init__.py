"""Edgebook - College football paper-betting platform."""

__version__ = "0.1.0"

from edgebook.core.config import settings
from edgebook.utils.logging import get_logger, setup_logging

__all__ = [
    "settings",
    "get_logger",
    "setup_logging",
]
