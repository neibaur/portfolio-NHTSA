"""Runtime settings loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AnyUrl, BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    environment: str = Field(default="local")
    log_level: str = Field(default="INFO")
    nhtsa_api_base_url: AnyUrl = Field(default="https://api.nhtsa.gov")
    nhtsa_api_timeout_seconds: float = Field(default=30.0, gt=0)
    database_url: str = Field(default="")

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "Settings":
        """Build settings from process environment and an optional .env file."""
        load_dotenv(env_file)
        return cls(
            environment=os.getenv("ENVIRONMENT", "local"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            nhtsa_api_base_url=os.getenv("NHTSA_API_BASE_URL", "https://api.nhtsa.gov"),
            nhtsa_api_timeout_seconds=float(os.getenv("NHTSA_API_TIMEOUT_SECONDS", "30")),
            database_url=os.getenv("DATABASE_URL", ""),
        )
