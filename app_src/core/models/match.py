from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.types.user_id import UserIdType
from .base import Base
from .mixins.int_id_pk import IntIdPkMixin

if TYPE_CHECKING:
    pass


class Match(Base, IntIdPkMixin):
    user_id: Mapped[UserIdType] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    matched_user_id: Mapped[UserIdType] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    # Todo status
    is_mutual: Mapped[bool] = mapped_column(
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
    )
    matched_user = relationship(
        "User",
        foreign_keys=[matched_user_id],
    )
