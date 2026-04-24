import uuid

from sqlmodel import Session

from app import crud
from app.models import User
from tests.utils.utils import create_supabase_access_token, random_email


def user_authentication_headers(*, user: User) -> dict[str, str]:
    """Return auth headers for an app user profile.

    Args:
        user: App user profile to encode in the test token.

    Returns:
        Authorization header containing a Supabase-compatible test token.
    """
    auth_token = create_supabase_access_token(user)
    return {"Authorization": f"Bearer {auth_token}"}


def create_random_user(db: Session) -> User:
    """Create a random non-superuser app profile.

    Args:
        db: Database session.

    Returns:
        Created app user profile.
    """
    email = random_email()
    user = crud.create_user_profile(session=db, user_id=uuid.uuid4(), email=email)
    return user


def authentication_token_from_email(
    *, email: str, db: Session
) -> dict[str, str]:
    """Return a valid token for the user with given email.

    Args:
        email: Email address to find or create.
        db: Database session.

    Returns:
        Authorization header containing a Supabase-compatible test token.
    """
    user = crud.get_user_by_email(session=db, email=email)
    if not user:
        user = crud.create_user_profile(
            session=db,
            user_id=uuid.uuid4(),
            email=email,
        )

    return user_authentication_headers(user=user)
