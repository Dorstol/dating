from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Block, Report
from core.models.enums import ReportReasonEnum
from core.types.user_id import UserIdType


class BlockReportService:
    """Service class for handling block and report operations."""

    @staticmethod
    async def block_user(
        session: AsyncSession, user_id: UserIdType, blocked_user_id: UserIdType
    ) -> Block:
        """Block a user."""
        if user_id == blocked_user_id:
            raise ValueError("Cannot block yourself")

        # Check if already blocked
        existing = await BlockReportService.get_block(
            session, user_id, blocked_user_id
        )
        if existing:
            raise ValueError("User is already blocked")

        block = Block(user_id=user_id, blocked_user_id=blocked_user_id)
        session.add(block)
        await session.commit()
        return block

    @staticmethod
    async def unblock_user(
        session: AsyncSession, user_id: UserIdType, blocked_user_id: UserIdType
    ) -> None:
        """Unblock a user."""
        block = await BlockReportService.get_block(
            session, user_id, blocked_user_id
        )
        if not block:
            raise ValueError("User is not blocked")

        await session.delete(block)
        await session.commit()

    @staticmethod
    async def get_block(
        session: AsyncSession, user_id: UserIdType, blocked_user_id: UserIdType
    ) -> Block | None:
        """Check if a block exists between two users."""
        result = await session.execute(
            select(Block).where(
                and_(
                    Block.user_id == user_id,
                    Block.blocked_user_id == blocked_user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_blocked_users(
        session: AsyncSession, user_id: UserIdType
    ) -> list[Block]:
        """Get all blocked users for a user."""
        result = await session.execute(
            select(Block).where(Block.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_blocked_user_ids(
        session: AsyncSession, user_id: UserIdType
    ) -> list[UserIdType]:
        """Get list of blocked user IDs (both directions)."""
        result = await session.execute(
            select(Block.blocked_user_id).where(Block.user_id == user_id)
        )
        blocked_by_me = list(result.scalars().all())

        result = await session.execute(
            select(Block.user_id).where(Block.blocked_user_id == user_id)
        )
        blocked_me = list(result.scalars().all())

        return list(set(blocked_by_me + blocked_me))

    @staticmethod
    async def report_user(
        session: AsyncSession,
        user_id: UserIdType,
        reported_user_id: UserIdType,
        reason: ReportReasonEnum,
        description: str | None = None,
    ) -> Report:
        """Report a user."""
        if user_id == reported_user_id:
            raise ValueError("Cannot report yourself")

        report = Report(
            user_id=user_id,
            reported_user_id=reported_user_id,
            reason=reason,
            description=description,
        )
        session.add(report)
        await session.commit()
        return report
