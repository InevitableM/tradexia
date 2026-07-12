"""Async Postgres connection pool, shared across the service.

Connected once at app startup (server.py's lifespan) and closed on shutdown.
Only fetch()/execute() are exposed — callers never touch the pool directly.
"""
import asyncpg
from loguru import logger
from config import get_settings


class Database:
    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        settings = get_settings()
        self._pool = await asyncpg.create_pool(settings.database_url)
        logger.info("[db] connected")

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            logger.info("[db] disconnected")

    @property
    def pool(self) -> asyncpg.Pool:
        if not self._pool:
            raise RuntimeError("Database not connected — call db.connect() first")
        return self._pool

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        return await self.pool.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> asyncpg.Record | None:
        return await self.pool.fetchrow(query, *args)

    async def execute(self, query: str, *args) -> str:
        return await self.pool.execute(query, *args)

    async def executemany(self, query: str, args_list: list[tuple]) -> None:
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args_list)


# Instantiated once here; every importer shares the same pool.
db = Database()
