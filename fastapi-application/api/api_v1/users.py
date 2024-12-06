from typing import Annotated

from fastapi import (
    APIRouter,
    Depends, HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies.auth import get_current_user
from core.models import db_helper
from core.schemas.user import (
    UserRead,
    UserCreate, UserUpdate,
)
from crud import users as users_crud

router = APIRouter(tags=["Users"])


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: UserRead = Depends(get_current_user)):
    return current_user


@router.get("", response_model=list[UserRead])
async def get_users(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
):
    users = await users_crud.get_all_users(session=session)
    return users


@router.post("", response_model=UserRead)
async def create_user(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
        user_create: UserCreate,
):
    user = await users_crud.create_user(
        session=session,
        user_create=user_create,
    )
    return user


@router.get("/users/{user_id}", response_model=UserRead)
async def read_user(user_id: int, session: AsyncSession = Depends(db_helper.session_getter)):
    user = await users_crud.get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserRead)
async def update_existing_user(user_id: int, user_update: UserUpdate,
                               session: AsyncSession = Depends(db_helper.session_getter)):
    user = await users_crud.update_user(session, user_id, user_update)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}")
async def delete_existing_user(user_id: int, session: AsyncSession = Depends(db_helper.session_getter)):
    success = await users_crud.delete_user(session, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}
