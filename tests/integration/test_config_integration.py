"""Integration tests for configuration module.

These tests verify that the config module works correctly with actual files
and across multiple configuration sources (files, environment variables).
"""

from pathlib import Path

import pytest

from vibe_coding.config import Config, load_env_file


class TestConfigIntegration:
    """Integration tests for configuration loading."""

    def test_load_env_file_reads_from_disk(self, tmp_path):
        """Test that load_env_file reads from actual disk file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_KEY=test_value\nANOTHER_KEY=another_value")

        result = load_env_file(env_file)

        assert result["TEST_KEY"] == "test_value"
        assert result["ANOTHER_KEY"] == "another_value"

    def test_config_reads_from_file_and_env(self, tmp_path, monkeypatch):
        """Test config precedence: env vars > file values."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=file_value\nKEY2=file_value2")

        # Set environment variable
        monkeypatch.setenv("KEY1", "env_value")

        config = Config(env_file)

        # KEY1 should come from environment
        assert config.get("KEY1") == "env_value"
        # KEY2 should come from file
        assert config.get("KEY2") == "file_value2"

    def test_config_with_prefix_reads_correctly(self, tmp_path, monkeypatch):
        """Test that prefix is correctly applied to environment lookups."""
        env_file = tmp_path / ".env"
        env_file.write_text("DATABASE_URL=sqlite:///app.db")

        # Set prefixed environment variable
        monkeypatch.setenv("APP_DATABASE_URL", "postgresql://localhost/app")

        config = Config(env_file, prefix="APP_")

        # Should use prefixed env var
        assert config.get("DATABASE_URL") == "postgresql://localhost/app"

    def test_config_bool_with_environment_override(self, tmp_path, monkeypatch):
        """Test boolean parsing with environment override."""
        env_file = tmp_path / ".env"
        env_file.write_text("DEBUG=false")

        monkeypatch.setenv("DEBUG", "true")

        config = Config(env_file)

        # Should parse environment value
        assert config.get_bool("DEBUG") is True

    def test_config_int_with_environment_override(self, tmp_path, monkeypatch):
        """Test integer parsing with environment override."""
        env_file = tmp_path / ".env"
        env_file.write_text("PORT=3000")

        monkeypatch.setenv("PORT", "8080")

        config = Config(env_file)

        # Should parse environment value
        assert config.get_int("PORT") == 8080

    def test_config_handles_missing_file_gracefully(self, tmp_path):
        """Test that config works even when env file doesn't exist."""
        missing_file = tmp_path / "nonexistent.env"

        config = Config(missing_file)

        # Should return defaults for missing keys
        assert config.get("ANY_KEY", "default") == "default"
        assert config.get_bool("DEBUG", default=True) is True
        assert config.get_int("PORT", default=8080) == 8080

    def test_full_configuration_workflow(self, tmp_path, monkeypatch):
        """Test complete configuration workflow with multiple sources."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
DATABASE_URL=sqlite:///default.db
API_KEY=dev-key-12345
DEBUG=false
PORT=3000
CACHE_ENABLED=true
        """)

        # Override some values with environment
        monkeypatch.setenv("DATABASE_URL", "postgresql://prod-server/db")
        monkeypatch.setenv("DEBUG", "true")

        config = Config(env_file)

        # Verify precedence
        assert config.get("DATABASE_URL") == "postgresql://prod-server/db"
        assert config.get("API_KEY") == "dev-key-12345"
        assert config.get_bool("DEBUG") is True
        assert config.get_int("PORT") == 3000
        assert config.get_bool("CACHE_ENABLED") is True

        # Verify defaults
        assert config.get("MISSING_KEY", "fallback") == "fallback"


class TestConfigWithFixtures:
    """Tests using fixture files."""

    def test_config_from_sample_fixture(self):
        """Test loading config from sample fixture file."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        env_file = fixtures_dir / "sample_config.env"

        if not env_file.exists():
            pytest.skip("sample_config.env fixture not found")

        config = Config(env_file)

        # Verify fixture values
        assert config.get("DATABASE_URL") is not None
        assert config.get("API_KEY") is not None
        assert config.get("DEBUG") in ["true", "false"]
        assert config.get_int("PORT") > 0
