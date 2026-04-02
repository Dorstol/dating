"""Publishes notification events to Redis for the bot to consume."""

import json
import logging

import redis.asyncio as redis

from core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Publishes notification events to Redis Pub/Sub."""

    CHANNEL = "bot:notifications"

    @staticmethod
    async def _publish(event: dict) -> None:
        try:
            r = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.publish(NotificationService.CHANNEL, json.dumps(event))
            await r.close()
        except redis.RedisError:
            logger.warning("Failed to publish notification: %s", event)

    @staticmethod
    async def notify_mutual_match(
        user_telegram_id: int | None,
        matched_user_name: str,
    ) -> None:
        """Notify user about a new mutual match."""
        if not user_telegram_id:
            return
        await NotificationService._publish(
            {
                "type": "mutual_match",
                "telegram_id": user_telegram_id,
                "matched_user_name": matched_user_name,
            }
        )

    @staticmethod
    async def notify_new_message(
        recipient_telegram_id: int | None,
        sender_name: str,
        text_preview: str,
        match_id: int,
    ) -> None:
        """Notify user about a new message (if they're not online in WebApp)."""
        if not recipient_telegram_id:
            return
        await NotificationService._publish(
            {
                "type": "new_message",
                "telegram_id": recipient_telegram_id,
                "sender_name": sender_name,
                "text_preview": text_preview[:100],
                "match_id": match_id,
            }
        )
