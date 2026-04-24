from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app import crud
from app.core.db import engine
from app.core.supabase import SupabaseAuthError, supabase_token_verifier
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_current_user(session: SessionDep, credentials: TokenDep) -> User:
    """Resolve the current app user from a Supabase bearer token.

    Args:
        session: Database session.
        credentials: HTTP bearer credentials from FastAPI security dependency.

    Returns:
        Active app user profile synced from Supabase token claims.

    Raises:
        HTTPException: Raised when the token is missing, invalid, or inactive.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    try:
        claims = supabase_token_verifier.verify(credentials.credentials)
    except SupabaseAuthError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user = session.get(User, claims.sub)
    full_name = claims.user_metadata.get("full_name")
    if user is None:
        user = crud.get_user_by_email(session=session, email=str(claims.email))
        if user is None:
            user = User(id=claims.sub, email=claims.email, full_name=full_name)
            session.add(user)
            session.commit()
            session.refresh(user)
        elif user.id != claims.sub:
            user.id = claims.sub
            if full_name:
                user.full_name = full_name
            session.add(user)
            session.commit()
            session.refresh(user)
    elif user.email != claims.email or (full_name and user.full_name != full_name):
        user.email = claims.email
        if full_name:
            user.full_name = full_name
        session.add(user)
        session.commit()
        session.refresh(user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
