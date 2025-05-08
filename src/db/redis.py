import redis.asyncio as redis
from src.core.settings import settings

redis_pool: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_pool
