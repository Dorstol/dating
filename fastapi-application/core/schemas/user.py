from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from core.models import GenderEnum, InterestEnum


class UserBase(BaseModel):
    username: str
    email: EmailStr
    gender: Optional[str] = None
    photo: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    interest: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    gender: Optional[GenderEnum] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    interest: Optional[InterestEnum] = None


class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
