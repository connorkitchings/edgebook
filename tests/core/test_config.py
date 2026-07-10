"""
Test cases for the core configuration.
"""

from vibe_coding.core.config import settings


def test_project_name():
    assert settings.PROJECT_NAME == "Vibe Coding Data Science Template"
