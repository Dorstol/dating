from fastapi import Depends
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_user
from core.models import User, Match
from core.types.user_id import UserIdType


async def find_matches(
    session: AsyncSession,
    user: User = Depends(current_user),
):
    subquery = exists().where(
        Match.user_id == user.id,
        Match.matched_user_id == User.id
    )

    query = select(User).where(
        User.id != user.id,
        ~subquery
    )

    result = await session.execute(query)
    return result.scalars().all()


async def process_match(
    session: AsyncSession,
    matched_user_id: UserIdType,
    user: User = Depends(current_user),
):
    existing_match = await session.execute(
        select(Match).where(
            Match.user_id == matched_user_id,
            Match.matched_user_id == user.id,
        )
    )

    existing_match = existing_match.scalars().first()

    if existing_match:
        existing_match.is_mutual = True
        await session.commit()

        new_match = Match(
            user_id=user.id,
            matched_user_id=matched_user_id,
            is_mutual=True,
        )
    else:

        new_match = Match(
            user_id=user.id,
            matched_user_id=matched_user_id,
            is_mutual=False,
        )

    session.add(new_match)
    await session.commit()
    return {"match_saved": True, "is_mutual": bool(existing_match)}


async def save_match(
    matched_user_id: UserIdType,
    is_mutual: bool,
    session: AsyncSession,
    user: User = Depends(current_user),
):
    match = Match(user_id=user.id, matched_user_id=matched_user_id, is_mutual=is_mutual)
    session.add(match)
    await session.commit()
    return match
