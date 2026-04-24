import structlog
from sqlalchemy import Engine
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.db import engine
from app.core.logging import setup_logging

logger = structlog.get_logger(__name__)

MAX_TRIES = 60 * 5
WAIT_SECONDS = 1
LOG_LEVEL_INFO = 20
LOG_LEVEL_WARNING = 30


@retry(
    stop=stop_after_attempt(MAX_TRIES),
    wait=wait_fixed(WAIT_SECONDS),
    before=before_log(logger, LOG_LEVEL_INFO),
    after=after_log(logger, LOG_LEVEL_WARNING),
)
def init(db_engine: Engine) -> None:
    """Wait for the application database to accept SQL queries.

    Args:
        db_engine: SQLAlchemy engine for the configured application database.
    """
    try:
        with Session(db_engine) as session:
            # Try to create session to check if DB is awake
            session.exec(select(1))
    except Exception:
        logger.exception("database_wait_failed")
        raise


def main() -> None:
    """Run application database startup checks."""
    setup_logging()
    logger.info("service_initializing")
    init(engine)
    logger.info("service_initialized")


if __name__ == "__main__":
    main()
