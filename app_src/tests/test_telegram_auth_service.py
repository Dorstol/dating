"""Unit tests for TelegramAuthService."""

import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import quote, urlencode

import pytest

from core.models import User
from crud.services.telegram_auth_service import TelegramAuthService

BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


def _make_init_data(
    user_data: dict,
    bot_token: str = BOT_TOKEN,
    auth_date: int | None = None,
    tamper_hash: bool = False,
) -> str:
    """Build a valid Telegram initData string."""
    if auth_date is None:
        auth_date = int(time.time())

    user_json = json.dumps(user_data, separators=(",", ":"))
    params = {
        "user": user_json,
        "auth_date": str(auth_date),
    }

    # Build data check string
    data_pairs = sorted(f"{k}={v}" for k, v in params.items())
    data_check_string = "\n".join(data_pairs)

    # Compute hash
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if tamper_hash:
        computed_hash = "0" * 64

    params["hash"] = computed_hash
    return urlencode(params, quote_via=quote)


class TestValidateInitData:
    @patch("crud.services.telegram_auth_service.settings")
    def test_valid_init_data(self, mock_settings):
        mock_settings.BOT_TOKEN = BOT_TOKEN
        user_data = {"id": 12345, "first_name": "John"}

        result = TelegramAuthService.validate_init_data(
            _make_init_data(user_data)
        )

        assert result["id"] == 12345
        assert result["first_name"] == "John"

    @patch("crud.services.telegram_auth_service.settings")
    def test_missing_hash_raises(self, mock_settings):
        mock_settings.BOT_TOKEN = BOT_TOKEN

        with pytest.raises(ValueError, match="Missing hash"):
            TelegramAuthService.validate_init_data("user=%7B%7D&auth_date=123")

    @patch("crud.services.telegram_auth_service.settings")
    def test_expired_init_data_raises(self, mock_settings):
        mock_settings.BOT_TOKEN = BOT_TOKEN
        user_data = {"id": 12345, "first_name": "John"}
        old_time = int(time.time()) - 600  # 10 minutes ago

        with pytest.raises(ValueError, match="expired"):
            TelegramAuthService.validate_init_data(
                _make_init_data(user_data, auth_date=old_time)
            )

    @patch("crud.services.telegram_auth_service.settings")
    def test_invalid_signature_raises(self, mock_settings):
        mock_settings.BOT_TOKEN = BOT_TOKEN
        user_data = {"id": 12345, "first_name": "John"}

        with pytest.raises(ValueError, match="Invalid initData signature"):
            TelegramAuthService.validate_init_data(
                _make_init_data(user_data, tamper_hash=True)
            )

    @patch("crud.services.telegram_auth_service.settings")
    def test_missing_bot_token_raises(self, mock_settings):
        mock_settings.BOT_TOKEN = ""

        with pytest.raises(ValueError, match="BOT_TOKEN"):
            TelegramAuthService.validate_init_data("anything")

    @patch("crud.services.telegram_auth_service.settings")
    def test_missing_user_raises(self, mock_settings):
        mock_settings.BOT_TOKEN = BOT_TOKEN
        auth_date = str(int(time.time()))

        # Build initData without user field
        params = {"auth_date": auth_date}
        data_check_string = f"auth_date={auth_date}"
        secret_key = hmac.new(
            b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
        ).digest()
        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        params["hash"] = computed_hash

        with pytest.raises(ValueError, match="Missing user"):
            TelegramAuthService.validate_init_data(urlencode(params))


class TestGetOrCreateUser:
    async def test_returns_existing_user(self):
        session = AsyncMock()
        existing_user = User(
            id=1,
            telegram_id=12345,
            email="tg_12345@telegram.local",
            hashed_password="",
            first_name="John",
            last_name="Doe",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        session.execute.return_value = mock_result

        result = await TelegramAuthService.get_or_create_user(
            session, {"id": 12345, "first_name": "John", "last_name": "Doe"}
        )

        assert result is existing_user
        session.add.assert_not_called()

    async def test_creates_new_user(self):
        session = AsyncMock()
        session.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await TelegramAuthService.get_or_create_user(
            session,
            {"id": 99999, "first_name": "Alice", "last_name": "Smith"},
        )

        assert result.telegram_id == 99999
        assert result.first_name == "Alice"
        assert result.last_name == "Smith"
        assert result.email == "tg_99999@telegram.local"
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    async def test_creates_user_without_last_name(self):
        session = AsyncMock()
        session.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await TelegramAuthService.get_or_create_user(
            session,
            {"id": 88888, "first_name": "Bob"},
        )

        assert result.first_name == "Bob"
        assert result.last_name == ""
