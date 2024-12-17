from typing import Optional

from fastapi_users import schemas
from pydantic import Field

from core.models import GenderEnum, InterestEnum
from core.types.user_id import UserIdType


class UserRead(schemas.BaseUser[UserIdType]):
    gender: Optional[GenderEnum]
    interest: Optional[InterestEnum]
    bio: Optional[str]
    age: Optional[int]
    is_active: bool = Field(exclude=True)
    is_superuser: bool = Field(exclude=True)
    is_verified: bool = Field(exclude=True)


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    gender: Optional[GenderEnum] = None
    interest: Optional[InterestEnum] = None
    bio: Optional[str] = None
    age: Optional[int] = None
