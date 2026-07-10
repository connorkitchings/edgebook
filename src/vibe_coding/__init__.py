"""Vibe Coding - AI-assisted development template.

This package provides utilities and patterns for AI-assisted development projects.

Example:
    >>> from vibe_coding import config
    >>> cfg = config.get_config()
    >>> value = cfg.get('KEY', 'default')
"""

__version__ = "0.1.0"

from vibe_coding.config import Config, get_config, load_env_file
from vibe_coding.utils.logging import get_logger, setup_logging

__all__ = [
    "Config",
    "get_config",
    "load_env_file",
    "get_logger",
    "setup_logging",
]
