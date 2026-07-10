"""Configuration management for Vibe Coding projects.

This module provides a simple, consistent way to load and manage configuration
settings. It supports both environment variables and configuration files.

Example usage:
    >>> from vibe_coding.config import get_config
    >>> config = get_config()
    >>> database_url = config.get('DATABASE_URL', 'sqlite:///default.db')
"""

import os
from pathlib import Path
from typing import Any


def load_env_file(filepath: Path | str) -> dict[str, str]:
    """Load environment variables from a .env file.

    Args:
        filepath: Path to the .env file

    Returns:
        Dictionary of key-value pairs from the file

    Example:
        >>> env_vars = load_env_file('.env')
        >>> print(env_vars.get('API_KEY'))
    """
    env_vars = {}
    filepath = Path(filepath)

    if not filepath.exists():
        return env_vars

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip().strip("\"'")

    return env_vars


class Config:
    """Configuration manager that reads from environment and config files.

    This class provides a unified interface for accessing configuration values
    from multiple sources with priority: environment variables > config files

    Attributes:
        env_file: Path to the .env file to load
        prefix: Optional prefix for environment variables
    """

    def __init__(self, env_file: Path | str | None = None, prefix: str = ""):
        """Initialize configuration manager.

        Args:
            env_file: Path to .env file (default: .env in project root)
            prefix: Optional prefix for environment variables
        """
        self.prefix = prefix
        self._config = {}

        # Default to .env in project root
        if env_file is None:
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
        else:
            env_file = Path(env_file)

        # Load from .env file
        self._config.update(load_env_file(env_file))

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Checks in order:
        1. Environment variable with prefix (if set)
        2. Environment variable without prefix
        3. Config file value
        4. Default value

        Args:
            key: Configuration key name
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config = Config()
            >>> value = config.get('DATABASE_URL', 'sqlite:///default.db')
        """
        # Check environment with prefix first
        if self.prefix:
            env_key = f"{self.prefix}{key}"
            if env_value := os.getenv(env_key):
                return env_value

        # Check environment without prefix
        if env_value := os.getenv(key):
            return env_value

        # Check config file
        if key in self._config:
            return self._config[key]

        return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value.

        Args:
            key: Configuration key name
            default: Default boolean value

        Returns:
            Boolean value (True for 'true', '1', 'yes', 'on')

        Example:
            >>> debug = config.get_bool('DEBUG', False)
        """
        value = self.get(key, str(default).lower())
        return value.lower() in ("true", "1", "yes", "on")

    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value.

        Args:
            key: Configuration key name
            default: Default integer value

        Returns:
            Integer value or default if conversion fails

        Example:
            >>> port = config.get_int('PORT', 8080)
        """
        try:
            return int(self.get(key, default))
        except (ValueError, TypeError):
            return default


# Global config instance for convenience
_config_instance: Config | None = None


def get_config(env_file: Path | str | None = None, prefix: str = "") -> Config:
    """Get the global configuration instance.

    This function returns a singleton Config instance for convenience.

    Args:
        env_file: Path to .env file
        prefix: Optional prefix for environment variables

    Returns:
        Config instance

    Example:
        >>> config = get_config()
        >>> value = config.get('API_KEY')
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(env_file, prefix)
    return _config_instance
