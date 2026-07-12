"""Configuration settings for Edgebook.

This module uses Pydantic Settings to load environment configuration
from variables and optional .env files.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings class."""

    PROJECT_NAME: str = "Edgebook"
    DATABASE_URL: str = Field(
        default="sqlite:///./edgebook.db", description="Database connection URL"
    )
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    INGESTION_MIN_PROVIDERS: int = 3
    INGESTION_PROVIDER_NAMES: str = ""
    ODDS_API_KEY: str = ""
    SPORTSDATAIO_API_KEY: str = ""
    COLLEGE_FOOTBALL_DATA_API_KEY: str = ""
    INGESTION_HTTP_TIMEOUT_SECONDS: float = Field(default=10.0, gt=0, le=60)
    INGESTION_HTTP_MAX_RETRIES: int = Field(default=2, ge=0, le=5)
    ODDS_API_REGIONS: str = "us"
    ODDS_API_BOOKMAKERS: str = ""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
