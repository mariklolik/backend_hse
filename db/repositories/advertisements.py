import asyncpg


async def create_advertisement(
    pool: asyncpg.Pool,
    seller_id: int,
    name: str,
    description: str,
    category: int,
    images_qty: int = 0,
) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO advertisements (seller_id, name, description, category, images_qty) "
            "VALUES ($1, $2, $3, $4, $5) RETURNING *",
            seller_id, name, description, category, images_qty,
        )
        return dict(row)


async def get_advertisement(pool: asyncpg.Pool, item_id: int) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT a.*, u.is_verified_seller "
            "FROM advertisements a "
            "JOIN users u ON a.seller_id = u.id "
            "WHERE a.id = $1",
            item_id,
        )
        return dict(row) if row else None


async def close_advertisement(pool: asyncpg.Pool, item_id: int) -> bool:
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM advertisements WHERE id = $1",
            item_id,
        )
        return result == "DELETE 1"


async def delete_moderation_results_for_item(pool: asyncpg.Pool, item_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM moderation_results WHERE item_id = $1",
            item_id,
        )
