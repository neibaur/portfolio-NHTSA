"""Tests for the NHTSA API client."""

from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from nhtsa_pipeline.clients.nhtsa import (
    NhtsaApiError,
    NhtsaClient,
    NhtsaRateLimitError,
    NhtsaServerError,
)
from nhtsa_pipeline.config.settings import Settings


class MockResponseSequence:
    """MockTransport handler that returns prebuilt responses in order."""

    def __init__(self, *responses: httpx.Response) -> None:
        self._responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if not self._responses:
            raise AssertionError("No mocked response available for request")
        return self._responses.pop(0)


def recall_payload(**overrides: Any) -> dict[str, Any]:
    """Build a representative NHTSA recalls API result."""
    payload = {
        "Manufacturer": "Honda (American Honda Motor Co.)",
        "NHTSACampaignNumber": "23V123000",
        "parkIt": False,
        "parkOutSide": True,
        "ReportReceivedDate": "14/11/2023",
        "Component": "AIR BAGS",
        "Summary": "The driver's air bag may not deploy as intended.",
        "Consequence": "An air bag that does not deploy can increase injury risk.",
        "Remedy": "Dealers will replace the driver's air bag module.",
        "Notes": "Owners may contact Honda customer service.",
        "ModelYear": 2019,
        "Make": "Honda",
        "Model": "Civic",
    }
    payload.update(overrides)
    return payload


def settings() -> Settings:
    """Build API settings for mocked NHTSA calls."""
    return Settings(nhtsa_api_base_url="https://api.nhtsa.gov")


def mocked_client(handler: MockResponseSequence) -> httpx.Client:
    """Build an httpx client backed by mocked responses."""
    return httpx.Client(
        base_url="https://api.nhtsa.gov",
        transport=httpx.MockTransport(handler),
    )


def test_get_recalls_by_vehicle_validates_response() -> None:
    handler = MockResponseSequence(
        httpx.Response(
            200,
            json={
                "Count": 1,
                "Message": "Results returned successfully",
                "Results": [recall_payload()],
            },
        )
    )

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        response = client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)

    assert len(handler.requests) == 1
    request = handler.requests[0]
    assert request.url.path == "/recalls/recallsByVehicle"
    assert request.url.params["make"] == "Honda"
    assert request.url.params["model"] == "Civic"
    assert request.url.params["modelYear"] == "2019"
    assert response.count == 1
    assert response.results[0].campaign_number == "23V123000"
    assert response.results[0].make == "Honda"
    assert response.results[0].park_outside is True


def test_get_validates_generic_response_envelope() -> None:
    handler = MockResponseSequence(
        httpx.Response(
            200,
            json={
                "Count": 1,
                "Message": "Results returned successfully",
                "Results": [{"ModelYear": 2019}],
            },
        )
    )

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        response = client.get("/products/vehicle/modelYears")

    assert handler.requests[0].url.path == "/products/vehicle/modelYears"
    assert response.count == 1
    assert response.results == [{"ModelYear": 2019}]


def test_get_recalls_by_vehicle_retries_429_then_succeeds() -> None:
    handler = MockResponseSequence(
        httpx.Response(429, headers={"Retry-After": "0.25"}),
        httpx.Response(
            200,
            json={
                "Count": 1,
                "Message": "Results returned successfully",
                "Results": [recall_payload()],
            },
        ),
    )
    sleep_calls: list[float] = []

    with NhtsaClient(
        settings=settings(),
        client=mocked_client(handler),
        sleep=sleep_calls.append,
    ) as client:
        response = client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)

    assert len(handler.requests) == 2
    assert sleep_calls == [0.25]
    assert response.results[0].model == "Civic"


def test_get_recalls_by_vehicle_uses_exponential_backoff_for_429_without_retry_after() -> None:
    handler = MockResponseSequence(
        httpx.Response(429),
        httpx.Response(429, headers={"Retry-After": "not-a-number"}),
        httpx.Response(
            200,
            json={
                "Count": 0,
                "Message": "Results returned successfully",
                "Results": [],
            },
        ),
    )
    sleep_calls: list[float] = []

    with NhtsaClient(
        settings=settings(),
        client=mocked_client(handler),
        retry_backoff_seconds=0.5,
        sleep=sleep_calls.append,
    ) as client:
        response = client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)

    assert len(handler.requests) == 3
    assert sleep_calls == [0.5, 1.0]
    assert response.count == 0


def test_get_raises_rate_limit_error_after_retries() -> None:
    handler = MockResponseSequence(
        httpx.Response(429),
        httpx.Response(429),
        httpx.Response(429),
    )
    sleep_calls: list[float] = []

    with NhtsaClient(
        settings=settings(),
        client=mocked_client(handler),
        max_retries=2,
        sleep=sleep_calls.append,
    ) as client:
        with pytest.raises(NhtsaRateLimitError, match="status 429"):
            client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)

    assert len(handler.requests) == 3
    assert sleep_calls == [1.0, 2.0]


def test_get_raises_server_error_for_500_responses() -> None:
    handler = MockResponseSequence(httpx.Response(500))

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        with pytest.raises(NhtsaServerError, match="status 500"):
            client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)

    assert len(handler.requests) == 1


def test_get_raises_domain_error_for_non_retryable_http_errors() -> None:
    handler = MockResponseSequence(httpx.Response(404))

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        with pytest.raises(NhtsaApiError, match="status 404"):
            client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)


def test_get_recalls_by_vehicle_raises_validation_error_for_invalid_records() -> None:
    handler = MockResponseSequence(
        httpx.Response(
            200,
            json={
                "Count": 1,
                "Message": "Results returned successfully",
                "Results": [recall_payload(NHTSACampaignNumber="")],
            },
        )
    )

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        with pytest.raises(ValidationError):
            client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)
