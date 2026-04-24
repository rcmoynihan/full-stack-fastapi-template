import uuid
from typing import Any

from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.models import User


def get_engine_kwargs() -> dict[str, Any]:
    """Build SQLAlchemy engine options from application settings.

    Returns:
        Engine keyword arguments tuned for predictable managed Postgres usage.
    """
    return {
        "pool_pre_ping": True,
        "pool_size": settings.SQLALCHEMY_POOL_SIZE,
        "max_overflow": settings.SQLALCHEMY_MAX_OVERFLOW,
        "pool_timeout": settings.SQLALCHEMY_POOL_TIMEOUT,
    }


engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    **get_engine_kwargs(),
)


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(
    session: Session,
    *,
    user_id: uuid.UUID | None = None,
    email: str | None = None,
    full_name: str | None = None,
) -> None:
    """Create the configured first superuser when missing.

    Args:
        session: Database session used for the bootstrap query and insert.
        user_id: Optional Supabase Auth user ID.
        email: Optional superuser email.
        full_name: Optional superuser display name.
    """
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    superuser_id = user_id or settings.FIRST_SUPERUSER_ID
    superuser_email = email or str(settings.FIRST_SUPERUSER)
    user = session.exec(
        select(User).where((User.id == superuser_id) | (User.email == superuser_email))
    ).first()
    if not user:
        user = User(
            id=superuser_id,
            email=superuser_email,
            full_name=full_name,
            is_superuser=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    elif not user.is_superuser:
        user.is_superuser = True
        session.add(user)
        session.commit()
