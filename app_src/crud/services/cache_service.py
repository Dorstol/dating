import json
import logging

import redis.asyncio as redis

from core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching data in Redis."""

    _redis: redis.Redis | None = None

    @classmethod
    async def get_redis(cls) -> redis.Redis:
        if cls._redis is None:
            cls._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return cls._redis

    @classmethod
    async def close(cls) -> None:
        if cls._redis is not None:
            await cls._redis.close()
            cls._redis = None

    @classmethod
    def _make_key(cls, *parts: str | int) -> str:
        return f"{settings.cache.prefix}:" + ":".join(str(p) for p in parts)

    @classmethod
    async def get_json(cls, *key_parts: str | int) -> dict | list | None:
        try:
            r = await cls.get_redis()
            data = await r.get(cls._make_key(*key_parts))
            if data is not None:
                return json.loads(data)
        except redis.RedisError:
            logger.warning("Redis read error", exc_info=True)
        return None

    @classmethod
    async def set_json(
        cls, value: dict | list, *key_parts: str | int, ttl: int | None = None
    ) -> None:
        try:
            r = await cls.get_redis()
            key = cls._make_key(*key_parts)
            await r.set(key, json.dumps(value, default=str), ex=ttl)
        except redis.RedisError:
            logger.warning("Redis write error", exc_info=True)

    @classmethod
    async def delete_pattern(cls, *key_parts: str | int) -> None:
        try:
            r = await cls.get_redis()
            pattern = cls._make_key(*key_parts) + "*"
            cursor = 0
            while True:
                cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    await r.delete(*keys)
                if cursor == 0:
                    break
        except redis.RedisError:
            logger.warning("Redis delete error", exc_info=True)

    @classmethod
    async def invalidate_suggestions(cls, user_id: int) -> None:
        await cls.delete_pattern("suggestions", user_id, "")
