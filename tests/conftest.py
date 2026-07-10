"""Test fixtures and utilities for the project.

This module provides pytest fixtures and utilities for testing.
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_env_file(temp_dir):
    """Create a sample .env file for testing."""
    env_path = temp_dir / ".env"
    env_path.write_text("""
# Test configuration
DATABASE_URL=postgresql://localhost/test
API_KEY=test-api-key-12345
DEBUG=true
PORT=8080
""")
    return env_path


@pytest.fixture
def empty_env_file(temp_dir):
    """Create an empty .env file for testing."""
    env_path = temp_dir / ".env"
    env_path.write_text("")
    return env_path


@pytest.fixture
def clean_config():
    """Provide a fresh Config instance for testing.

    This fixture clears any cached configuration to ensure
    tests don't interfere with each other.
    """
    # Clear any cached config
    import vibe_coding.config

    vibe_coding.config._config_instance = None
    yield
    # Clean up after test
    vibe_coding.config._config_instance = None
