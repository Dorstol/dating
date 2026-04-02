import asyncio
import json
import logging

import redis.asyncio as redis
from fastapi import WebSocket

from core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with Redis Pub/Sub for multi-worker support."""

    def __init__(self):
        self._connections: dict[int, dict[int, WebSocket]] = {}
        # match_id -> {user_id -> websocket}
        self._redis: redis.Redis | None = None
        self._pubsub: redis.client.PubSub | None = None
        self._listener_task: asyncio.Task | None = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
        return self._redis

    def _channel(self, match_id: int) -> str:
        return f"chat:{match_id}"

    async def connect(
        self, websocket: WebSocket, match_id: int, user_id: int
    ) -> None:
        """Register a WebSocket connection and subscribe to Redis channel."""
        await websocket.accept()

        if match_id not in self._connections:
            self._connections[match_id] = {}
        self._connections[match_id][user_id] = websocket

        try:
            r = await self._get_redis()
            if self._pubsub is None:
                self._pubsub = r.pubsub()
            await self._pubsub.subscribe(self._channel(match_id))

            if self._listener_task is None or self._listener_task.done():
                self._listener_task = asyncio.create_task(self._listen())
        except redis.RedisError:
            logger.warning("Redis unavailable, falling back to local-only mode")

    async def disconnect(self, match_id: int, user_id: int) -> None:
        """Remove a WebSocket connection."""
        if match_id in self._connections:
            self._connections[match_id].pop(user_id, None)
            if not self._connections[match_id]:
                del self._connections[match_id]
                try:
                    if self._pubsub:
                        await self._pubsub.unsubscribe(self._channel(match_id))
                except redis.RedisError:
                    pass

    async def broadcast(
        self, match_id: int, message: dict, exclude_user_id: int | None = None
    ) -> None:
        """
        Publish message to Redis channel.

        Falls back to local delivery if Redis is unavailable.
        """
        payload = json.dumps(message)
        try:
            r = await self._get_redis()
            await r.publish(self._channel(match_id), payload)
        except redis.RedisError:
            logger.warning("Redis publish failed, delivering locally")
            await self._deliver_local(match_id, message, exclude_user_id)

    async def _deliver_local(
        self, match_id: int, message: dict, exclude_user_id: int | None = None
    ) -> None:
        """Deliver message to locally connected WebSockets."""
        connections = self._connections.get(match_id, {})
        for uid, ws in list(connections.items()):
            if exclude_user_id and uid == exclude_user_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect(match_id, uid)

    async def _listen(self) -> None:
        """Listen for messages from Redis Pub/Sub and deliver to local WebSockets."""
        try:
            while self._pubsub:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    channel = message["channel"]
                    # channel format: "chat:{match_id}"
                    match_id = int(channel.split(":")[1])
                    data = json.loads(message["data"])
                    await self._deliver_local(match_id, data)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Redis listener error")

    async def close(self) -> None:
        """Cleanup all connections and Redis resources."""
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None
        if self._redis:
            await self._redis.close()
            self._redis = None


manager = ConnectionManager()
