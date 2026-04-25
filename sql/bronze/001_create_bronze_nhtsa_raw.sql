-- Raw API payloads captured from NHTSA public endpoints.
CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.nhtsa_api_responses (
    id BIGSERIAL PRIMARY KEY,
    source_endpoint TEXT NOT NULL,
    request_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
