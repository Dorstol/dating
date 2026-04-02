from pydantic import BaseModel

from core.types.user_id import UserIdType


class BlockResponse(BaseModel):
    id: int
    user_id: UserIdType
    blocked_user_id: UserIdType

    class Config:
        from_attributes = True
