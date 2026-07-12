"""Configuration settings for Edgebook.

This module uses Pydantic Settings to load environment configuration
from variables and optional .env files.
"""

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev-secret-key-change-in-production"
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    """Application settings class."""

    PROJECT_NAME: str = "Edgebook"
    SECRET_KEY: str = Field(
        default=DEV_SECRET_KEY,
        description="Secret key for JWT signing",
    )
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
    INGESTION_MIN_QUOTA_REMAINING: int = Field(default=100, ge=0)
    ODDS_API_REGIONS: str = "us"
    ODDS_API_BOOKMAKERS: str = "draftkings,fanduel,betmgm,caesars"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def _enforce_production_hardening(self) -> "Settings":
        """Fail fast when production secrets are missing or insecure.

        Hosting the app with the placeholder secret would let an attacker
        forge JWTs, so this guard refuses to construct a ``Settings``
        instance in the ``production`` environment unless a strong key is
        provided.
        """
        if self.ENV != "production":
            return self

        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production")

        if self.SECRET_KEY == DEV_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be changed from the default value in production"
            )

        if len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} "
                "characters in production"
            )

        return self


settings = Settings()
