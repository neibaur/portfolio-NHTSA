"""Pydantic schemas for NHTSA API responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NhtsaApiResponse(BaseModel):
    """Standard response envelope returned by many NHTSA endpoints."""

    model_config = ConfigDict(extra="allow")

    count: int = Field(alias="Count", ge=0)
    message: str = Field(alias="Message", default="")
    results: list[dict[str, Any]] = Field(alias="Results", default_factory=list)


class NhtsaRecall(BaseModel):
    """Validated recall record returned by the NHTSA recalls API."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    campaign_number: str = Field(alias="NHTSACampaignNumber", min_length=1)
    manufacturer: str = Field(alias="Manufacturer", min_length=1)
    subject: str | None = Field(alias="Subject", default=None)
    component: str = Field(alias="Component", min_length=1)
    summary: str = Field(alias="Summary", min_length=1)
    consequence: str = Field(alias="Consequence", min_length=1)
    remedy: str = Field(alias="Remedy", min_length=1)
    report_received_date: str = Field(alias="ReportReceivedDate", min_length=1)
    notes: str | None = Field(alias="Notes", default=None)
    make: str | None = Field(alias="Make", default=None)
    model: str | None = Field(alias="Model", default=None)
    model_year: int | None = Field(alias="ModelYear", default=None)
    park_it: bool | None = Field(alias="parkIt", default=None)
    park_outside: bool | None = Field(alias="parkOutSide", default=None)


class NhtsaRecallsResponse(BaseModel):
    """Validated response envelope for NHTSA vehicle recall lookups."""

    model_config = ConfigDict(extra="allow")

    count: int = Field(alias="Count", ge=0)
    message: str = Field(alias="Message", default="")
    results: list[NhtsaRecall] = Field(alias="Results", default_factory=list)
