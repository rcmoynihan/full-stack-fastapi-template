import uuid
from typing import Any

import httpx
import jwt
import pytest

from app.core.config import settings
from app.core.supabase import (
    SupabaseAdminClient,
    SupabaseAuthError,
    SupabaseTokenVerifier,
)
from tests.utils.utils import random_email


def make_response(status_code: int, payload: dict[str, Any] | None = None) -> httpx.Response:
    """Create an HTTPX response with request metadata.

    Args:
        status_code: HTTP status code.
        payload: Optional JSON body.

    Returns:
        HTTPX response suitable for client tests.
    """
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("GET", "http://supabase.test/auth/v1/admin/users"),
    )


def test_hmac_token_verifier_accepts_valid_claims() -> None:
    user_id = uuid.uuid4()
    token = jwt.encode(
        {
            "sub": str(user_id),
            "email": "user@example.com",
            "aud": settings.SUPABASE_JWT_AUDIENCE,
            "iss": settings.SUPABASE_JWT_ISSUER,
            "user_metadata": {"full_name": "Test User"},
        },
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )
    verifier = SupabaseTokenVerifier(
        jwks_url="http://supabase.test/jwks",
        jwt_secret=settings.SUPABASE_JWT_SECRET,
        issuer=settings.SUPABASE_JWT_ISSUER,
    )

    claims = verifier.verify(token)

    assert claims.sub == user_id
    assert claims.email == "user@example.com"
    assert claims.user_metadata["full_name"] == "Test User"


def test_hmac_token_verifier_rejects_missing_secret() -> None:
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "email": "user@example.com",
            "aud": settings.SUPABASE_JWT_AUDIENCE,
            "iss": settings.SUPABASE_JWT_ISSUER,
            "user_metadata": {},
        },
        "secret",
        algorithm="HS256",
    )
    verifier = SupabaseTokenVerifier(
        jwks_url="http://supabase.test/jwks",
        jwt_secret=None,
        issuer=settings.SUPABASE_JWT_ISSUER,
    )

    with pytest.raises(SupabaseAuthError):
        verifier.verify(token)


def test_admin_client_create_update_delete_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid.uuid4()
    calls: list[tuple[str, str]] = []

    def fake_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Return fake Supabase Auth responses."""
        _ = kwargs
        calls.append((method, url))
        return make_response(
            200,
            {
                "id": str(user_id),
                "email": "user@example.com",
                "user_metadata": {"full_name": "Test User"},
            },
        )

    monkeypatch.setattr("app.core.supabase.httpx.request", fake_request)
    client = SupabaseAdminClient(base_url="http://supabase.test", secret_key="secret")

    created = client.create_user(
        email="user@example.com", password="password", full_name="Test User"
    )
    updated = client.update_user(user_id=user_id, email="user@example.com")
    client.delete_user(user_id=user_id)

    assert created.id == user_id
    assert updated.email == "user@example.com"
    assert calls == [
        ("POST", "http://supabase.test/auth/v1/admin/users"),
        ("PUT", f"http://supabase.test/auth/v1/admin/users/{user_id}"),
        ("DELETE", f"http://supabase.test/auth/v1/admin/users/{user_id}"),
    ]


def test_admin_client_finds_user_by_email(monkeypatch: pytest.MonkeyPatch) -> None:
    email = random_email()
    user_id = uuid.uuid4()

    def fake_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Return a fake paginated Supabase user list."""
        _ = method, url, kwargs
        return make_response(
            200,
            {
                "users": [
                    {
                        "id": str(user_id),
                        "email": email,
                        "user_metadata": {},
                    }
                ]
            },
        )

    monkeypatch.setattr("app.core.supabase.httpx.request", fake_request)
    client = SupabaseAdminClient(base_url="http://supabase.test", secret_key="secret")

    user = client.get_user_by_email(email=email)

    assert user
    assert user.id == user_id


def test_admin_client_raises_on_supabase_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Return a fake Supabase Auth error."""
        _ = method, url, kwargs
        return make_response(400, {"msg": "bad request"})

    monkeypatch.setattr("app.core.supabase.httpx.request", fake_request)
    client = SupabaseAdminClient(base_url="http://supabase.test", secret_key="secret")

    with pytest.raises(SupabaseAuthError):
        client.create_user(email="user@example.com", password="password")
