"""Tests for configuration module.

This module tests the configuration management functionality.
"""

from vibe_coding.config import Config, load_env_file


class TestLoadEnvFile:
    """Tests for load_env_file function."""

    def test_loads_simple_variables(self, temp_dir):
        """Test loading simple key-value pairs."""
        env_path = temp_dir / ".env"
        env_path.write_text("KEY1=value1\nKEY2=value2")

        result = load_env_file(env_path)

        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_ignores_comments(self, temp_dir):
        """Test that comment lines are ignored."""
        env_path = temp_dir / ".env"
        env_path.write_text("# This is a comment\nKEY=value\n  # Another comment")

        result = load_env_file(env_path)

        assert result == {"KEY": "value"}

    def test_ignores_empty_lines(self, temp_dir):
        """Test that empty lines are ignored."""
        env_path = temp_dir / ".env"
        env_path.write_text("\nKEY1=value1\n\nKEY2=value2\n")

        result = load_env_file(env_path)

        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_strips_quotes(self, temp_dir):
        """Test that quotes are stripped from values."""
        env_path = temp_dir / ".env"
        env_path.write_text("KEY1=\"quoted value\"\nKEY2='single quotes'")

        result = load_env_file(env_path)

        assert result["KEY1"] == "quoted value"
        assert result["KEY2"] == "single quotes"

    def test_returns_empty_for_missing_file(self):
        """Test that missing files return empty dict."""
        result = load_env_file("/nonexistent/path/.env")

        assert result == {}


class TestConfig:
    """Tests for Config class."""

    def test_get_from_env_file(self, sample_env_file, clean_config):
        """Test getting values from env file."""
        config = Config(sample_env_file)

        assert config.get("DATABASE_URL") == "postgresql://localhost/test"
        assert config.get("API_KEY") == "test-api-key-12345"

    def test_get_default_value(self, empty_env_file, clean_config):
        """Test that defaults work when key not found."""
        config = Config(empty_env_file)

        assert config.get("MISSING_KEY", "default") == "default"

    def test_get_bool_parses_true_values(self, temp_dir, clean_config):
        """Test boolean parsing for true values."""
        env_path = temp_dir / ".env"
        env_path.write_text(
            "\n".join(
                [
                    "TRUE1=true",
                    "TRUE2=TRUE",
                    "TRUE3=1",
                    "TRUE4=yes",
                    "TRUE5=on",
                ]
            )
        )
        config = Config(env_path)

        assert config.get_bool("TRUE1") is True
        assert config.get_bool("TRUE2") is True
        assert config.get_bool("TRUE3") is True
        assert config.get_bool("TRUE4") is True
        assert config.get_bool("TRUE5") is True

    def test_get_bool_returns_default(self, empty_env_file, clean_config):
        """Test boolean default value."""
        config = Config(empty_env_file)

        assert config.get_bool("MISSING", default=True) is True
        assert config.get_bool("MISSING", default=False) is False

    def test_get_int_parses_numbers(self, temp_dir, clean_config):
        """Test integer parsing."""
        env_path = temp_dir / ".env"
        env_path.write_text("PORT=8080")
        config = Config(env_path)

        assert config.get_int("PORT") == 8080

    def test_get_int_returns_default_on_error(self, temp_dir, clean_config):
        """Test that invalid integers return default."""
        env_path = temp_dir / ".env"
        env_path.write_text("PORT=not_a_number")
        config = Config(env_path)

        assert config.get_int("PORT", default=3000) == 3000

    def test_environment_overrides_file(self, temp_dir, clean_config, monkeypatch):
        """Test that environment variables override file values."""
        env_path = temp_dir / ".env"
        env_path.write_text("KEY=from_file")
        monkeypatch.setenv("KEY", "from_env")

        config = Config(env_path)

        assert config.get("KEY") == "from_env"

    def test_prefix_works(self, temp_dir, clean_config, monkeypatch):
        """Test that prefix is applied to environment lookups."""
        env_path = temp_dir / ".env"
        env_path.write_text("KEY=from_file")
        monkeypatch.setenv("APP_KEY", "from_prefixed_env")

        config = Config(env_path, prefix="APP_")

        assert config.get("KEY") == "from_prefixed_env"

    def test_default_env_file_location(self, clean_config, monkeypatch):
        """Test default location for .env file."""
        # Should not raise even if default file doesn't exist
        config = Config()  # No env_file specified

        assert config.get("ANY_KEY", "default") == "default"


class TestConfigIntegration:
    """Integration tests for configuration."""

    def test_full_workflow(self, temp_dir, clean_config, monkeypatch):
        """Test complete configuration workflow."""
        # Setup env file
        env_path = temp_dir / ".env"
        env_path.write_text("""
DATABASE_URL=sqlite:///default.db
DEBUG=false
PORT=3000
        """)

        # Override one value with environment
        monkeypatch.setenv("PORT", "8080")

        config = Config(env_path)

        # Verify file values
        assert config.get("DATABASE_URL") == "sqlite:///default.db"

        # Verify environment override
        assert config.get("PORT") == "8080"
        assert config.get_int("PORT") == 8080

        # Verify defaults
        assert config.get("MISSING_KEY", "fallback") == "fallback"
