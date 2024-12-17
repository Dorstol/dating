from pydantic import BaseModel

from core.types.user_id import UserIdType


class MatchRead(BaseModel):
    id: int
    user_id: UserIdType
    matched_user_id: UserIdType

    class Config:
        from_attributes = True


class MatchCreate(BaseModel):
    matched_user_id: UserIdType
