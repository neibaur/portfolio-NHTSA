"""Postgres connection helpers."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg import Connection

from nhtsa_pipeline.config.settings import Settings


@contextmanager
def postgres_connection(settings: Settings | None = None) -> Iterator[Connection[Any]]:
    """Open a Postgres connection using the configured database URL."""
    config = settings or Settings.from_env()
    if not config.database_url:
        raise ValueError("DATABASE_URL must be configured before opening a database connection.")

    with psycopg.connect(config.database_url) as connection:
        yield connection
