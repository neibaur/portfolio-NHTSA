"""Tests for the NHTSA API client."""

from typing import Any, Protocol

import httpx
import pytest

from nhtsa_pipeline.clients.nhtsa import NhtsaApiError, NhtsaClient
from nhtsa_pipeline.config.settings import Settings


class MockRouter(Protocol):
    """Small protocol for the subset of respx used in these tests."""

    def get(self, url: str) -> Any:
        """Register a mocked GET route."""


def test_get_recalls_by_vehicle_validates_response(mocked_nhtsa_api: MockRouter) -> None:
    route = mocked_nhtsa_api.get("/recalls/recallsByVehicle")
    route.mock(
        return_value=httpx.Response(
            200,
            json={
                "Count": 1,
                "Message": "Results returned successfully",
                "Results": [{"Make": "Honda", "Model": "Civic", "ModelYear": 2019}],
            },
        )
    )
    settings = Settings(nhtsa_api_base_url="https://api.nhtsa.gov")

    with NhtsaClient(settings=settings) as client:
        response = client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)

    assert route.called
    assert response.count == 1
    assert response.results[0]["Make"] == "Honda"


def test_get_raises_domain_error_for_http_errors(mocked_nhtsa_api: MockRouter) -> None:
    route = mocked_nhtsa_api.get("/recalls/recallsByVehicle")
    route.mock(
        return_value=httpx.Response(
            429,
            request=httpx.Request("GET", "https://api.nhtsa.gov/recalls/recallsByVehicle"),
        )
    )
    settings = Settings(nhtsa_api_base_url="https://api.nhtsa.gov")

    with NhtsaClient(settings=settings) as client:
        with pytest.raises(NhtsaApiError, match="status 429"):
            client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)
