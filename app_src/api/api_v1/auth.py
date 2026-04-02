from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.authentication.backend import authentication_backend
from api.dependencies.authentication.strategy import get_database_strategy
from core.config import settings
from core.models import db_helper
from core.schemas.user import UserCreate, UserRead
from crud.services.telegram_auth_service import TelegramAuthService

from .fastapi_users import fastapi_users

router = APIRouter(
    prefix=settings.api.v1.auth,
    tags=["Auth"],
)
# /login & /logout
router.include_router(
    router=fastapi_users.get_auth_router(
        authentication_backend,
    ),
)
# /register
router.include_router(
    fastapi_users.get_register_router(
        UserRead,
        UserCreate,
    ),
)


class TelegramAuthRequest(BaseModel):
    init_data: str


@router.post(
    "/telegram",
    summary="Authenticate via Telegram WebApp",
)
async def telegram_auth(
    body: TelegramAuthRequest,
    session: AsyncSession = Depends(db_helper.session_getter),
    strategy=Depends(get_database_strategy),
):
    """Validate Telegram initData and return access token."""
    try:
        telegram_user = TelegramAuthService.validate_init_data(body.init_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    user = await TelegramAuthService.get_or_create_user(session, telegram_user)
    token = await strategy.write_token(user)
    return {"access_token": token, "token_type": "bearer"}
