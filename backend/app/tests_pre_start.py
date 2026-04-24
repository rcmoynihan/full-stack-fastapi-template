import os

import structlog
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.logging import setup_logging

logger = structlog.get_logger(__name__)

MAX_TRIES = 60 * 5
WAIT_SECONDS = 1
LOG_LEVEL_INFO = 20
LOG_LEVEL_WARNING = 30
DEFAULT_POSTGRES_SERVER = "localhost"
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_POSTGRES_DB = "app"
DEFAULT_POSTGRES_USER = "postgres"
DEFAULT_POSTGRES_PASSWORD = "changethis"
UNSAFE_DATABASE_HOST_FRAGMENTS = ("supabase",)


def _build_test_database_url() -> URL:
    """Build the local database URL used by backend test startup checks.

    Returns:
        SQLAlchemy URL for the local test database.
    """
    ignored_urls = [
        name
        for name in ("DATABASE_URL", "DATABASE_URL_DIRECT")
        if os.environ.pop(name, None)
    ]
    if ignored_urls:
        logger.warning(
            "ignored_deployment_database_urls_for_tests",
            variable_names=ignored_urls,
        )

    os.environ["ENVIRONMENT"] = "local"
    server = os.environ.setdefault("POSTGRES_SERVER", DEFAULT_POSTGRES_SERVER)
    port = int(os.environ.setdefault("POSTGRES_PORT", str(DEFAULT_POSTGRES_PORT)))
    database = os.environ.setdefault("POSTGRES_DB", DEFAULT_POSTGRES_DB)
    user = os.environ.setdefault("POSTGRES_USER", DEFAULT_POSTGRES_USER)
    password = os.environ.setdefault("POSTGRES_PASSWORD", DEFAULT_POSTGRES_PASSWORD)

    server_lower = server.lower()
    if any(fragment in server_lower for fragment in UNSAFE_DATABASE_HOST_FRAGMENTS):
        raise RuntimeError(
            f"Refusing to run backend tests against non-local database host: {server}"
        )

    return URL.create(
        "postgresql+psycopg",
        username=user,
        password=password,
        host=server,
        port=port,
        database=database,
    )


@retry(
    stop=stop_after_attempt(MAX_TRIES),
    wait=wait_fixed(WAIT_SECONDS),
    before=before_log(logger, LOG_LEVEL_INFO),
    after=after_log(logger, LOG_LEVEL_WARNING),
)
def init(db_engine: Engine) -> None:
    """Wait for the local test database to accept connections.

    Args:
        db_engine: SQLAlchemy engine for the local test database.
    """
    try:
        # Try to create session to check if DB is awake
        with Session(db_engine) as session:
            session.exec(select(1))
    except Exception:
        logger.exception("test_database_wait_failed")
        raise


def main() -> None:
    """Run backend test database startup checks."""
    setup_logging()
    logger.info("test_database_initializing")
    engine = create_engine(_build_test_database_url())
    init(engine)
    engine.dispose()
    logger.info("test_database_initialized")


if __name__ == "__main__":
    main()
