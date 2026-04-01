"""Unit tests for password validation in UserManager."""

import pytest
from fastapi import HTTPException

from core.authentication.user_manager import UserManager
from core.models import User


class TestPasswordValidation:
    @pytest.fixture
    def user_manager(self):
        return UserManager.__new__(UserManager)

    @pytest.fixture
    def user(self, make_user):
        return make_user(email="test@example.com")

    async def test_valid_password(self, user_manager, user):
        await user_manager.validate_password("StrongPass1", user)

    async def test_too_short(self, user_manager, user):
        with pytest.raises(HTTPException, match="at least 8 characters"):
            await user_manager.validate_password("Short1A", user)

    async def test_too_long(self, user_manager, user):
        password = "A" * 127 + "a1"
        with pytest.raises(HTTPException, match="not exceed 128"):
            await user_manager.validate_password(password, user)

    async def test_exactly_max_length(self, user_manager, user):
        password = "A" * 63 + "a" * 63 + "1" + "x"
        assert len(password) == 128
        await user_manager.validate_password(password, user)

    async def test_no_uppercase(self, user_manager, user):
        with pytest.raises(HTTPException, match="uppercase"):
            await user_manager.validate_password("lowercase1", user)

    async def test_no_lowercase(self, user_manager, user):
        with pytest.raises(HTTPException, match="lowercase"):
            await user_manager.validate_password("UPPERCASE1", user)

    async def test_no_digit(self, user_manager, user):
        with pytest.raises(HTTPException, match="digit"):
            await user_manager.validate_password("NoDigitHere", user)

    async def test_contains_whitespace(self, user_manager, user):
        with pytest.raises(HTTPException, match="whitespace"):
            await user_manager.validate_password("Strong Pass1", user)

    async def test_contains_tab(self, user_manager, user):
        with pytest.raises(HTTPException, match="whitespace"):
            await user_manager.validate_password("Strong\tPass1", user)

    async def test_contains_email(self, user_manager, user):
        with pytest.raises(HTTPException, match="email"):
            await user_manager.validate_password(
                "test@example.comAbc1", user
            )

    async def test_blacklisted_password(self, user_manager, user):
        with pytest.raises(HTTPException, match="too weak"):
            await user_manager.validate_password("Password1A", user)

    async def test_blacklisted_qwerty(self, user_manager, user):
        with pytest.raises(HTTPException, match="too weak"):
            await user_manager.validate_password("Qwerty1Abc", user)

    async def test_blacklisted_123456(self, user_manager, user):
        with pytest.raises(HTTPException, match="too weak"):
            await user_manager.validate_password("Abc123456x", user)

    async def test_blacklisted_letmein(self, user_manager, user):
        with pytest.raises(HTTPException, match="too weak"):
            await user_manager.validate_password("Letmein1Abc", user)

    async def test_min_boundary_8_chars(self, user_manager, user):
        await user_manager.validate_password("Abcdef1x", user)

    async def test_7_chars_rejected(self, user_manager, user):
        with pytest.raises(HTTPException, match="at least 8"):
            await user_manager.validate_password("Abcde1x", user)
