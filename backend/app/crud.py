import uuid
from typing import Any

from sqlmodel import Session, select

from app.models import Item, ItemCreate, User, UserUpdate


def create_user_profile(
    *,
    session: Session,
    user_id: uuid.UUID,
    email: str,
    full_name: str | None = None,
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    """Create an app profile for a Supabase Auth user.

    Args:
        session: Database session.
        user_id: Supabase Auth user ID.
        email: User email.
        full_name: Optional display name.
        is_active: Whether the profile is allowed to use the app.
        is_superuser: Whether the profile has administrator privileges.

    Returns:
        Created app user profile.
    """
    db_obj = User(
        id=user_id,
        email=email,
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    """Update an app user profile.

    Args:
        session: Database session.
        db_user: Existing app user profile.
        user_in: Profile update payload.

    Returns:
        Updated app user profile.
    """
    user_data = user_in.model_dump(exclude_unset=True, exclude={"password"})
    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """Return an app user profile by email.

    Args:
        session: Database session.
        email: Email address.

    Returns:
        Matching profile or None.
    """
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    """Create an item owned by an app user profile.

    Args:
        session: Database session.
        item_in: Item fields from the API request.
        owner_id: App user profile ID.

    Returns:
        Created item.
    """
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
