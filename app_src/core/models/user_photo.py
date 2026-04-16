from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.types.user_id import UserIdType

from .base import Base
from .mixins.int_id_pk import IntIdPkMixin


class UserPhoto(Base, IntIdPkMixin):
    __tablename__ = "user_photos"

    user_id: Mapped[UserIdType] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship("User", back_populates="photos")  # noqa: F821
