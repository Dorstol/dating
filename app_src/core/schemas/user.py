from typing import Optional

from fastapi_users import schemas
from pydantic import Field, validator

from core.models import GenderEnum, InterestEnum
from core.types.user_id import UserIdType


class UserRead(schemas.BaseUser[UserIdType]):
    """
        Schema for reading user information.
        The secret/internal fields are excluded from the serialized output.
    """
    first_name: str
    last_name: str
    gender: Optional[GenderEnum]
    interest: Optional[InterestEnum]
    bio: Optional[str]
    age: Optional[int]
    photo: Optional[str]
    location: Optional[str]
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
    interest: InterestEnum
    age: int
    photo: str
    location: str
    is_active: bool = Field(default=True, exclude=True)
    is_superuser: bool = Field(default=False, exclude=True)
    is_verified: bool = Field(default=False, exclude=True)

    @validator("age")
    def age_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Age must be a positive integer.")
        return v
    
    @validator("age")
    def age_must_be_between_16_and_100(cls, v):
        if v < 16 or v > 100:
            raise ValueError("Age must be between 16 and 100.")
        return v


class UserUpdate(schemas.BaseUserUpdate):
    """
        Schema for updating an existing user.
        Only the fields that need to be updated are provided, all others are optional.
    """
    gender: Optional[GenderEnum] = None
    interest: Optional[InterestEnum] = None
    bio: Optional[str] = None
    age: Optional[int] = None
