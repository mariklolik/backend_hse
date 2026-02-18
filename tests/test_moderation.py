import pytest
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from db.repositories.moderation import (
    create_moderation_task,
    get_moderation_result,
    update_moderation_result,
)


@pytest.fixture
def mock_pool():
    conn = AsyncMock()
    pool = MagicMock()

    @asynccontextmanager
    async def acquire():
        yield conn

    pool.acquire = acquire
    return pool, conn


@pytest.mark.asyncio
async def test_create_moderation_task(mock_pool):
    pool, conn = mock_pool
    conn.fetchrow.return_value = {
        "id": 1, "item_id": 10, "status": "pending",
        "is_violation": None, "probability": None,
        "error_message": None, "created_at": datetime.now(timezone.utc),
        "processed_at": None,
    }

    result = await create_moderation_task(pool, 10)

    assert result["id"] == 1
    assert result["status"] == "pending"
    conn.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_moderation_result(mock_pool):
    pool, conn = mock_pool
    conn.fetchrow.return_value = {
        "id": 1, "item_id": 10, "status": "completed",
        "is_violation": True, "probability": 0.9,
        "error_message": None,
    }

    result = await get_moderation_result(pool, 1)

    assert result["status"] == "completed"
    assert result["is_violation"] is True


@pytest.mark.asyncio
async def test_get_moderation_result_not_found(mock_pool):
    pool, conn = mock_pool
    conn.fetchrow.return_value = None

    result = await get_moderation_result(pool, 999)

    assert result is None


@pytest.mark.asyncio
async def test_update_moderation_result(mock_pool):
    pool, conn = mock_pool

    await update_moderation_result(pool, 1, "completed", is_violation=True, probability=0.9)

    conn.execute.assert_called_once()
    args = conn.execute.call_args[0]
    assert args[1] == "completed"
    assert args[2] is True
    assert args[3] == 0.9
