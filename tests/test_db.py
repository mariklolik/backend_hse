import pytest
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager

from db.repositories.users import create_user, get_user
from db.repositories.advertisements import create_advertisement, get_advertisement


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
async def test_create_user(mock_pool):
    pool, conn = mock_pool
    conn.fetchrow.return_value = {
        "id": 1,
        "name": "Test User",
        "is_verified_seller": False,
        "created_at": "2026-01-01T00:00:00",
    }

    result = await create_user(pool, "Test User")

    assert result["id"] == 1
    assert result["name"] == "Test User"
    assert result["is_verified_seller"] is False
    conn.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_user(mock_pool):
    pool, conn = mock_pool
    conn.fetchrow.return_value = {
        "id": 1,
        "name": "Test User",
        "is_verified_seller": True,
        "created_at": "2026-01-01T00:00:00",
    }

    result = await get_user(pool, 1)

    assert result["id"] == 1
    assert result["is_verified_seller"] is True
    conn.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_not_found(mock_pool):
    pool, conn = mock_pool
    conn.fetchrow.return_value = None

    result = await get_user(pool, 999)

    assert result is None


@pytest.mark.asyncio
async def test_create_advertisement(mock_pool):
    pool, conn = mock_pool
    conn.fetchrow.return_value = {
        "id": 1,
        "seller_id": 1,
        "name": "Test Ad",
        "description": "Test Description",
        "category": 5,
        "images_qty": 3,
        "created_at": "2026-01-01T00:00:00",
    }

    result = await create_advertisement(pool, 1, "Test Ad", "Test Description", 5, 3)

    assert result["id"] == 1
    assert result["seller_id"] == 1
    assert result["name"] == "Test Ad"
    conn.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_advertisement(mock_pool):
    pool, conn = mock_pool
    conn.fetchrow.return_value = {
        "id": 1,
        "seller_id": 1,
        "name": "Test Ad",
        "description": "Test Description",
        "category": 5,
        "images_qty": 3,
        "is_verified_seller": False,
        "created_at": "2026-01-01T00:00:00",
    }

    result = await get_advertisement(pool, 1)

    assert result["id"] == 1
    assert result["is_verified_seller"] is False
    conn.fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_advertisement_not_found(mock_pool):
    pool, conn = mock_pool
    conn.fetchrow.return_value = None

    result = await get_advertisement(pool, 999)

    assert result is None
