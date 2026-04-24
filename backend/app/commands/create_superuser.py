"""One-off command to create the first superuser.

Usage: python -m app.commands.create_superuser
"""

import structlog
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine, init_db
from app.core.logging import setup_logging
from app.core.supabase import SupabaseAuthError, supabase_admin

logger = structlog.get_logger(__name__)


def main() -> None:
    """Create the configured first superuser in Supabase Auth and the app DB."""
    setup_logging()
    logger.info("create_superuser_started")
    auth_user = supabase_admin.get_user_by_email(email=str(settings.FIRST_SUPERUSER))
    if auth_user is None:
        try:
            auth_user = supabase_admin.create_user(
                email=str(settings.FIRST_SUPERUSER),
                password=settings.FIRST_SUPERUSER_PASSWORD,
                full_name="Admin",
            )
        except SupabaseAuthError as exc:
            logger.error("create_superuser_failed", error=str(exc))
            raise

    with Session(engine) as session:
        init_db(
            session,
            user_id=auth_user.id,
            email=str(auth_user.email),
            full_name=auth_user.user_metadata.get("full_name"),
        )
    logger.info("create_superuser_finished")


if __name__ == "__main__":
    main()
