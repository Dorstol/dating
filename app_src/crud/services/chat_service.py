from sqlalchemy import and_, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Match, Message
from core.types.user_id import UserIdType


class ChatService:
    """Service for chat message operations."""

    @staticmethod
    async def validate_match_participant(
        session: AsyncSession, match_id: int, user_id: UserIdType
    ) -> Match:
        """
        Verify the match exists, is mutual, and user is a participant.

        Raises ValueError if validation fails.
        """
        result = await session.execute(
            select(Match).where(Match.id == match_id)
        )
        match = result.scalar_one_or_none()

        if match is None:
            raise ValueError("Match not found")

        if not match.is_mutual:
            raise ValueError("Match is not mutual")

        if match.user_id != user_id and match.matched_user_id != user_id:
            raise ValueError("User is not a participant of this match")

        return match

    @staticmethod
    async def save_message(
        session: AsyncSession,
        match_id: int,
        sender_id: UserIdType,
        text: str,
    ) -> Message:
        """Save a chat message to the database."""
        message = Message(
            match_id=match_id,
            sender_id=sender_id,
            text=text,
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message

    @staticmethod
    async def get_history(
        session: AsyncSession,
        match_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Message], int]:
        """Get paginated message history for a match."""
        total_result = await session.execute(
            select(func.count())
            .select_from(Message)
            .where(Message.match_id == match_id)
        )
        total = total_result.scalar() or 0

        result = await session.execute(
            select(Message)
            .where(Message.match_id == match_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        messages = list(result.scalars().all())

        return messages, total

    @staticmethod
    async def mark_as_read(
        session: AsyncSession,
        match_id: int,
        reader_id: UserIdType,
    ) -> int:
        """Mark all unread messages in a match as read (except own messages)."""
        result = await session.execute(
            update(Message)
            .where(
                and_(
                    Message.match_id == match_id,
                    Message.sender_id != reader_id,
                    Message.is_read.is_(False),
                )
            )
            .returning(Message.id)
        )
        await session.commit()
        return len(result.all())
