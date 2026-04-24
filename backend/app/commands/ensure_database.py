"""Create the configured local Postgres database when it is missing.

Usage: python -m app.commands.ensure_database
"""

import os

import psycopg
import structlog
from psycopg import sql

from app.core.logging import setup_logging

DEFAULT_MAINTENANCE_DATABASE = "postgres"
DEFAULT_POSTGRES_HOST = "localhost"
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_POSTGRES_USER = "postgres"

logger = structlog.get_logger(__name__)


def get_postgres_port() -> int:
    """Read the Postgres port from the environment.

    Returns:
        Configured Postgres port.
    """
    return int(os.environ.get("POSTGRES_PORT", str(DEFAULT_POSTGRES_PORT)))


def get_target_database() -> str:
    """Read the application database name from the environment.

    Returns:
        Configured application database name.
    """
    database = os.environ.get("POSTGRES_DB")
    if not database:
        raise RuntimeError("POSTGRES_DB must be set before ensuring the database.")
    return database


def build_maintenance_conninfo() -> str:
    """Build a connection string for the maintenance database.

    Returns:
        Psycopg connection string for the local Postgres maintenance database.
    """
    host = os.environ.get("POSTGRES_SERVER", DEFAULT_POSTGRES_HOST)
    port = get_postgres_port()
    user = os.environ.get("POSTGRES_USER", DEFAULT_POSTGRES_USER)
    password = os.environ.get("POSTGRES_PASSWORD", "")
    return (
        f"host={host} port={port} dbname={DEFAULT_MAINTENANCE_DATABASE} "
        f"user={user} password={password}"
    )


def ensure_database() -> None:
    """Create the configured application database when it is absent."""
    target_database = get_target_database()
    if target_database == DEFAULT_MAINTENANCE_DATABASE:
        logger.info("database_ensure_skipped", database=target_database)
        return

    with psycopg.connect(build_maintenance_conninfo(), autocommit=True) as connection:
        exists = connection.execute(
            "select 1 from pg_database where datname = %s",
            (target_database,),
        ).fetchone()
        if exists:
            logger.info("database_exists", database=target_database)
            return

        connection.execute(
            sql.SQL("create database {}").format(sql.Identifier(target_database))
        )
        logger.info("database_created", database=target_database)


def main() -> None:
    """Run local database bootstrap."""
    setup_logging()
    ensure_database()


if __name__ == "__main__":
    main()
