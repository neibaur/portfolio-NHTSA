"""Helpers for writing local JSON inspection files."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.-]+")
SOURCE_NHTSA = "NHTSA"


def sanitized_filename_part(value: str) -> str:
    """Return a filesystem-friendly filename segment."""
    return _UNSAFE_FILENAME_CHARS.sub("_", value.strip()).strip("_") or "unknown"


def raw_recalls_path(
    *,
    output_dir: Path,
    year: int,
    make: str,
    model: str,
) -> Path:
    """Build the local raw recalls JSON output path."""
    safe_make = sanitized_filename_part(make)
    safe_model = sanitized_filename_part(model)
    return output_dir / f"nhtsa_recalls_{year}_{safe_make}_{safe_model}.json"


def write_json_file(payload: dict[str, Any], output_path: Path) -> Path:
    """Write a JSON payload to disk and return the path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def extract_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract API result records while tolerating NHTSA response key casing."""
    results = payload.get("Results", payload.get("results", []))
    if not isinstance(results, list):
        return []
    return [record for record in results if isinstance(record, dict)]


def utc_ingestion_timestamp() -> str:
    """Return the current UTC timestamp in ISO8601 format."""
    return datetime.now(UTC).isoformat()


def build_bronze_payload(
    api_payload: dict[str, Any],
    *,
    endpoint: str,
    query: dict[str, str | int],
    ingestion_timestamp: str | None = None,
) -> dict[str, Any]:
    """Wrap raw API records in a standardized local Bronze payload."""
    records = extract_results(api_payload)
    return {
        "metadata": {
            "source": SOURCE_NHTSA,
            "endpoint": endpoint,
            "query": query,
            "ingestion_timestamp": ingestion_timestamp or utc_ingestion_timestamp(),
            "record_count": len(records),
        },
        "data": records,
    }


def write_raw_recalls_json(
    payload: dict[str, Any],
    *,
    output_dir: Path,
    year: int,
    make: str,
    model: str,
    endpoint: str,
    query: dict[str, str | int],
) -> Path:
    """Write NHTSA recalls records in the local Bronze JSON format."""
    bronze_payload = build_bronze_payload(payload, endpoint=endpoint, query=query)
    return write_json_file(
        bronze_payload,
        raw_recalls_path(output_dir=output_dir, year=year, make=make, model=model),
    )
