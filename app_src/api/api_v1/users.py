from fastapi import APIRouter

from core.config import settings
from core.schemas.user import UserRead, UserUpdate
from .fastapi_users import fastapi_users

router = APIRouter(
    prefix=settings.api.v1.users,
    tags=["Users"],
)

router.include_router(
    fastapi_users.get_users_router(
        UserRead,
        UserUpdate,
    ),
)
