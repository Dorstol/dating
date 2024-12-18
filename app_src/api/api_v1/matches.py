from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.config import settings
from core.models import User, Match, db_helper
from core.schemas.match import MatchResponse
from core.schemas.user import UserRead
from crud.matches import find_matches, process_match
from .fastapi_users import current_user

router = APIRouter(
    prefix=settings.api.v1.matches,
    tags=["Matches"],
)


@router.get(
    "/suggestion",
    response_model=List[UserRead],
)
async def suggest_matches(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    matches = await find_matches(
        session=session,
        user=user,
    )
    return matches


@router.post(
    "/{matched_user_id}",
    response_model=MatchResponse,
)
async def like_user(
    matched_user_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    if user.id == matched_user_id:
        raise HTTPException(status_code=405, detail="can`t like yourself")

    result = await process_match(
        user=user,
        matched_user_id=matched_user_id,
        session=session,
    )
    return result


@router.get(
    "",
    response_model=List[MatchResponse],
)
async def get_matches(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    query = (
        select(Match)
        .where(Match.user_id == user.id)
        .options(joinedload(Match.matched_user))
    )
    result = await session.execute(query)
    matches = result.scalars().all()
    return matches
