"""Application configuration using pydantic-settings."""
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    OPENAI_API_KEY: str = "sk-placeholder"
    OPENWEATHER_API_KEY: str = ""
    GOOGLE_PLACES_API_KEY: str = ""
    LOG_LEVEL: str = "INFO"

    @property
    def log_level(self) -> int:
        """Return numeric log level."""
        return getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)


settings = Settings()
