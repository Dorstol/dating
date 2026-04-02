"""Redis Pub/Sub listener that sends Telegram notifications."""

import asyncio
import json
import logging
import time

import redis.asyncio as redis
from aiogram import Bot


logger = logging.getLogger(__name__)

CHANNEL = "bot:notifications"
# Throttle: max 1 notification per type per user per 60 seconds
THROTTLE_TTL = 60


class NotificationListener:
    """Listens to Redis Pub/Sub and sends Telegram messages."""

    def __init__(self, bot: Bot, redis_url: str):
        self.bot = bot
        self.redis_url = redis_url
        self._redis: redis.Redis | None = None
        self._task: asyncio.Task | None = None
        # In-memory throttle: {(telegram_id, type): last_sent_ts}
        self._throttle: dict[tuple[int, str], float] = {}

    async def start(self) -> None:
        self._redis = redis.from_url(self.redis_url, decode_responses=True)
        self._task = asyncio.create_task(self._listen())
        logger.info("Notification listener started")

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._redis:
            await self._redis.close()

    def _is_throttled(self, telegram_id: int, event_type: str) -> bool:
        key = (telegram_id, event_type)
        now = time.monotonic()
        last = self._throttle.get(key)
        if last is not None and now - last < THROTTLE_TTL:
            return True
        self._throttle[key] = now
        return False

    async def _listen(self) -> None:
        try:
            pubsub = self._redis.pubsub()
            await pubsub.subscribe(CHANNEL)
            logger.info("Subscribed to %s", CHANNEL)

            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        await self._handle_event(event)
                    except Exception:
                        logger.exception("Error handling notification event")
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Notification listener error")

    async def _handle_event(self, event: dict) -> None:
        event_type = event.get("type")
        telegram_id = event.get("telegram_id")

        if not telegram_id:
            return

        if self._is_throttled(telegram_id, event_type):
            logger.debug("Throttled %s for %s", event_type, telegram_id)
            return

        if event_type == "mutual_match":
            await self._send_match_notification(telegram_id, event)
        elif event_type == "new_message":
            await self._send_message_notification(telegram_id, event)

    async def _send_match_notification(self, telegram_id: int, event: dict) -> None:
        name = event.get("matched_user_name", "Someone")
        text = f"You have a new match with {name}!\n\nOpen the app to start chatting."
        await self._send(telegram_id, text)

    async def _send_message_notification(self, telegram_id: int, event: dict) -> None:
        sender = event.get("sender_name", "Someone")
        preview = event.get("text_preview", "")
        text = f'New message from {sender}:\n"{preview}"'
        await self._send(telegram_id, text)

    async def _send(self, telegram_id: int, text: str) -> None:
        try:
            await self.bot.send_message(chat_id=telegram_id, text=text)
        except Exception:
            logger.warning("Failed to send notification to %s", telegram_id)
