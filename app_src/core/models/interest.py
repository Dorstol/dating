from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.int_id_pk import IntIdPkMixin

if TYPE_CHECKING:
    from .user import User


class Interest(Base, IntIdPkMixin):
    """Модель для хранения интересов/тегов"""

    __tablename__ = "interests"

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    # Связь с пользователями (используем строковое имя для избежания циклического импорта)
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_interests",
        back_populates="interests",
    )

    def __repr__(self):
        return f"<Interest(id={self.id}, name='{self.name}')>"
