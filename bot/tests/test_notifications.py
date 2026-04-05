"""Unit tests for bot notification listener."""

from unittest.mock import AsyncMock

import pytest

from bot.notifications import NotificationListener


@pytest.fixture
def listener():
    bot = AsyncMock()
    nl = NotificationListener(bot, "redis://localhost:6379")
    return nl


class TestThrottle:
    def test_first_call_not_throttled(self, listener):
        assert listener._is_throttled(123, "mutual_match") is False

    def test_second_call_throttled(self, listener):
        listener._is_throttled(123, "mutual_match")
        assert listener._is_throttled(123, "mutual_match") is True

    def test_different_types_not_throttled(self, listener):
        listener._is_throttled(123, "mutual_match")
        assert listener._is_throttled(123, "new_message") is False

    def test_different_users_not_throttled(self, listener):
        listener._is_throttled(123, "mutual_match")
        assert listener._is_throttled(456, "mutual_match") is False


class TestHandleEvent:
    async def test_match_notification(self, listener):
        event = {
            "type": "mutual_match",
            "telegram_id": 123,
            "matched_user_name": "Alice",
        }
        await listener._handle_event(event)
        listener.bot.send_message.assert_awaited_once()
        call_kwargs = listener.bot.send_message.call_args.kwargs
        assert "Alice" in call_kwargs["text"]

    async def test_message_notification(self, listener):
        event = {
            "type": "new_message",
            "telegram_id": 456,
            "sender_name": "Bob",
            "text_preview": "Hello!",
            "match_id": 1,
        }
        await listener._handle_event(event)
        listener.bot.send_message.assert_awaited_once()
        call_kwargs = listener.bot.send_message.call_args.kwargs
        assert "Bob" in call_kwargs["text"]
        assert "Hello!" in call_kwargs["text"]

    async def test_skips_no_telegram_id(self, listener):
        event = {"type": "mutual_match", "telegram_id": None}
        await listener._handle_event(event)
        listener.bot.send_message.assert_not_awaited()

    async def test_throttled_event_skipped(self, listener):
        event = {
            "type": "mutual_match",
            "telegram_id": 123,
            "matched_user_name": "Alice",
        }
        await listener._handle_event(event)
        listener.bot.send_message.reset_mock()

        await listener._handle_event(event)
        listener.bot.send_message.assert_not_awaited()

    async def test_send_failure_does_not_raise(self, listener):
        listener.bot.send_message.side_effect = Exception("Telegram error")
        event = {
            "type": "mutual_match",
            "telegram_id": 123,
            "matched_user_name": "Alice",
        }
        # Should not raise
        await listener._handle_event(event)
