"""One-off command to create the first superuser.

Usage: python -m app.commands.create_superuser
"""

import structlog
from sqlmodel import Session

from app.core.db import engine, init_db
from app.core.logging import setup_logging

logger = structlog.get_logger(__name__)


def main() -> None:
    """Create the configured first superuser if it does not already exist."""
    setup_logging()
    logger.info("create_superuser_started")
    with Session(engine) as session:
        init_db(session)
    logger.info("create_superuser_finished")


if __name__ == "__main__":
    main()
