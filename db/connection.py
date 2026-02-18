import os

import asyncpg


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "postgres"),
        database=os.getenv("PG_DATABASE", "backend"),
    )


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()
