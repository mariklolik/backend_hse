import asyncpg


async def create_user(pool: asyncpg.Pool, name: str, is_verified_seller: bool = False) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO users (name, is_verified_seller) VALUES ($1, $2) RETURNING *",
            name, is_verified_seller,
        )
        return dict(row)


async def get_user(pool: asyncpg.Pool, user_id: int) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(row) if row else None
