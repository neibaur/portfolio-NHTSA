"""Shared pytest configuration."""

from collections.abc import Iterator

import pytest
import respx


@pytest.fixture
def mocked_nhtsa_api() -> Iterator[respx.MockRouter]:
    """Mock external HTTP calls made by httpx."""
    with respx.mock(base_url="https://api.nhtsa.gov") as router:
        yield router
