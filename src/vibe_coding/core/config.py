"""
Configuration for the project.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Project settings.
    """

    # Example setting
    PROJECT_NAME: str = "Vibe Coding Data Science Template"


settings = Settings()
