from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Interest, User


class InterestService:
    """Service class for handling interest-related operations."""

    @staticmethod
    async def get_or_create_interests(
        session: AsyncSession, interest_names: list[str]
    ) -> list[Interest]:
        """
        Get existing interests or create new ones if they don't exist.

        Args:
            session: Database session
            interest_names: List of interest names to get or create

        Returns:
            List of Interest objects
        """
        if not interest_names:
            return []

        # Normalize and filter out empty names
        normalized_names = [
            name.strip().lower() for name in interest_names if name.strip()
        ]

        if not normalized_names:
            return []

        # Get existing interests
        existing_interests = await session.execute(
            select(Interest).where(func.lower(Interest.name).in_(normalized_names))
        )
        existing_interests = existing_interests.scalars().all()

        # Create a set of existing names for efficient lookup
        existing_names = {interest.name.lower() for interest in existing_interests}

        # Create new interests for names that don't exist
        new_interests = []
        for name in interest_names:
            cleaned_name = name.strip()
            normalized_name = cleaned_name.lower()

            if normalized_name and normalized_name not in existing_names:
                new_interest = Interest(name=cleaned_name)
                session.add(new_interest)
                new_interests.append(new_interest)
                # Add to existing_names to avoid duplicates in the same batch
                existing_names.add(normalized_name)

        # Flush to get IDs for new interests
        if new_interests:
            await session.flush()

        return existing_interests + new_interests

    @staticmethod
    async def get_popular_interests(
        session: AsyncSession, limit: int = 20
    ) -> list[Interest]:
        """
        Get popular interests based on user count.

        Args:
            session: Database session
            limit: Maximum number of interests to return

        Returns:
            List of Interest objects ordered by popularity
        """
        from core.models import user_interests

        # TODO: Add caching for better performance

        result = await session.execute(
            select(Interest)
            .outerjoin(user_interests)
            .group_by(Interest.id)
            .order_by(func.count(user_interests.c.user_id).desc())
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def search_interests(
        session: AsyncSession, query: str, limit: int = 10
    ) -> list[Interest]:
        """
        Search interests by name using case-insensitive partial matching.

        Args:
            session: Database session
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching Interest objects
        """
        result = await session.execute(
            select(Interest)
            .where(func.lower(Interest.name).contains(query.lower()))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def update_user_interests(
        session: AsyncSession, user: User, interest_names: list[str]
    ) -> list[Interest]:
        """
        Update user's interests with the provided list of interest names.

        Args:
            session: Database session
            user: User object to update
            interest_names: List of interest names to associate with the user

        Returns:
            List of Interest objects now associated with the user
        """
        # Get or create interests
        interests = await InterestService.get_or_create_interests(
            session, interest_names
        )

        # Update user's interest associations
        user.interests = interests

        await session.commit()
        return interests
