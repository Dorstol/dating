from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.dependencies.auth import oauth2_scheme
from core.models import db_helper
from core.redis_client import store_token_in_redis, revoke_token
from core.schemas.token import Token
from core.security import create_access_token
from crud.users import authenticate_user

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    user = await authenticate_user(
        username=form_data.username, password=form_data.password, session=session
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    ttl_seconds = settings.ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600
    await store_token_in_redis(access_token, ttl_seconds)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    await revoke_token(token)
    return {"detail": "Logged out successfully"}
