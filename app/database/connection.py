import asyncpg

from app.settings.setting import get_settings


_db_pool: asyncpg.Pool | None = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Return a shared PostgreSQL connection pool.

    The pool is created lazily on the first request and reused by all
    repositories that require database access.
    """
    global _db_pool

    if _db_pool is None:
        settings = get_settings()

        _db_pool = await asyncpg.create_pool(
            host=settings.database.host,
            port=settings.database.port,
            database=settings.database.name,
            user=settings.database.user,
            password=settings.database.password,
            min_size=settings.database.min_pool_size,
            max_size=settings.database.max_pool_size,
        )

    return _db_pool