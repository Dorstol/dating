from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.types.user_id import UserIdType

from .base import Base
from .enums import ReportReasonEnum
from .mixins.int_id_pk import IntIdPkMixin

if TYPE_CHECKING:
    pass


class Report(Base, IntIdPkMixin):
    user_id: Mapped[UserIdType] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    reported_user_id: Mapped[UserIdType] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    reason: Mapped[ReportReasonEnum] = mapped_column(
        Enum(ReportReasonEnum),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
    )
    reported_user = relationship(
        "User",
        foreign_keys=[reported_user_id],
    )
