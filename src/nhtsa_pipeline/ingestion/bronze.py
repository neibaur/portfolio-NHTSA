"""Bronze layer ingestion entry points."""

from nhtsa_pipeline.clients.nhtsa import NhtsaClient
from nhtsa_pipeline.models.nhtsa import NhtsaRecallsResponse


def fetch_vehicle_recalls(
    client: NhtsaClient,
    *,
    make: str,
    model: str,
    model_year: int,
) -> NhtsaRecallsResponse:
    """Fetch raw recall data for storage in the Bronze layer."""
    return client.get_recalls_by_vehicle(make=make, model=model, model_year=model_year)
