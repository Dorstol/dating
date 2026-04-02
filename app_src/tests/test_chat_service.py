"""Unit tests for ChatService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.models import Match, Message
from crud.services.chat_service import ChatService


class TestValidateMatchParticipant:
    async def test_valid_participant_user_id(self):
        session = AsyncMock()
        match = Match(id=1, user_id=10, matched_user_id=20, is_mutual=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = match
        session.execute.return_value = mock_result

        result = await ChatService.validate_match_participant(session, 1, 10)

        assert result is match

    async def test_valid_participant_matched_user_id(self):
        session = AsyncMock()
        match = Match(id=1, user_id=10, matched_user_id=20, is_mutual=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = match
        session.execute.return_value = mock_result

        result = await ChatService.validate_match_participant(session, 1, 20)

        assert result is match

    async def test_match_not_found_raises(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Match not found"):
            await ChatService.validate_match_participant(session, 999, 10)

    async def test_not_mutual_raises(self):
        session = AsyncMock()
        match = Match(id=1, user_id=10, matched_user_id=20, is_mutual=False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = match
        session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not mutual"):
            await ChatService.validate_match_participant(session, 1, 10)

    async def test_non_participant_raises(self):
        session = AsyncMock()
        match = Match(id=1, user_id=10, matched_user_id=20, is_mutual=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = match
        session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not a participant"):
            await ChatService.validate_match_participant(session, 1, 99)


class TestSaveMessage:
    async def test_saves_and_returns_message(self):
        session = AsyncMock()
        session.add = MagicMock()

        result = await ChatService.save_message(session, 1, 10, "hello")

        assert result.match_id == 1
        assert result.sender_id == 10
        assert result.text == "hello"
        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()


class TestGetHistory:
    async def test_returns_messages_and_total(self):
        session = AsyncMock()

        # Mock total count
        mock_total = MagicMock()
        mock_total.scalar.return_value = 3

        # Mock messages
        msg1 = Message(id=1, match_id=1, sender_id=10, text="hi")
        msg2 = Message(id=2, match_id=1, sender_id=20, text="hello")
        mock_messages = MagicMock()
        mock_messages.scalars.return_value.all.return_value = [msg1, msg2]

        session.execute.side_effect = [mock_total, mock_messages]

        messages, total = await ChatService.get_history(session, 1, limit=50, offset=0)

        assert total == 3
        assert len(messages) == 2
        assert messages[0].text == "hi"

    async def test_empty_history(self):
        session = AsyncMock()

        mock_total = MagicMock()
        mock_total.scalar.return_value = 0

        mock_messages = MagicMock()
        mock_messages.scalars.return_value.all.return_value = []

        session.execute.side_effect = [mock_total, mock_messages]

        messages, total = await ChatService.get_history(session, 1)

        assert total == 0
        assert messages == []


class TestMarkAsRead:
    async def test_marks_unread_messages(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(1,), (2,), (3,)]
        session.execute.return_value = mock_result

        count = await ChatService.mark_as_read(session, 1, 20)

        assert count == 3
        session.commit.assert_awaited_once()

    async def test_no_unread_messages(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute.return_value = mock_result

        count = await ChatService.mark_as_read(session, 1, 20)

        assert count == 0
