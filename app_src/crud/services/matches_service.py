from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Match, User
from core.models.associations import user_interests
from core.types.user_id import UserIdType
from crud.services.cache_service import CacheService
from crud.services.block_report_service import BlockReportService
from crud.services.notification_service import NotificationService


class MatchingService:
    """Service class for handling matching logic and operations."""

    @staticmethod
    async def find_matches_by_interests_and_rating(
        session: AsyncSession,
        user: User,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[User], int]:
        """
        Find potential matches based on common interests and sorted by rating.

        Returns:
            Tuple of (matched users list, total count).
        """
        # Получаем ID заблокированных пользователей (в обе стороны)
        blocked_ids = await BlockReportService.get_blocked_user_ids(session, user.id)

        # Получаем ID уже лайкнутых пользователей
        liked_result = await session.execute(
            select(Match.matched_user_id).where(Match.user_id == user.id)
        )
        liked_ids = [row[0] for row in liked_result]

        gender_filter = User.gender != user.gender if user.gender else True
        base_filter = and_(
            gender_filter,
            User.id != user.id,
            User.is_active.is_(True),
        )
        if blocked_ids:
            base_filter = and_(base_filter, User.id.notin_(blocked_ids))
        if liked_ids:
            base_filter = and_(base_filter, User.id.notin_(liked_ids))

        # Total count of all potential matches
        total_result = await session.execute(
            select(func.count()).select_from(User).where(base_filter)
        )
        total = total_result.scalar() or 0

        if not user.interests:
            matches = await MatchingService._find_basic_matches(
                session, user, limit, offset=offset, blocked_ids=blocked_ids,
                liked_ids=liked_ids,
            )
            return matches, total

        user_interest_ids = [interest.id for interest in user.interests]

        query = (
            select(User)
            .join(user_interests, User.id == user_interests.c.user_id)
            .where(
                and_(
                    base_filter,
                    user_interests.c.interest_id.in_(user_interest_ids),
                )
            )
            .group_by(User.id)
            .order_by(
                func.count(user_interests.c.interest_id).desc(),
                User.rating.desc(),
                User.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)
        matched_users = list(result.scalars().all())

        # Fill remaining slots with basic matches if needed
        if len(matched_users) < limit:
            remaining_limit = limit - len(matched_users)
            matched_user_ids = [u.id for u in matched_users]

            basic_matches = await MatchingService._find_basic_matches(
                session,
                user,
                remaining_limit,
                exclude_ids=matched_user_ids,
                blocked_ids=blocked_ids,
                liked_ids=liked_ids,
            )
            matched_users.extend(basic_matches)

        return matched_users, total

    @staticmethod
    async def _find_basic_matches(
        session: AsyncSession,
        user: User,
        limit: int,
        exclude_ids: list[int] | None = None,
        offset: int = 0,
        blocked_ids: list[int] | None = None,
        liked_ids: list[int] | None = None,
    ) -> list[User]:
        """Find basic matches without interest filtering, sorted by rating."""
        gender_filter = User.gender != user.gender if user.gender else True
        query = select(User).where(
            and_(
                gender_filter, User.id != user.id, User.is_active.is_(True)
            )
        )

        if exclude_ids:
            query = query.where(User.id.notin_(exclude_ids))

        if blocked_ids:
            query = query.where(User.id.notin_(blocked_ids))

        if liked_ids:
            query = query.where(User.id.notin_(liked_ids))

        query = (
            query.order_by(
                User.rating.desc(),
                User.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)
        return list(result.scalars().all())

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

        # Проверяем блокировку в обе стороны
        blocked_ids = await BlockReportService.get_blocked_user_ids(session, user.id)
        if matched_user_id in blocked_ids:
            raise ValueError("Cannot like a blocked user")

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
            # The other user already liked us - make it mutual.
            # We update the single existing record so both users share the same match_id
            # (creating a reverse record would give each user a different id → broken chat).
            existing_match.is_mutual = True

            # Increment ratings for both users when match becomes mutual
            user.increment_rating()
            matched_user.increment_rating()

            await session.commit()

            await CacheService.invalidate_suggestions(user.id)
            await CacheService.invalidate_suggestions(matched_user.id)

            # Notify both users about mutual match
            await NotificationService.notify_mutual_match(
                user.telegram_id,
                matched_user.first_name,
            )
            await NotificationService.notify_mutual_match(
                matched_user.telegram_id,
                user.first_name,
            )

            return existing_match
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

        await CacheService.invalidate_suggestions(user.id)
        await CacheService.invalidate_suggestions(matched_user.id)
        return new_match

    @staticmethod
    async def get_user_matches(
        session: AsyncSession,
        user_id: UserIdType,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Match], int]:
        """Get paginated matches for a user with total count.

        Uses min(id) per canonical pair so that both participants always see
        the same match_id — required for the shared WebSocket chat channel.
        """
        from sqlalchemy.orm import joinedload

        # Subquery: canonical (min) match id per unique pair.
        # Includes matches where the user is liker (user_id) OR liked in a
        # mutual match (matched_user_id). Deduplicates legacy reverse records.
        canonical_subq = (
            select(func.min(Match.id).label("canonical_id"))
            .where(
                or_(
                    Match.user_id == user_id,
                    and_(
                        Match.matched_user_id == user_id,
                        Match.is_mutual.is_(True),
                    ),
                )
            )
            .group_by(
                func.least(Match.user_id, Match.matched_user_id),
                func.greatest(Match.user_id, Match.matched_user_id),
            )
        ).subquery()

        # Total count
        total_result = await session.execute(
            select(func.count()).select_from(canonical_subq)
        )
        total = total_result.scalar() or 0

        # Paginated results
        query = (
            select(Match)
            .join(canonical_subq, Match.id == canonical_subq.c.canonical_id)
            .options(joinedload(Match.matched_user))
            .order_by(Match.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        matches = list(result.scalars().all())

        return matches, total
