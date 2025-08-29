from datetime import datetime
from typing import TYPE_CHECKING

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.types.user_id import UserIdType

from .base import Base
from .enums import GenderEnum
from .mixins.int_id_pk import IntIdPkMixin

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from .interest import Interest


class User(Base, IntIdPkMixin, SQLAlchemyBaseUserTable[UserIdType]):
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    gender: Mapped[GenderEnum] = mapped_column(
        Enum(GenderEnum),
        nullable=True,
        default=GenderEnum.OTHER,
    )
    photo: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    location: Mapped[str] = mapped_column(nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    bio: Mapped[str] = mapped_column(nullable=True)

    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # Связь с интересами (многие-ко-многим)
    interests: Mapped[list["Interest"]] = relationship(
        "Interest",
        secondary="user_interests",
        back_populates="users",
        lazy="selectin",
    )

    @classmethod
    def get_db(cls, session: "AsyncSession"):
        return SQLAlchemyUserDatabase(session, cls)

    def get_interests_names(self) -> list[str]:
        """Получить список названий интересов пользователя"""
        return [interest.name for interest in self.interests]

    def has_interest(self, interest_name: str) -> bool:
        """Проверить, есть ли у пользователя определенный интерес"""
        return any(
            interest.name.lower() == interest_name.lower()
            for interest in self.interests
        )

    def increment_rating(self) -> None:
        """Увеличить рейтинг пользователя"""
        self.rating += 1

    def decrement_rating(self) -> None:
        """Уменьшить рейтинг пользователя"""
        self.rating = max(0, self.rating - 1)
