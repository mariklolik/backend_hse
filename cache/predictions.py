import json

import redis.asyncio as redis

PREDICTION_TTL = 3600


def _cache_key(item_id: int) -> str:
    return f"prediction:{item_id}"


async def get_cached_prediction(client: redis.Redis, item_id: int) -> dict | None:
    data = await client.get(_cache_key(item_id))
    if data is None:
        return None
    return json.loads(data)


async def set_cached_prediction(
    client: redis.Redis,
    item_id: int,
    is_violation: bool,
    probability: float,
) -> None:
    data = json.dumps({"is_violation": is_violation, "probability": probability})
    await client.set(_cache_key(item_id), data, ex=PREDICTION_TTL)


async def delete_cached_prediction(client: redis.Redis, item_id: int) -> None:
    await client.delete(_cache_key(item_id))
