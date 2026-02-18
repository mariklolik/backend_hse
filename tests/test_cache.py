import pytest
from unittest.mock import AsyncMock

from cache.predictions import (
    get_cached_prediction,
    set_cached_prediction,
    delete_cached_prediction,
    _cache_key,
    PREDICTION_TTL,
)


@pytest.fixture
def mock_redis():
    return AsyncMock()


def test_cache_key_format():
    assert _cache_key(42) == "prediction:42"


@pytest.mark.asyncio
async def test_get_cached_prediction_hit(mock_redis):
    mock_redis.get.return_value = '{"is_violation": true, "probability": 0.9}'

    result = await get_cached_prediction(mock_redis, 1)

    assert result["is_violation"] is True
    assert result["probability"] == 0.9
    mock_redis.get.assert_called_once_with("prediction:1")


@pytest.mark.asyncio
async def test_get_cached_prediction_miss(mock_redis):
    mock_redis.get.return_value = None

    result = await get_cached_prediction(mock_redis, 1)

    assert result is None


@pytest.mark.asyncio
async def test_set_cached_prediction(mock_redis):
    await set_cached_prediction(mock_redis, 1, True, 0.9)

    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][0] == "prediction:1"
    assert call_args[1]["ex"] == PREDICTION_TTL


@pytest.mark.asyncio
async def test_delete_cached_prediction(mock_redis):
    await delete_cached_prediction(mock_redis, 1)

    mock_redis.delete.assert_called_once_with("prediction:1")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_roundtrip_integration():
    import redis.asyncio as redis

    try:
        client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        await client.ping()
    except Exception:
        pytest.skip("Redis not available")

    try:
        await set_cached_prediction(client, 9999, True, 0.85)
        result = await get_cached_prediction(client, 9999)
        assert result is not None
        assert result["is_violation"] is True
        assert result["probability"] == 0.85

        await delete_cached_prediction(client, 9999)
        result = await get_cached_prediction(client, 9999)
        assert result is None
    finally:
        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_ttl_is_set_integration():
    import redis.asyncio as redis

    try:
        client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        await client.ping()
    except Exception:
        pytest.skip("Redis not available")

    try:
        await set_cached_prediction(client, 9998, False, 0.2)
        ttl = await client.ttl("prediction:9998")
        assert ttl > 0
        assert ttl <= PREDICTION_TTL

        await client.delete("prediction:9998")
    finally:
        await client.close()
