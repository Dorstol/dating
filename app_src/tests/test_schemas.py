"""Unit tests for Pydantic schemas validation."""

import pytest
from pydantic import ValidationError

from core.schemas.interest import UserInterestsUpdate
from core.schemas.user import UserCreate


class TestUserCreateSchema:
    def _valid_data(self, **overrides):
        defaults = {
            "email": "test@example.com",
            "password": "StrongPass1",
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "age": 25,
            "location": "New York",
        }
        defaults.update(overrides)
        return defaults

    def test_valid_user(self):
        user = UserCreate(**self._valid_data())
        assert user.email == "test@example.com"
        assert user.age == 25

    def test_age_too_young(self):
        with pytest.raises(ValidationError, match="between 16 and 100"):
            UserCreate(**self._valid_data(age=15))

    def test_age_too_old(self):
        with pytest.raises(ValidationError, match="between 16 and 100"):
            UserCreate(**self._valid_data(age=101))

    def test_age_zero(self):
        with pytest.raises(ValidationError, match="positive integer"):
            UserCreate(**self._valid_data(age=0))

    def test_age_negative(self):
        with pytest.raises(ValidationError, match="positive integer"):
            UserCreate(**self._valid_data(age=-5))

    def test_age_boundary_16(self):
        user = UserCreate(**self._valid_data(age=16))
        assert user.age == 16

    def test_age_boundary_100(self):
        user = UserCreate(**self._valid_data(age=100))
        assert user.age == 100

    def test_empty_first_name(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            UserCreate(**self._valid_data(first_name="   "))

    def test_empty_last_name(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            UserCreate(**self._valid_data(last_name=""))

    def test_name_strips_whitespace(self):
        user = UserCreate(**self._valid_data(first_name="  John  "))
        assert user.first_name == "John"

    def test_interests_max_10(self):
        interests = [f"interest_{i}" for i in range(11)]
        with pytest.raises(ValidationError, match="longer than 10"):
            UserCreate(**self._valid_data(interests=interests))

    def test_interests_within_limit(self):
        interests = [f"interest_{i}" for i in range(10)]
        user = UserCreate(**self._valid_data(interests=interests))
        assert len(user.interests) == 10

    def test_interests_normalized_to_lowercase(self):
        user = UserCreate(**self._valid_data(interests=["Photography", "TRAVEL"]))
        assert user.interests == ["photography", "travel"]

    def test_interests_default_empty(self):
        user = UserCreate(**self._valid_data())
        assert user.interests == []

    def test_invalid_gender(self):
        with pytest.raises(ValidationError):
            UserCreate(**self._valid_data(gender="InvalidGender"))


class TestUserInterestsUpdateSchema:
    def test_valid_interests(self):
        data = UserInterestsUpdate(interests=["music", "travel"])
        assert data.interests == ["music", "travel"]

    def test_empty_interests_rejected(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            UserInterestsUpdate(interests=[])

    def test_too_many_interests(self):
        with pytest.raises(ValidationError, match="longer than 10"):
            UserInterestsUpdate(interests=[f"i{n}" for n in range(11)])

    def test_interests_stripped_and_lowered(self):
        data = UserInterestsUpdate(interests=["  Music  ", "TRAVEL"])
        assert data.interests == ["music", "travel"]

    def test_whitespace_only_interests_filtered(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            UserInterestsUpdate(interests=["   ", "  "])

    def test_long_interest_name_filtered(self):
        long_name = "a" * 51
        data = UserInterestsUpdate(interests=[long_name, "valid"])
        assert data.interests == ["valid"]
