"""Tests for the NHTSA API client."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from nhtsa_pipeline.clients.nhtsa import (
    NhtsaApiError,
    NhtsaClient,
    NhtsaInvalidJsonError,
    NhtsaRateLimitError,
    NhtsaServerError,
    NhtsaTimeoutError,
)
from nhtsa_pipeline.config.settings import Settings
from nhtsa_pipeline.io.json_files import (
    build_bronze_payload,
    raw_recalls_path,
    write_raw_recalls_json,
)


class MockResponseSequence:
    """MockTransport handler that returns prebuilt responses in order."""

    def __init__(self, *responses: httpx.Response | Exception) -> None:
        self._responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if not self._responses:
            raise AssertionError("No mocked response available for request")
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


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


def test_fetch_recalls_raw_returns_unmodified_payload() -> None:
    payload = {
        "Count": 1,
        "Message": "Results returned successfully",
        "Results": [recall_payload()],
        "SearchCriteria": "modelYear:2019 make:Honda model:Civic",
    }
    handler = MockResponseSequence(httpx.Response(200, json=payload))

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        response = client.fetch_recalls_raw(year=2019, make="Honda", model="Civic")

    assert response == payload


def test_get_recalls_by_vehicle_accepts_real_recalls_response_casing() -> None:
    handler = MockResponseSequence(
        httpx.Response(
            200,
            json={
                "Count": 1,
                "Message": "Results returned successfully",
                "results": [recall_payload(ModelYear="2023", Make="TOYOTA", Model="CAMRY")],
            },
        )
    )

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        response = client.get_recalls_by_vehicle(make="Toyota", model="Camry", model_year=2023)

    assert response.count == 1
    assert len(response.results) == 1
    assert response.results[0].make == "TOYOTA"
    assert response.results[0].model_year == 2023


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


def test_get_recalls_by_vehicle_handles_successful_empty_results() -> None:
    handler = MockResponseSequence(
        httpx.Response(
            200,
            json={
                "Count": 0,
                "Message": "Results returned successfully",
                "Results": [],
            },
        )
    )

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        response = client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)

    assert response.count == 0
    assert response.results == []


def test_fetch_recalls_raw_warns_when_count_positive_but_results_empty(
    caplog: pytest.LogCaptureFixture,
) -> None:
    handler = MockResponseSequence(
        httpx.Response(
            200,
            json={
                "Count": 1,
                "Message": "Results returned successfully",
                "results": [],
            },
        )
    )

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        with caplog.at_level("WARNING"):
            payload = client.fetch_recalls_raw(year=2023, make="Toyota", model="Camry")

    assert payload["Count"] == 1
    assert "reported Count=1 but the result list was empty" in caplog.text


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


def test_get_raises_invalid_json_error() -> None:
    handler = MockResponseSequence(httpx.Response(200, content=b"not-json"))

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        with pytest.raises(NhtsaInvalidJsonError, match="invalid JSON"):
            client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)


def test_get_raises_invalid_json_error_for_non_object_payload() -> None:
    handler = MockResponseSequence(httpx.Response(200, json=[]))

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        with pytest.raises(NhtsaInvalidJsonError, match="non-object"):
            client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)


def test_get_raises_timeout_error() -> None:
    request = httpx.Request("GET", "https://api.nhtsa.gov/recalls/recallsByVehicle")
    handler = MockResponseSequence(httpx.TimeoutException("request timed out", request=request))

    with NhtsaClient(settings=settings(), client=mocked_client(handler)) as client:
        with pytest.raises(NhtsaTimeoutError, match="timed out"):
            client.get_recalls_by_vehicle(make="Honda", model="Civic", model_year=2019)


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


def test_write_raw_recalls_json_writes_expected_file() -> None:
    output_dir = Path("data/raw/test-writer")
    shutil.rmtree(output_dir, ignore_errors=True)
    payload = {
        "Count": 1,
        "Message": "Results returned successfully",
        "Results": [recall_payload()],
    }

    try:
        output_path = write_raw_recalls_json(
            payload,
            output_dir=output_dir,
            year=2023,
            make="Toyota",
            model="Camry",
            endpoint="/recalls/recallsByVehicle",
            query={"modelYear": 2023, "make": "Toyota", "model": "Camry"},
        )

        assert output_path == output_dir / "nhtsa_recalls_2023_Toyota_Camry.json"
        file_text = output_path.read_text(encoding="utf-8")
        assert file_text.endswith("\n")
        assert '"metadata": {' in file_text
        assert '"data": [' in file_text
        assert '"NHTSACampaignNumber": "23V123000"' in file_text
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def test_build_bronze_payload_adds_standard_metadata() -> None:
    payload = {
        "Count": 2,
        "Message": "Results returned successfully",
        "results": [recall_payload(), recall_payload(NHTSACampaignNumber="23V456000")],
    }
    query = {"modelYear": 2023, "make": "Toyota", "model": "Camry"}

    bronze_payload = build_bronze_payload(
        payload,
        endpoint="/recalls/recallsByVehicle",
        query=query,
        ingestion_timestamp="2026-04-26T18:30:00+00:00",
    )

    assert bronze_payload == {
        "metadata": {
            "source": "NHTSA",
            "endpoint": "/recalls/recallsByVehicle",
            "query": query,
            "ingestion_timestamp": "2026-04-26T18:30:00+00:00",
            "record_count": 2,
        },
        "data": payload["results"],
    }


def test_build_bronze_payload_calculates_record_count_for_uppercase_results() -> None:
    payload = {
        "Count": 1,
        "Message": "Results returned successfully",
        "Results": [recall_payload()],
    }

    bronze_payload = build_bronze_payload(
        payload,
        endpoint="/recalls/recallsByVehicle",
        query={"modelYear": 2019, "make": "Honda", "model": "Civic"},
        ingestion_timestamp="2026-04-26T18:30:00+00:00",
    )

    assert bronze_payload["metadata"]["record_count"] == 1
    assert bronze_payload["data"] == payload["Results"]


def test_build_bronze_payload_uses_iso8601_timestamp() -> None:
    bronze_payload = build_bronze_payload(
        {"Count": 0, "Message": "Results returned successfully", "results": []},
        endpoint="/recalls/recallsByVehicle",
        query={"modelYear": 2023, "make": "Toyota", "model": "Camry"},
    )

    timestamp = bronze_payload["metadata"]["ingestion_timestamp"]
    parsed_timestamp = datetime.fromisoformat(timestamp)

    assert parsed_timestamp.tzinfo is not None
    assert bronze_payload["metadata"]["record_count"] == 0


def test_raw_recalls_path_sanitizes_filename_parts() -> None:
    output_dir = Path("data/raw/test-writer")

    output_path = raw_recalls_path(
        output_dir=output_dir,
        year=2023,
        make="Mercedes-Benz",
        model="E Class / Wagon",
    )

    assert output_path == output_dir / "nhtsa_recalls_2023_Mercedes-Benz_E_Class_Wagon.json"
