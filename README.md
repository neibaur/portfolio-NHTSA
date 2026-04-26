# portfolio-nhtsa

A production-style Python data engineering project for ingesting public vehicle safety data from the National Highway Traffic Safety Administration (NHTSA), storing raw API payloads in Supabase Postgres, and transforming them into analytics-ready datasets.

## Project Overview

This repository is a portfolio project focused on clear, testable data pipeline design. The pipeline will extract NHTSA public API data, preserve raw responses in a Bronze layer, standardize and validate records in a Silver layer, and publish curated Gold tables for dashboards and analysis.

The current scaffold intentionally keeps business logic small. It establishes the package structure, configuration, quality gates, and example client tests that future ingestion and transformation work can build on.

## Architecture

```text
NHTSA Public APIs
        |
        v
Python ingestion jobs
        |
        v
Supabase Postgres
        |
        v
Bronze: raw JSON API responses
        |
        v
Silver: validated, cleaned, deduplicated records
        |
        v
Gold: analytics tables for dashboards
```

## Medallion Layers

**Bronze**

- Stores raw API response payloads and request metadata.
- Preserves source data for auditability and reprocessing.
- Keeps transformations minimal.

**Silver**

- Applies Pydantic validation and normalization.
- Produces typed, deduplicated, analysis-friendly entities.
- Adds data quality checks as contracts become stable.

**Gold**

- Publishes dimensional or aggregate models.
- Supports dashboard metrics, portfolio reporting, and downstream analytics.
- Optimizes for query patterns rather than raw source fidelity.

## Tech Stack

- Python 3.11+
- `httpx` for API calls
- `pydantic` for response validation
- `psycopg` for Postgres access
- `python-dotenv` for local environment configuration
- `pytest` and `pytest-cov` for tests and coverage
- `ruff` for linting
- `mypy` for static type checking
- GitHub Actions for CI

## Planned Pipeline Flow

1. Load configuration from environment variables or `.env`.
2. Call selected NHTSA public API endpoints with a typed API client.
3. Validate standard API response envelopes with Pydantic.
4. Insert raw JSON payloads into Bronze Postgres tables.
5. Transform Bronze records into Silver normalized entities.
6. Build Gold fact and dimension tables for analytics and dashboards.
7. Run tests, linting, type checks, and coverage in CI before merging changes.

## Repository Structure

```text
portfolio-nhtsa/
  src/
    nhtsa_pipeline/
      clients/        # NHTSA API client wrappers
      config/         # Settings and environment loading
      db/             # Postgres connection helpers
      ingestion/      # Bronze ingestion entry points
      models/         # Pydantic schemas
      transforms/     # Silver and Gold transformation helpers
  tests/
    unit/
    integration/
  sql/
    bronze/
    silver/
    gold/
  .github/workflows/
    ci.yml
```

## Getting Started

Create and activate a Python 3.11+ virtual environment, then install the project with development dependencies:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Create local environment settings:

```bash
cp .env.example .env
```

Run quality checks:

```bash
ruff check .
mypy
pytest
```

## Milestone 1: Local API Client

The first local milestone fetches NHTSA recalls data and saves the raw JSON response for inspection. It does not connect to Supabase or any database.

Run a sample recalls fetch from the repository root:

```bash
python scripts/fetch_recalls_sample.py --year 2023 --make Toyota --model Camry
```

The script writes the raw API response to:

```text
data/raw/nhtsa_recalls_2023_Toyota_Camry.json
```

Files under `data/raw/` are ignored by git so downloaded API samples stay local.

## Milestone 2: Bronze Layer Simulation

Local raw API files now use a Bronze-style envelope with `metadata` and `data` fields. The metadata captures the source system, endpoint, query parameters, UTC ingestion timestamp, and record count. The `data` field stores the raw records returned by the API with minimal transformation.

This structure makes each local extract easier to audit and replay. It also mirrors the shape that can later be inserted into a database Bronze table, without adding Supabase or database logic yet.

Example output shape:

```json
{
  "metadata": {
    "source": "NHTSA",
    "endpoint": "/recalls/recallsByVehicle",
    "query": {
      "modelYear": 2023,
      "make": "Toyota",
      "model": "Camry"
    },
    "ingestion_timestamp": "2026-04-26T18:30:00+00:00",
    "record_count": 2
  },
  "data": []
}
```

## Configuration

The application reads these environment variables:

- `ENVIRONMENT`
- `LOG_LEVEL`
- `NHTSA_API_BASE_URL`
- `NHTSA_API_TIMEOUT_SECONDS`
- `DATABASE_URL`

See `.env.example` for local defaults.

## Testing

The initial test suite includes mocked HTTP tests for the NHTSA API client and a small transformation helper test. External API calls should remain mocked in unit tests so the suite is deterministic and fast.

Coverage settings are defined in `pyproject.toml` and enforced with a minimum threshold.

## License

This project is licensed under the MIT License.
