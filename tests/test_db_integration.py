import pytest
import asyncpg

from db.repositories.users import create_user, get_user
from db.repositories.advertisements import create_advertisement, get_advertisement, close_advertisement


@pytest.fixture
async def db_pool():
    try:
        pool = await asyncpg.create_pool(
            host="localhost", port=5432,
            user="postgres", password="postgres",
            database="backend",
        )
    except Exception:
        pytest.skip("PostgreSQL not available")
        return

    yield pool
    await pool.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_create_and_get(db_pool):
    user = await create_user(db_pool, "IntegrationTestUser", True)
    assert user["name"] == "IntegrationTestUser"

    fetched = await get_user(db_pool, user["id"])
    assert fetched is not None
    assert fetched["name"] == "IntegrationTestUser"

    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1", user["id"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_advertisement_create_and_close(db_pool):
    user = await create_user(db_pool, "AdTestUser", False)

    ad = await create_advertisement(db_pool, user["id"], "TestAd", "Desc", 1, 2)
    assert ad["name"] == "TestAd"

    fetched = await get_advertisement(db_pool, ad["id"])
    assert fetched is not None

    deleted = await close_advertisement(db_pool, ad["id"])
    assert deleted is True

    fetched_after = await get_advertisement(db_pool, ad["id"])
    assert fetched_after is None

    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1", user["id"])
