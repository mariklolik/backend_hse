import asyncpg
from datetime import datetime, timezone


async def create_moderation_task(pool: asyncpg.Pool, item_id: int) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO moderation_results (item_id, status) "
            "VALUES ($1, 'pending') RETURNING *",
            item_id,
        )
        return dict(row)


async def get_moderation_result(pool: asyncpg.Pool, task_id: int) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM moderation_results WHERE id = $1",
            task_id,
        )
        return dict(row) if row else None


async def update_moderation_result(
    pool: asyncpg.Pool,
    task_id: int,
    status: str,
    is_violation: bool | None = None,
    probability: float | None = None,
    error_message: str | None = None,
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE moderation_results "
            "SET status = $1, is_violation = $2, probability = $3, "
            "error_message = $4, processed_at = $5 "
            "WHERE id = $6",
            status, is_violation, probability,
            error_message, datetime.now(timezone.utc), task_id,
        )
