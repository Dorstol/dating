from datetime import datetime

from sqlalchemy import func, Enum
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .enums import GenderEnum, InterestEnum
from .mixins.int_id_pk import IntIdPkMixin


class User(IntIdPkMixin, Base):
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum))
    # photo
    age: Mapped[int] = mapped_column(nullable=True)
    bio: Mapped[str] = mapped_column(nullable=True)
    interest: Mapped[InterestEnum] = mapped_column(Enum(InterestEnum))