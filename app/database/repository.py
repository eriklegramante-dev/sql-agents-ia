from typing import Generic, Optional, TypeVar

import asyncpg
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Generic repository contract backed by an asyncpg pool.

    Defines the CRUD methods expected from concrete repositories that return
    Pydantic model instances.
    """

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        raise NotImplementedError

    async def create(self, entity: T) -> T:
        raise NotImplementedError

    async def update(self, entity: T) -> T:
        raise NotImplementedError

    async def delete(self, entity_id: str) -> bool:
        raise NotImplementedError
