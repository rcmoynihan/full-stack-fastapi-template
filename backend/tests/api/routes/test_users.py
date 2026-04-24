import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.supabase import SupabaseAuthError, SupabaseUser
from app.models import User
from tests.utils.user import create_random_user, user_authentication_headers
from tests.utils.utils import (
    create_supabase_access_token,
    random_email,
    random_lower_string,
)


class FakeSupabaseAdmin:
    """Test double for Supabase Auth admin operations."""

    def __init__(self) -> None:
        """Create an in-memory fake admin client."""
        self.deleted_user_ids: list[uuid.UUID] = []
        self.updated_users: list[dict[str, Any]] = []
        self.raise_on_create = False
        self.raise_on_update = False
        self.raise_on_delete = False

    def create_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> SupabaseUser:
        """Return a fake Supabase user for admin-created accounts."""
        _ = password
        if self.raise_on_create:
            raise SupabaseAuthError("create failed")
        return SupabaseUser(
            id=uuid.uuid4(),
            email=email,
            user_metadata={"full_name": full_name},
        )

    def update_user(
        self,
        *,
        user_id: uuid.UUID,
        email: str | None = None,
        password: str | None = None,
        full_name: str | None = None,
    ) -> SupabaseUser:
        """Record a fake Supabase user update."""
        if self.raise_on_update:
            raise SupabaseAuthError("update failed")
        self.updated_users.append(
            {
                "user_id": user_id,
                "email": email,
                "password": password,
                "full_name": full_name,
            }
        )
        return SupabaseUser(
            id=user_id,
            email=email or random_email(),
            user_metadata={"full_name": full_name},
        )

    def delete_user(self, *, user_id: uuid.UUID) -> None:
        """Record a fake Supabase user deletion."""
        if self.raise_on_delete:
            raise SupabaseAuthError("delete failed")
        self.deleted_user_ids.append(user_id)


@pytest.fixture
def fake_supabase_admin(monkeypatch: pytest.MonkeyPatch) -> FakeSupabaseAdmin:
    """Replace the users route Supabase admin client with a fake."""
    fake = FakeSupabaseAdmin()
    monkeypatch.setattr("app.api.routes.users.supabase_admin", fake)
    return fake


def test_get_users_superuser_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == settings.FIRST_SUPERUSER


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == settings.EMAIL_TEST_USER


def test_get_current_user_creates_profile_from_supabase_token(
    client: TestClient, db: Session
) -> None:
    user = User(id=uuid.uuid4(), email=random_email(), full_name="New User")
    headers = {"Authorization": f"Bearer {create_supabase_access_token(user)}"}

    r = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)

    assert r.status_code == 200
    created_user = db.get(User, user.id)
    assert created_user
    assert created_user.email == user.email


def test_invalid_supabase_token_is_rejected(client: TestClient) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert r.status_code == 403


def test_create_user_new_email(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    fake_supabase_admin: FakeSupabaseAdmin,
) -> None:
    _ = fake_supabase_admin
    email = random_email()
    data = {"email": email, "password": random_lower_string(), "is_active": True}

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )

    assert 200 <= r.status_code < 300
    created_user = r.json()
    user = crud.get_user_by_email(session=db, email=email)
    assert user
    assert user.email == created_user["email"]


def test_create_user_existing_email(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    email = random_email()
    crud.create_user_profile(session=db, user_id=uuid.uuid4(), email=email)
    data = {"email": email, "password": random_lower_string()}

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 400


def test_create_user_by_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {"email": random_email(), "password": random_lower_string()}

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 403


def test_create_user_returns_supabase_error(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    fake_supabase_admin: FakeSupabaseAdmin,
) -> None:
    fake_supabase_admin.raise_on_create = True
    data = {"email": random_email(), "password": random_lower_string()}

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 400
    assert r.json()["detail"] == "create failed"


def test_retrieve_users(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    crud.create_user_profile(session=db, user_id=uuid.uuid4(), email=random_email())
    crud.create_user_profile(session=db, user_id=uuid.uuid4(), email=random_email())

    r = client.get(f"{settings.API_V1_STR}/users/", headers=superuser_token_headers)
    all_users = r.json()

    assert len(all_users["data"]) > 1
    assert "count" in all_users
    for item in all_users["data"]:
        assert "email" in item


def test_update_user_me(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
    fake_supabase_admin: FakeSupabaseAdmin,
) -> None:
    full_name = "Updated Name"
    email = random_email()
    data = {"full_name": full_name, "email": email}

    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["email"] == email
    assert updated_user["full_name"] == full_name
    assert fake_supabase_admin.updated_users[-1]["email"] == email
    user = crud.get_user_by_email(session=db, email=email)
    assert user


def test_update_user_me_existing_email_conflict(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    existing = create_random_user(db)

    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"email": existing.email},
    )

    assert r.status_code == 409


def test_update_user_me_returns_supabase_error(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    fake_supabase_admin: FakeSupabaseAdmin,
) -> None:
    fake_supabase_admin.raise_on_update = True

    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": "Updated"},
    )

    assert r.status_code == 400
    assert r.json()["detail"] == "update failed"


def test_delete_user_me(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
    fake_supabase_admin: FakeSupabaseAdmin,
) -> None:
    normal_user = crud.get_user_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert normal_user
    normal_user_id = normal_user.id

    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    db.expire_all()
    assert db.get(User, normal_user_id) is None
    assert fake_supabase_admin.deleted_user_ids == [normal_user_id]


def test_delete_user_me_rejects_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )

    assert r.status_code == 403


def test_get_existing_user_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user = create_random_user(db)

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    api_user = r.json()
    assert user.email == api_user["email"]


def test_get_non_existing_user_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_get_existing_user_current_user(client: TestClient, db: Session) -> None:
    user = create_random_user(db)
    headers = user_authentication_headers(user=user)

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=headers,
    )

    assert 200 <= r.status_code < 300
    api_user = r.json()
    assert user.email == api_user["email"]


def test_get_existing_user_permissions_error(
    db: Session,
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = create_random_user(db)

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


def test_get_non_existing_user_permissions_error(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


def test_update_user(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    fake_supabase_admin: FakeSupabaseAdmin,
) -> None:
    user = create_random_user(db)
    data = {"full_name": "Updated", "password": random_lower_string()}

    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated"
    assert fake_supabase_admin.updated_users[-1]["password"] == data["password"]


def test_update_user_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json={"full_name": "Updated"},
    )

    assert r.status_code == 404


def test_update_user_existing_email_conflict(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = create_random_user(db)
    existing = create_random_user(db)

    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json={"email": existing.email},
    )

    assert r.status_code == 409


def test_update_user_returns_supabase_error(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    fake_supabase_admin: FakeSupabaseAdmin,
) -> None:
    fake_supabase_admin.raise_on_update = True
    user = create_random_user(db)

    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json={"full_name": "Updated"},
    )

    assert r.status_code == 400
    assert r.json()["detail"] == "update failed"


def test_delete_user(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    fake_supabase_admin: FakeSupabaseAdmin,
) -> None:
    user = create_random_user(db)
    user_id = user.id

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    db.expire_all()
    assert db.get(User, user_id) is None
    assert fake_supabase_admin.deleted_user_ids == [user_id]


def test_delete_user_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_delete_user_rejects_current_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/users/{settings.FIRST_SUPERUSER_ID}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 403


def test_delete_user_returns_supabase_error(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    fake_supabase_admin: FakeSupabaseAdmin,
) -> None:
    fake_supabase_admin.raise_on_delete = True
    user = create_random_user(db)

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 400
    assert r.json()["detail"] == "delete failed"
