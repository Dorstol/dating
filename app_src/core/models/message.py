from datetime import datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.types.user_id import UserIdType

from .base import Base
from .mixins.int_id_pk import IntIdPkMixin


class Message(Base, IntIdPkMixin):
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matchs.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id: Mapped[UserIdType] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )

    match = relationship("Match", backref="messages")
    sender = relationship("User", foreign_keys=[sender_id])
