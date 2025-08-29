from fastapi_users import schemas
from pydantic import Field, field_validator

from core.models import GenderEnum
from core.types.user_id import UserIdType

from .interest import InterestRead


class UserRead(schemas.BaseUser[UserIdType]):
    """
    Schema for reading user information.
    The secret/internal fields are excluded from the serialized output.
    """

    first_name: str
    last_name: str
    gender: GenderEnum | None
    interests: list[InterestRead] = []
    bio: str | None
    age: int | None
    photo: str | None
    location: str | None
    is_active: bool = Field(exclude=True)
    is_superuser: bool = Field(exclude=True)
    is_verified: bool = Field(exclude=True)


class UserCreate(schemas.BaseUserCreate):
    """
    Schema for creating a new user.
    Default values are provided for internal fields.
    """

    first_name: str
    last_name: str
    gender: GenderEnum
    age: int
    location: str
    interests: list[str] = Field(default=[], description="List of interest names")
    is_active: bool = Field(default=True, exclude=True)
    is_superuser: bool = Field(default=False, exclude=True)
    is_verified: bool = Field(default=False, exclude=True)

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Age must be a positive integer.")
        if v < 16 or v > 100:
            raise ValueError("Age must be between 16 and 100.")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Name cannot be empty.")
        return v.strip()

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, v: list[str]) -> list[str]:
        if len(v) > 10:
            raise ValueError("Interests list cannot be longer than 10 items")
        return [interest.strip().lower() for interest in v if interest.strip()]


class UserUpdate(schemas.BaseUserUpdate):
    """
    Schema for updating an existing user.
    Only the fields that need to be updated are provided, all others are optional.
    """

    gender: GenderEnum | None = None
    interests: list[str] | None = None
    bio: str | None = None
    age: int | None = None
