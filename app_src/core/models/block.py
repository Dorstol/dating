from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.types.user_id import UserIdType

from .base import Base
from .mixins.int_id_pk import IntIdPkMixin

if TYPE_CHECKING:
    pass


class Block(Base, IntIdPkMixin):
    __table_args__ = (
        UniqueConstraint("user_id", "blocked_user_id"),
    )

    user_id: Mapped[UserIdType] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    blocked_user_id: Mapped[UserIdType] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
    )
    blocked_user = relationship(
        "User",
        foreign_keys=[blocked_user_id],
    )
