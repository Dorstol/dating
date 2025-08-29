from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.config import settings
from core.models import Match, User, db_helper
from core.schemas.match import MatchResponse
from core.schemas.user import UserRead
from crud.services.matches_service import find_matches, process_match

from .fastapi_users import current_user

router = APIRouter(
    prefix=settings.api.v1.matches,
    tags=["Matches"],
)


@router.get(
    "/suggestion",
    response_model=list[UserRead],
    summary="Get match suggestions",
    description="Get a list of potential matches for the current user based on interests and ratings",
)
async def suggest_matches(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Get potential matches for the current user."""
    matches = await find_matches(
        session=session,
        user=user,
    )
    return matches


@router.post(
    "/{matched_user_id}",
    response_model=MatchResponse,
    summary="Like a user",
    description="Like another user and potentially create a match if mutual",
)
async def like_user(
    matched_user_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Like another user and create a match."""
    if user.id == matched_user_id:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Cannot match with yourself",
        )

    result = await process_match(
        user=user,
        matched_user_id=matched_user_id,
        session=session,
    )
    return result


@router.get(
    "",
    response_model=list[MatchResponse],
    summary="Get user matches",
    description="Get all matches for the current user",
)
async def get_matches(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Get all matches for the current user."""
    query = (
        select(Match)
        .where(Match.user_id == user.id)
        .options(joinedload(Match.matched_user))
    )
    result = await session.execute(query)
    matches = result.scalars().all()
    return matches
