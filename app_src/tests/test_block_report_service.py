"""Unit tests for BlockReportService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.models import Block, Report
from core.models.enums import ReportReasonEnum
from crud.services.block_report_service import BlockReportService


class TestBlockUser:
    @pytest.fixture
    def session(self):
        s = AsyncMock()
        s.add = MagicMock()
        return s

    async def test_cannot_block_yourself(self, session):
        with pytest.raises(ValueError, match="Cannot block yourself"):
            await BlockReportService.block_user(session, 1, 1)

    async def test_cannot_block_already_blocked(self, session):
        existing = Block(user_id=1, blocked_user_id=2)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="already blocked"):
            await BlockReportService.block_user(session, 1, 2)

    async def test_block_creates_record(self, session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        result = await BlockReportService.block_user(session, 1, 2)

        assert result.user_id == 1
        assert result.blocked_user_id == 2
        session.add.assert_called_once()
        session.commit.assert_awaited_once()


class TestUnblockUser:
    @pytest.fixture
    def session(self):
        return AsyncMock()

    async def test_unblock_nonexistent_raises(self, session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not blocked"):
            await BlockReportService.unblock_user(session, 1, 2)

    async def test_unblock_deletes_record(self, session):
        existing = Block(user_id=1, blocked_user_id=2)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        session.execute.return_value = mock_result

        await BlockReportService.unblock_user(session, 1, 2)

        session.delete.assert_awaited_once_with(existing)
        session.commit.assert_awaited_once()


class TestGetBlockedUserIds:
    async def test_returns_ids_from_both_directions(self):
        session = AsyncMock()

        # Первый вызов — заблокированные мной
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = [2, 3]
        # Второй вызов — заблокировавшие меня
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = [4]

        session.execute.side_effect = [mock_result1, mock_result2]

        result = await BlockReportService.get_blocked_user_ids(session, 1)

        assert set(result) == {2, 3, 4}

    async def test_returns_empty_when_no_blocks(self):
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        session.execute.side_effect = [mock_result, mock_result]

        result = await BlockReportService.get_blocked_user_ids(session, 1)

        assert result == []

    async def test_deduplicates_ids(self):
        session = AsyncMock()

        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = [2]
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = [2]

        session.execute.side_effect = [mock_result1, mock_result2]

        result = await BlockReportService.get_blocked_user_ids(session, 1)

        assert result == [2]


class TestReportUser:
    @pytest.fixture
    def session(self):
        s = AsyncMock()
        s.add = MagicMock()
        return s

    async def test_cannot_report_yourself(self, session):
        with pytest.raises(ValueError, match="Cannot report yourself"):
            await BlockReportService.report_user(
                session, 1, 1, ReportReasonEnum.SPAM
            )

    async def test_report_creates_record(self, session):
        result = await BlockReportService.report_user(
            session, 1, 2, ReportReasonEnum.FAKE, "Фейковый профиль"
        )

        assert result.user_id == 1
        assert result.reported_user_id == 2
        assert result.reason == ReportReasonEnum.FAKE
        assert result.description == "Фейковый профиль"
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    async def test_report_without_description(self, session):
        result = await BlockReportService.report_user(
            session, 1, 2, ReportReasonEnum.HARASSMENT
        )

        assert result.description is None
        session.add.assert_called_once()
