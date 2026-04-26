"""HTTP client for NHTSA public APIs."""

import time
from collections.abc import Callable, Mapping
from typing import Any, cast

import httpx

from nhtsa_pipeline.config.settings import Settings
from nhtsa_pipeline.models.nhtsa import NhtsaApiResponse, NhtsaRecallsResponse


class NhtsaApiError(RuntimeError):
    """Raised when the NHTSA API returns an unsuccessful response."""


class NhtsaRateLimitError(NhtsaApiError):
    """Raised when the NHTSA API keeps returning rate-limit responses."""


class NhtsaServerError(NhtsaApiError):
    """Raised when the NHTSA API returns a server-side error."""


class NhtsaClient:
    """Small typed wrapper around NHTSA public API endpoints."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.Client | None = None,
        *,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings or Settings.from_env()
        self._max_retries: int = max_retries
        self._retry_backoff_seconds: float = retry_backoff_seconds
        self._sleep: Callable[[float], None] = sleep
        self._owns_client: bool = client is None
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
    ) -> NhtsaRecallsResponse:
        """Fetch recall records for a specific make, model, and model year."""
        payload = self.get_json(
            "/recalls/recallsByVehicle",
            params={"make": make, "model": model, "modelYear": model_year},
        )
        return NhtsaRecallsResponse.model_validate(payload)

    def get(
        self,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
    ) -> NhtsaApiResponse:
        """Fetch a NHTSA endpoint and validate the standard response envelope."""
        payload = self.get_json(path, params=params)
        return NhtsaApiResponse.model_validate(payload)

    def get_json(
        self,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
    ) -> dict[str, Any]:
        """Fetch a NHTSA endpoint and return the decoded JSON body."""
        response = self._get_with_retries(path, params=params)
        return cast(dict[str, Any], response.json())

    def _get_with_retries(
        self,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
    ) -> httpx.Response:
        for attempt in range(self._max_retries + 1):
            response = self._client.get(path, params=params)
            if response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                if attempt < self._max_retries:
                    self._sleep(self._retry_delay(response, attempt))
                    continue
                message = "NHTSA API rate limit exceeded after retries with status 429"
                raise NhtsaRateLimitError(message)

            if response.status_code >= httpx.codes.INTERNAL_SERVER_ERROR:
                message = f"NHTSA API server error with status {response.status_code}"
                raise NhtsaServerError(message)

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                message = f"NHTSA API request failed with status {exc.response.status_code}"
                raise NhtsaApiError(message) from exc

            return response

        message = "NHTSA API request failed before a response could be returned"
        raise NhtsaApiError(message)

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = cast(str | None, response.headers.get("Retry-After"))
        if retry_after is not None:
            try:
                parsed_retry_after = float(retry_after)
                return max(parsed_retry_after, 0.0)
            except ValueError:
                pass

        fallback_delay = self._retry_backoff_seconds * (2.0**attempt)
        return float(fallback_delay)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "NhtsaClient":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()
