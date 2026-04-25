"""Pydantic schemas for NHTSA API responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NhtsaApiResponse(BaseModel):
    """Standard response envelope returned by many NHTSA endpoints."""

    model_config = ConfigDict(extra="allow")

    count: int = Field(alias="Count", ge=0)
    message: str = Field(alias="Message", default="")
    results: list[dict[str, Any]] = Field(alias="Results", default_factory=list)
