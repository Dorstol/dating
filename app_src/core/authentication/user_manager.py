import logging
import re
from typing import Optional, TYPE_CHECKING

from fastapi import HTTPException
from fastapi_users import BaseUserManager, IntegerIDMixin

from core.config import settings
from core.models.user import User
from core.types.user_id import UserIdType

if TYPE_CHECKING:
    from fastapi import Request

log = logging.getLogger(__name__)

class PasswordValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=400, detail=message)

class UserManager(IntegerIDMixin, BaseUserManager[User, UserIdType]):
    reset_password_token_secret = settings.access_token.reset_password_token_secret
    verification_token_secret = settings.access_token.verification_token_secret

    async def validate_password(
        self, password: str, user: User,
    ) -> None:
        """
            Validates a user's password based on predefined rules.

            Args:
                password (str): The password to validate.
                user (User): The user instance (can be used for custom validation).

            Raises:
                PasswordValidationError: If the password doesn't meet the criteria.
            """
        if len(password) < 8:
            raise PasswordValidationError("Password must be at least 8 characters long.")

        if len(password) > 128:
            raise PasswordValidationError("Password must not exceed 128 characters.")

        if not re.search(r"[A-Z]", password):
            raise PasswordValidationError("Password must contain at least one uppercase letter.")

        if not re.search(r"[a-z]", password):
            raise PasswordValidationError("Password must contain at least one lowercase letter.")

        if not re.search(r"\d", password):
            raise PasswordValidationError("Password must contain at least one digit.")

        if re.search(r"\s", password):
            raise PasswordValidationError("Password must not contain whitespace characters.")

        if user.email in password:
            raise PasswordValidationError("Password must not contain your email address.")

        blacklist = ["password", "123456", "qwerty", "letmein"]
        if any(blacklist_word in password.lower() for blacklist_word in blacklist):
            raise PasswordValidationError("Password is too weak or common.")

        return

    async def on_after_register(
        self,
        user: User,
        request: Optional["Request"] = None,
    ):
        log.warning(
            "User %r has registered.",
            user.id,
        )

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional["Request"] = None,
    ):
        log.warning(
            "User %r has forgot their password. Reset token: %r",
            user.id,
            token,
        )

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional["Request"] = None,
    ):
        log.warning(
            "Verification requested for user %r. Verification token: %r",
            user.id,
            token,
        )
