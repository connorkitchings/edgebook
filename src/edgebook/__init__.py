"""Edgebook - College football paper-betting platform."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("edgebook")
except PackageNotFoundError:  # pragma: no cover - source checkout without install
    __version__ = "0.0.0+dev"

from edgebook.core.config import settings
from edgebook.utils.logging import get_logger, setup_logging

__all__ = [
    "__version__",
    "settings",
    "get_logger",
    "setup_logging",
]
