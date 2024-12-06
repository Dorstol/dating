from redis.asyncio import Redis

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
TOKEN_PREFIX = "token:"

redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    encoding="utf-8",
    decode_responses=True
)


async def store_token_in_redis(token: str, ttl_seconds: int):
    await redis_client.setex(f"{TOKEN_PREFIX}{token}", ttl_seconds, "true")


async def is_token_valid(token: str) -> bool:
    exists = await redis_client.exists(f"{TOKEN_PREFIX}{token}")
    return exists == 1


async def revoke_token(token: str):
    await redis_client.delete(f"{TOKEN_PREFIX}{token}")
