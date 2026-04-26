"""Runtime settings loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AnyUrl, BaseModel, Field, TypeAdapter

DEFAULT_NHTSA_API_BASE_URL = "https://api.nhtsa.gov"
_ANY_URL_ADAPTER: TypeAdapter[AnyUrl] = TypeAdapter(AnyUrl)


def parse_any_url(value: str) -> AnyUrl:
    """Parse a URL string into Pydantic's AnyUrl type."""
    return _ANY_URL_ADAPTER.validate_python(value)


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    environment: str = Field(default="local")
    log_level: str = Field(default="INFO")
    nhtsa_api_base_url: AnyUrl = Field(
        default_factory=lambda: parse_any_url(DEFAULT_NHTSA_API_BASE_URL)
    )
    nhtsa_api_timeout_seconds: float = Field(default=30.0, gt=0)
    database_url: str = Field(default="")

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "Settings":
        """Build settings from process environment and an optional .env file."""
        load_dotenv(env_file)
        return cls(
            environment=os.getenv("ENVIRONMENT", "local"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            nhtsa_api_base_url=parse_any_url(
                os.getenv("NHTSA_API_BASE_URL", DEFAULT_NHTSA_API_BASE_URL)
            ),
            nhtsa_api_timeout_seconds=float(os.getenv("NHTSA_API_TIMEOUT_SECONDS", "30")),
            database_url=os.getenv("DATABASE_URL", ""),
        )
