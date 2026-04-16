"""Shared fixtures for unit tests."""

import os

os.environ.setdefault(
    "APP_CONFIG__DB__URL",
    "postgresql+asyncpg://user:pwd@localhost:5432/test",
)
os.environ.setdefault(
    "APP_CONFIG__ACCESS_TOKEN__RESET_PASSWORD_TOKEN_SECRET", "test-secret"
)
os.environ.setdefault(
    "APP_CONFIG__ACCESS_TOKEN__VERIFICATION_TOKEN_SECRET", "test-secret"
)

import pytest

from core.models import Interest, User
from core.models.enums import GenderEnum


@pytest.fixture
def make_user():
    """Factory fixture for creating User instances."""

    def _make_user(
        id=1,
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        gender=GenderEnum.Male,
        age=25,
        location="New York",
        rating=5,
        is_active=True,
        interests=None,
        hashed_password="hashed",
    ):
        user = User(
            id=id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            age=age,
            location=location,
            rating=rating,
            is_active=is_active,
            hashed_password=hashed_password,
        )
        user.interests = interests or []
        return user

    return _make_user


@pytest.fixture
def make_interest():
    """Factory fixture for creating Interest instances."""

    def _make_interest(id=1, name="Photography"):
        return Interest(id=id, name=name)

    return _make_interest


@pytest.fixture
def sample_interests(make_interest):
    """A set of common interests."""
    return [
        make_interest(id=1, name="Photography"),
        make_interest(id=2, name="Travel"),
        make_interest(id=3, name="Music"),
    ]
