from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models import User, db_helper
from core.schemas.match import MatchResponse
from core.schemas.pagination import PaginatedResponse
from core.schemas.user import UserRead
from crud.services.cache_service import CacheService
from crud.services.matches_service import MatchingService

from .fastapi_users import current_user

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix=settings.api.v1.matches,
    tags=["Matches"],
)


@router.get(
    "/suggestion",
    response_model=PaginatedResponse[UserRead],
    summary="Get match suggestions",
    description="Get a list of potential matches for the current user based on interests and ratings",
)
@limiter.limit(settings.rate_limit.suggestion)
async def suggest_matches(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Get potential matches for the current user."""
    cached = await CacheService.get_json("suggestions", user.id, limit, offset)
    if cached is not None:
        return JSONResponse(content=cached)

    items, total = await MatchingService.find_matches_by_interests_and_rating(
        session=session,
        user=user,
        limit=limit,
        offset=offset,
    )
    serialized_items = [UserRead.model_validate(u, from_attributes=True) for u in items]
    response = PaginatedResponse(items=serialized_items, total=total, limit=limit, offset=offset)
    await CacheService.set_json(
        response.model_dump(mode="json"),
        "suggestions",
        user.id,
        limit,
        offset,
        ttl=settings.cache.suggestions_ttl,
    )
    return response


@router.post(
    "/{matched_user_id}",
    response_model=MatchResponse,
    summary="Like a user",
    description="Like another user and potentially create a match if mutual",
)
@limiter.limit(settings.rate_limit.like)
async def like_user(
    request: Request,
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

    result = await MatchingService.process_like(
        session=session,
        user=user,
        matched_user_id=matched_user_id,
    )
    return result


@router.get(
    "",
    response_model=PaginatedResponse[MatchResponse],
    summary="Get user matches",
    description="Get all matches for the current user",
)
async def get_matches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """Get all matches for the current user."""
    items, total = await MatchingService.get_user_matches(
        session=session,
        user_id=user.id,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
