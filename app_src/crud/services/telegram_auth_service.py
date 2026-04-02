import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs, unquote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models import User


class TelegramAuthService:
    """Service for Telegram WebApp authentication."""

    INIT_DATA_EXPIRY = 300  # 5 minutes

    @staticmethod
    def validate_init_data(init_data: str) -> dict:
        """
        Validate Telegram WebApp initData and return parsed user data.

        Raises ValueError if validation fails.
        """
        if not settings.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not configured")

        parsed = parse_qs(init_data)

        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            raise ValueError("Missing hash in initData")

        # Check auth_date is not too old
        auth_date_str = parsed.get("auth_date", [None])[0]
        if not auth_date_str:
            raise ValueError("Missing auth_date in initData")

        auth_date = int(auth_date_str)
        if time.time() - auth_date > TelegramAuthService.INIT_DATA_EXPIRY:
            raise ValueError("initData has expired")

        # Build data check string: sorted key=value pairs, excluding hash
        data_pairs = []
        for key, values in parsed.items():
            if key == "hash":
                continue
            data_pairs.append(f"{key}={unquote(values[0])}")
        data_pairs.sort()
        data_check_string = "\n".join(data_pairs)

        # Compute HMAC-SHA256
        secret_key = hmac.new(
            b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256
        ).digest()
        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            raise ValueError("Invalid initData signature")

        # Extract user data
        user_data_str = parsed.get("user", [None])[0]
        if not user_data_str:
            raise ValueError("Missing user in initData")

        return json.loads(unquote(user_data_str))

    @staticmethod
    async def get_or_create_user(
        session: AsyncSession, telegram_user: dict
    ) -> User:
        """
        Find existing user by telegram_id or create a new one.

        Returns the User instance.
        """
        telegram_id = telegram_user["id"]

        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is not None:
            return user

        first_name = telegram_user.get("first_name", "")
        last_name = telegram_user.get("last_name", "")

        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            email=f"tg_{telegram_id}@telegram.local",
            hashed_password="",
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
