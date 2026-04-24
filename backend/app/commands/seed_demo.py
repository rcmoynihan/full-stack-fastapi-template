"""One-off command to seed demo/development data.

Usage: python -m app.commands.seed_demo
"""

import structlog
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.db import engine, init_db
from app.core.logging import setup_logging
from app.models import Item, ItemCreate, User

DEMO_ITEMS: tuple[ItemCreate, ...] = (
    ItemCreate(
        title="Review deployment checklist",
        description="Confirm Fly secrets, Supabase URLs, and smoke-test URLs.",
    ),
    ItemCreate(
        title="Invite the first teammate",
        description="Use the admin screen to create the next application user.",
    ),
)

logger = structlog.get_logger(__name__)


def _seed_demo_items(session: Session, owner: User) -> int:
    """Create deterministic demo items for the first superuser.

    Args:
        session: Active database session.
        owner: User that owns the demo items.

    Returns:
        Number of newly-created demo items.
    """
    created_count = 0
    for item_in in DEMO_ITEMS:
        existing_item = session.exec(
            select(Item).where(
                Item.owner_id == owner.id,
                Item.title == item_in.title,
            )
        ).first()
        if existing_item:
            continue
        crud.create_item(session=session, item_in=item_in, owner_id=owner.id)
        created_count += 1
    return created_count


def main() -> None:
    """Seed demo data for local development."""
    setup_logging()
    logger.info("seed_demo_started")
    with Session(engine) as session:
        init_db(session)
        first_superuser = session.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        ).first()
        if first_superuser is None:
            raise RuntimeError("No superuser exists after database bootstrap.")

        created_count = _seed_demo_items(session, first_superuser)

    logger.info("seed_demo_finished", created_count=created_count)


if __name__ == "__main__":
    main()
