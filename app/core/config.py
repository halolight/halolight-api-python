"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App settings
    APP_NAME: str = "HaloLight API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "production", "test"] = "development"

    # API settings
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database settings
    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL."""
        if not v:
            raise ValueError("DATABASE_URL is required")
        # Accept any valid database URL (PostgreSQL, SQLite, etc.)
        # PostgreSQL for production, SQLite for testing
        valid_schemes = [
            "postgresql://",
            "postgresql+",
            "postgres://",
            "sqlite://",
        ]
        if not any(v.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(f"DATABASE_URL must start with one of: {', '.join(valid_schemes)}")
        return v

    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    JWT_REFRESH_SECRET_KEY: str | None = None  # Falls back to JWT_SECRET_KEY
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days

    # Security
    PASSWORD_MIN_LENGTH: int = 8  # Match API spec (minimum 8 characters)

    # File upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_PATH: str = "./uploads"

    # Rate limiting
    THROTTLE_TTL: int = 60  # seconds
    THROTTLE_LIMIT: int = 100  # requests per TTL


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
