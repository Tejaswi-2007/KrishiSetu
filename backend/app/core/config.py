"""Application configuration using pydantic-settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "KrishiSetu"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:digimandi_dev_2024@localhost:5432/digimandi"
    DATABASE_TEST_URL: str = "postgresql://postgres:digimandi_dev_2024@localhost:5432/digimandi_test"

    # Security
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # File uploads
    UPLOAD_DIR: str = "./storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Video conferencing
    JITSI_DOMAIN: str = "meet.jit.si"
    JITSI_APP_ID: str = ""
    JITSI_APP_SECRET: str = ""

    # Market price sources
    AGMARKNET_BASE_URL: str = "https://agmarknet.gov.in"
    DATA_GOV_IN_API_KEY: str = ""

    # Email (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@digimandi.in"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
