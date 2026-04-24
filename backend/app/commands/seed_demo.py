"""One-off command to seed demo/development data.

Usage: python -m app.commands.seed_demo
"""

import structlog

from app.core.logging import setup_logging

logger = structlog.get_logger(__name__)


def main() -> None:
    """Seed demo data for local development."""
    setup_logging()
    logger.info("seed_demo_started")
    logger.info("seed_demo_finished")


if __name__ == "__main__":
    main()
