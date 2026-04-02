from pydantic import BaseModel, Field

from core.models.enums import ReportReasonEnum
from core.types.user_id import UserIdType


class ReportCreate(BaseModel):
    reason: ReportReasonEnum
    description: str | None = Field(None, max_length=500)


class ReportResponse(BaseModel):
    id: int
    user_id: UserIdType
    reported_user_id: UserIdType
    reason: ReportReasonEnum
    description: str | None

    class Config:
        from_attributes = True
