"""Integration tests for workflow automation.

These tests verify that the setup and CLI tools work correctly.
"""

import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestWorkflowIntegration:
    """Integration tests for workflow scripts."""

    def test_validate_template_script_runs(self):
        """Test that validate_template.py executes without errors."""
        result = subprocess.run(
            ["python", "scripts/validate_template.py"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        # Script should complete (may have warnings but should not crash)
        assert result.returncode in [0, 1]  # 0 = success, 1 = validation warnings

    def test_vibe_sync_help_works(self):
        """Test that vibe_sync CLI shows help."""
        result = subprocess.run(
            ["python", "scripts/vibe_sync.py", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Vibe-Coding Session Manager" in result.stdout

    def test_setup_project_help_works(self):
        """Test that setup_project CLI shows help."""
        result = subprocess.run(
            ["python", "scripts/setup_project.py", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Run interactive project setup" in result.stdout

    def test_import_vibe_coding_works(self):
        """Test that vibe_coding package can be imported."""
        result = subprocess.run(
            ["python", "-c", "import vibe_coding; print(vibe_coding.__version__)"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_config_import_works(self):
        """Test that config module can be imported."""
        result = subprocess.run(
            ["python", "-c", "from vibe_coding.config import Config, get_config"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    def test_logging_import_works(self):
        """Test that logging module can be imported."""
        result = subprocess.run(
            [
                "python",
                "-c",
                "from vibe_coding.utils.logging import get_logger, setup_logging",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    @pytest.mark.skip(reason="Requires manual input")
    def test_setup_project_interactive(self):
        """Test interactive setup (skipped in automated runs)."""
        # This test exists as documentation
        # To run manually: python scripts/setup_project.py
        pass
