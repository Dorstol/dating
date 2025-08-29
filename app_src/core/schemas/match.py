from pydantic import BaseModel

from core.types.user_id import UserIdType


class MatchResponse(BaseModel):
    id: int
    user_id: UserIdType
    matched_user_id: UserIdType
    is_mutual: bool


class MatchCreate(BaseModel):
    matched_user_id: UserIdType
