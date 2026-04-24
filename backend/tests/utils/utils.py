import random
import string

import jwt

from app.core.config import settings
from app.models import User


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def create_supabase_access_token(user: User) -> str:
    """Create a test Supabase-compatible access token.

    Args:
        user: App user profile to encode in the token.

    Returns:
        Signed JWT accepted by the local test verifier.
    """
    if not settings.SUPABASE_JWT_SECRET:
        raise RuntimeError("SUPABASE_JWT_SECRET is required for backend tests")
    return jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "aud": settings.SUPABASE_JWT_AUDIENCE,
            "iss": settings.SUPABASE_JWT_ISSUER,
            "role": "authenticated",
            "user_metadata": {"full_name": user.full_name},
        },
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )


def get_superuser_token_headers() -> dict[str, str]:
    """Return auth headers for the configured first superuser.

    Returns:
        Authorization header containing a Supabase-compatible test token.
    """
    user = User(
        id=settings.FIRST_SUPERUSER_ID,
        email=settings.FIRST_SUPERUSER,
        is_superuser=True,
        full_name="Admin",
    )
    return {"Authorization": f"Bearer {create_supabase_access_token(user)}"}
