import os

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def create_redis_client() -> redis.Redis:
    client = redis.from_url(REDIS_URL, decode_responses=True)
    return client
