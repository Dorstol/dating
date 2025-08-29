from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.api_v1.fastapi_users import current_user
from core.config import settings
from core.models import User, db_helper
from core.schemas.interest import (
    InterestRead,
    UserInterestsResponse,
    UserInterestsUpdate,
)
from crud.services.interest_service import InterestService

router = APIRouter(
    prefix=settings.api.v1.interests,
    tags=["Interests"],
)


@router.get("/popular", response_model=list[InterestRead])
async def get_popular_interests(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Получить популярные интересы"""
    interests = await InterestService.get_popular_interests(session, limit)
    return interests


@router.get("/search", response_model=list[InterestRead])
async def search_interests(
    q: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Поиск интересов по названию"""
    interests = await InterestService.search_interests(session, q, limit)
    return interests


@router.get("/my", response_model=UserInterestsResponse)
async def get_my_interests(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Получить интересы текущего пользователя"""
    # Перезагружаем пользователя с интересами
    result = await session.execute(
        select(User).options(selectinload(User.interests)).where(User.id == user.id)
    )
    user_with_interests = result.scalar_one()

    return UserInterestsResponse(
        interests=user_with_interests.interests,
        count=len(user_with_interests.interests),
    )


@router.put("/my", response_model=UserInterestsResponse)
async def update_my_interests(
    interests_data: UserInterestsUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Обновить интересы текущего пользователя"""
    try:
        interests = await InterestService.update_user_interests(
            session, user, interests_data.interests
        )

        return UserInterestsResponse(interests=interests, count=len(interests))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
