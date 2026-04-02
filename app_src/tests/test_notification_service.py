"""Unit tests for NotificationService."""

from unittest.mock import AsyncMock, patch


from crud.services.notification_service import NotificationService


class TestNotifyMutualMatch:
    async def test_publishes_event(self):
        with patch.object(
            NotificationService, "_publish", new_callable=AsyncMock
        ) as mock_pub:
            await NotificationService.notify_mutual_match(123456, "Alice")
            mock_pub.assert_awaited_once_with(
                {
                    "type": "mutual_match",
                    "telegram_id": 123456,
                    "matched_user_name": "Alice",
                }
            )

    async def test_skips_if_no_telegram_id(self):
        with patch.object(
            NotificationService, "_publish", new_callable=AsyncMock
        ) as mock_pub:
            await NotificationService.notify_mutual_match(None, "Alice")
            mock_pub.assert_not_awaited()


class TestNotifyNewMessage:
    async def test_publishes_event(self):
        with patch.object(
            NotificationService, "_publish", new_callable=AsyncMock
        ) as mock_pub:
            await NotificationService.notify_new_message(
                123456, "Bob", "Hey there!", 42
            )
            mock_pub.assert_awaited_once_with(
                {
                    "type": "new_message",
                    "telegram_id": 123456,
                    "sender_name": "Bob",
                    "text_preview": "Hey there!",
                    "match_id": 42,
                }
            )

    async def test_skips_if_no_telegram_id(self):
        with patch.object(
            NotificationService, "_publish", new_callable=AsyncMock
        ) as mock_pub:
            await NotificationService.notify_new_message(None, "Bob", "Hey", 42)
            mock_pub.assert_not_awaited()

    async def test_truncates_long_text(self):
        with patch.object(
            NotificationService, "_publish", new_callable=AsyncMock
        ) as mock_pub:
            long_text = "x" * 200
            await NotificationService.notify_new_message(123, "Bob", long_text, 1)
            event = mock_pub.call_args[0][0]
            assert len(event["text_preview"]) == 100
