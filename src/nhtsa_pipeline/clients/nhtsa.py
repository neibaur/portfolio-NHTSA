"""HTTP client for NHTSA public APIs."""

from collections.abc import Mapping
from typing import Any

import httpx

from nhtsa_pipeline.config.settings import Settings
from nhtsa_pipeline.models.nhtsa import NhtsaApiResponse


class NhtsaApiError(RuntimeError):
    """Raised when the NHTSA API returns an unsuccessful response."""


class NhtsaClient:
    """Small typed wrapper around NHTSA public API endpoints."""

    def __init__(self, settings: Settings | None = None, client: httpx.Client | None = None) -> None:
        self._settings = settings or Settings.from_env()
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=str(self._settings.nhtsa_api_base_url),
            timeout=self._settings.nhtsa_api_timeout_seconds,
        )

    def get_recalls_by_vehicle(
        self,
        *,
        make: str,
        model: str,
        model_year: int,
    ) -> NhtsaApiResponse:
        """Fetch recall records for a specific make, model, and model year."""
        return self.get(
            "/recalls/recallsByVehicle",
            params={"make": make, "model": model, "modelYear": model_year},
        )

    def get(
        self,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
    ) -> NhtsaApiResponse:
        """Fetch a NHTSA endpoint and validate the standard response envelope."""
        response = self._client.get(path, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            message = f"NHTSA API request failed with status {exc.response.status_code}"
            raise NhtsaApiError(message) from exc

        payload: dict[str, Any] = response.json()
        return NhtsaApiResponse.model_validate(payload)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "NhtsaClient":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()
