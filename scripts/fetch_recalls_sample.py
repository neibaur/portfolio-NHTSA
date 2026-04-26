"""Fetch a local sample of NHTSA recalls data and save the raw JSON response."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from nhtsa_pipeline.clients.nhtsa import NhtsaApiError, NhtsaClient  # noqa: E402
from nhtsa_pipeline.io.json_files import write_raw_recalls_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True, help="Vehicle model year")
    parser.add_argument("--make", required=True, help="Vehicle make")
    parser.add_argument("--model", required=True, help="Vehicle model")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory for the raw JSON output",
    )
    return parser.parse_args()


def main() -> int:
    """Fetch recalls and write the raw JSON payload locally."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args()

    try:
        with NhtsaClient() as client:
            payload = client.fetch_recalls_raw(
                year=args.year,
                make=args.make,
                model=args.model,
            )
    except NhtsaApiError as exc:
        logging.getLogger(__name__).error("NHTSA recalls fetch failed: %s", exc)
        return 1

    output_path = write_raw_recalls_json(
        payload,
        output_dir=args.output_dir,
        year=args.year,
        make=args.make,
        model=args.model,
    )
    print(f"Wrote raw NHTSA recalls JSON to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
