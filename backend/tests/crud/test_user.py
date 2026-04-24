import uuid

from sqlmodel import Session

from app import crud
from app.models import UserUpdate
from tests.utils.utils import random_email, random_lower_string


def test_create_user_profile(db: Session) -> None:
    user_id = uuid.uuid4()
    email = random_email()

    user = crud.create_user_profile(
        session=db,
        user_id=user_id,
        email=email,
        full_name="Test User",
        is_superuser=True,
    )

    assert user.id == user_id
    assert user.email == email
    assert user.full_name == "Test User"
    assert user.is_superuser is True


def test_get_user_by_email(db: Session) -> None:
    email = random_email()
    crud.create_user_profile(session=db, user_id=uuid.uuid4(), email=email)

    user = crud.get_user_by_email(session=db, email=email)

    assert user
    assert user.email == email


def test_update_user_profile(db: Session) -> None:
    user = crud.create_user_profile(
        session=db,
        user_id=uuid.uuid4(),
        email=random_email(),
    )
    new_email = random_email()
    new_name = random_lower_string()

    updated = crud.update_user(
        session=db,
        db_user=user,
        user_in=UserUpdate(email=new_email, full_name=new_name, is_active=False),
    )

    assert updated.email == new_email
    assert updated.full_name == new_name
    assert updated.is_active is False
