"""Helpers for writing local JSON inspection files."""

import json
import re
from pathlib import Path
from typing import Any

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.-]+")


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


def write_raw_recalls_json(
    payload: dict[str, Any],
    *,
    output_dir: Path,
    year: int,
    make: str,
    model: str,
) -> Path:
    """Write raw NHTSA recalls JSON to the expected local filename."""
    return write_json_file(
        payload,
        raw_recalls_path(output_dir=output_dir, year=year, make=make, model=model),
    )

