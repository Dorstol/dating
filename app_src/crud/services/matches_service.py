from fastapi import Depends
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_user
from core.models import Match, User
from core.models.associations import user_interests
from core.types.user_id import UserIdType


class MatchingService:
    """Service class for handling matching logic and operations."""

    @staticmethod
    async def find_matches_by_interests_and_rating(
        session: AsyncSession, user: User, limit: int = 20
    ) -> list[User]:
        """
        Find potential matches based on common interests and sorted by rating.

        Algorithm:
        1. Find users with common interests
        2. Sort by rating (higher rating = higher priority)
        3. Apply basic filtering (different gender, active users, etc.)
        """
        if not user.interests:
            # If user has no interests, fall back to basic matching
            return await MatchingService._find_basic_matches(session, user, limit)

        # Get user interest IDs for efficient querying
        user_interest_ids = [interest.id for interest in user.interests]

        # Find users with common interests, sorted by rating (desc) and number of common interests
        query = (
            select(User)
            .join(user_interests, User.id == user_interests.c.user_id)
            .where(
                and_(
                    User.gender != user.gender,
                    User.id != user.id,
                    User.is_active.is_(True),
                    user_interests.c.interest_id.in_(user_interest_ids),
                )
            )
            .group_by(User.id)
            .order_by(
                func.count(
                    user_interests.c.interest_id
                ).desc(),  # More common interests first
                User.rating.desc(),  # Higher rating second
                User.created_at.desc(),  # Newer users third
            )
            .limit(limit)
        )

        result = await session.execute(query)
        matched_users = result.scalars().all()

        # If we don't have enough matches with common interests,
        # fill the remaining slots with basic matches
        if len(matched_users) < limit:
            remaining_limit = limit - len(matched_users)
            matched_user_ids = [u.id for u in matched_users]

            basic_matches = await MatchingService._find_basic_matches(
                session, user, remaining_limit, exclude_ids=matched_user_ids
            )
            matched_users.extend(basic_matches)

        return matched_users

    @staticmethod
    async def _find_basic_matches(
        session: AsyncSession,
        user: User,
        limit: int,
        exclude_ids: list[int] | None = None,
    ) -> list[User]:
        """Find basic matches without interest filtering, sorted by rating."""
        query = select(User).where(
            and_(
                User.gender != user.gender, User.id != user.id, User.is_active.is_(True)
            )
        )

        if exclude_ids:
            query = query.where(User.id.notin_(exclude_ids))

        query = query.order_by(
            User.rating.desc(),  # Higher rating first
            User.created_at.desc(),  # Newer users second
        ).limit(limit)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def _get_existing_match(
        session: AsyncSession, user_id: UserIdType, matched_user_id: UserIdType
    ) -> Match | None:
        """Check if a match already exists between two users."""
        result = await session.execute(
            select(Match).where(
                or_(
                    and_(
                        Match.user_id == matched_user_id,
                        Match.matched_user_id == user_id,
                    ),
                    and_(
                        Match.user_id == user_id,
                        Match.matched_user_id == matched_user_id,
                    ),
                )
            )
        )
        return result.scalars().first()

    @staticmethod
    async def _get_user_by_id(session: AsyncSession, user_id: UserIdType) -> User:
        """Get user by ID with error handling."""
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        return user

    @staticmethod
    async def process_like(
        session: AsyncSession, user: User, matched_user_id: UserIdType
    ) -> Match:
        """
        Process a like action between users.

        This method:
        1. Validates the like action
        2. Increments the liked user's rating
        3. Creates or updates match records
        4. Handles mutual match logic
        """
        # Validation
        if user.id == matched_user_id:
            raise ValueError("Cannot match with yourself")

        # Get the user being liked
        matched_user = await MatchingService._get_user_by_id(session, matched_user_id)

        # Check for existing match
        existing_match = await MatchingService._get_existing_match(
            session, user.id, matched_user_id
        )

        if existing_match:
            return await MatchingService._handle_existing_match(
                session, existing_match, user, matched_user
            )

        # Create new match and increment rating
        return await MatchingService._create_new_match(session, user, matched_user)

    @staticmethod
    async def _handle_existing_match(
        session: AsyncSession, existing_match: Match, user: User, matched_user: User
    ) -> Match:
        """Handle cases where a match already exists."""
        if existing_match.user_id == matched_user.id:
            # The other user already liked us - make it mutual
            existing_match.is_mutual = True

            # Increment ratings for both users when match becomes mutual
            user.increment_rating()
            matched_user.increment_rating()

            # Create the reverse match
            reverse_match = Match(
                user_id=user.id,
                matched_user_id=matched_user.id,
                is_mutual=True,
            )
            session.add(reverse_match)
            await session.commit()
            return reverse_match
        else:
            # We already liked this user
            return existing_match

    @staticmethod
    async def _create_new_match(
        session: AsyncSession, user: User, matched_user: User
    ) -> Match:
        """Create a new one-way match."""
        # Increment the liked user's rating
        matched_user.increment_rating()

        # Create new one-way match
        new_match = Match(
            user_id=user.id,
            matched_user_id=matched_user.id,
            is_mutual=False,
        )
        session.add(new_match)
        await session.commit()
        return new_match


# Legacy functions for backward compatibility
async def find_matches(
    session: AsyncSession, user: User = Depends(current_user), limit: int = 20
) -> list[User]:
    """
    Find potential matches for a user.

    Uses the new matching algorithm based on common interests and ratings.
    """
    return await MatchingService.find_matches_by_interests_and_rating(
        session, user, limit
    )


async def process_match(
    session: AsyncSession,
    matched_user_id: UserIdType,
    user: User = Depends(current_user),
) -> Match:
    """
    Process a match (like) action.

    Uses the new service-based approach for better maintainability.
    """
    return await MatchingService.process_like(session, user, matched_user_id)
