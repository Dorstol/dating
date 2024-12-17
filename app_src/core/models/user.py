from datetime import datetime
from typing import TYPE_CHECKING

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import func, Enum
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from core.types.user_id import UserIdType
from .base import Base
from .enums import GenderEnum, InterestEnum
from .mixins.int_id_pk import IntIdPkMixin

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class User(Base, IntIdPkMixin, SQLAlchemyBaseUserTable[UserIdType]):
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    gender: Mapped[GenderEnum] = mapped_column(
        Enum(GenderEnum),
        nullable=True,
        server_default=GenderEnum.none,
    )
    # photo
    age: Mapped[int] = mapped_column(nullable=True)
    bio: Mapped[str] = mapped_column(nullable=True)
    interest: Mapped[InterestEnum] = mapped_column(
        Enum(InterestEnum),
        nullable=True,
        server_default=InterestEnum.none,
    )

    @classmethod
    def get_db(cls, session: "AsyncSession"):
        return SQLAlchemyUserDatabase(session, cls)
