from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_user
from core.models import User, Match
from core.types.user_id import UserIdType


async def find_matches(
    session: AsyncSession,
    user: User = Depends(current_user),
):
    query = select(User).where(
        User.gender != user.gender,
        User.id != user.id,
        User.is_active == True,
    )

    result = await session.execute(query)
    return result.scalars().all()


async def process_match(
    session: AsyncSession,
    matched_user_id: UserIdType,
    user: User = Depends(current_user),
):
    # Check if we're not trying to match with ourselves
    if user.id == matched_user_id:
        raise ValueError("Cannot match with yourself")

    # Check if the match already exists in either direction
    existing_match = await session.execute(
        select(Match).where(
            (
                (Match.user_id == matched_user_id) & 
                (Match.matched_user_id == user.id)
            ) |
            (
                (Match.user_id == user.id) & 
                (Match.matched_user_id == matched_user_id)
            )
        )
    )
    existing_match = existing_match.scalars().first()

    if existing_match:
        if existing_match.user_id == matched_user_id:
            # Other user initiated the match, make it mutual
            existing_match.is_mutual = True
            await session.commit()
            
            # Create the reverse match
            new_match = Match(
                user_id=user.id,
                matched_user_id=matched_user_id,
                is_mutual=True,
            )
            session.add(new_match)
            await session.commit()
            return new_match
        else:
            # We already initiated this match
            return existing_match

    # Create new one-way match
    new_match = Match(
        user_id=user.id,
        matched_user_id=matched_user_id,
        is_mutual=False,
    )
    session.add(new_match)
    await session.commit()
    return new_match
