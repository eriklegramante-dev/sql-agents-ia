from uuid import UUID

import asyncpg
import pytest

from app.core.datasets.exceptions import (
    DatasetRelatedRecordsDeletionException,
)
from app.database.dataset_repository import DatasetRepository


class FakeTransaction:
    """Fake async transaction used by dataset repository tests."""

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        return None


class FakeConnection:
    """Fake database connection used to record executed SQL statements."""

    def __init__(
        self,
        fail: bool = False,
    ) -> None:
        self.executions: list[tuple[str, UUID]] = []
        self.fail = fail

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()

    async def execute(
        self,
        query: str,
        dataset_id: UUID,
    ) -> str:
        if self.fail:
            raise asyncpg.PostgresError("Database cleanup failed.")

        self.executions.append(
            (
                query,
                dataset_id,
            )
        )

        return "DELETE 1"


class FakeAcquireContext:
    """Fake pool acquire context used to expose a test connection."""

    def __init__(
        self,
        connection: FakeConnection,
    ) -> None:
        self.connection = connection

    async def __aenter__(self) -> FakeConnection:
        return self.connection

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        return None


class FakePool:
    """Fake asyncpg pool used by dataset repository tests."""

    def __init__(
        self,
        fail: bool = False,
    ) -> None:
        self.connection = FakeConnection(
            fail=fail,
        )

    def acquire(self) -> FakeAcquireContext:
        return FakeAcquireContext(
            connection=self.connection,
        )


@pytest.mark.asyncio
async def test_delete_related_records_removes_schema_and_profile():
    """Delete schema and profile records belonging to the dataset."""
    pool = FakePool()

    repository = DatasetRepository(
        pool=pool,
    )

    dataset_id = UUID("11111111-1111-1111-1111-111111111111")

    result = await repository.delete_related_records(
        dataset_id=dataset_id,
    )

    assert result is None
    assert len(pool.connection.executions) == 2

    schema_query, schema_dataset_id = pool.connection.executions[0]

    profile_query, profile_dataset_id = pool.connection.executions[1]

    assert "DELETE FROM dataset_schemas" in schema_query
    assert schema_dataset_id == dataset_id

    assert "DELETE FROM dataset_profiles" in profile_query
    assert profile_dataset_id == dataset_id


@pytest.mark.asyncio
async def test_delete_related_records_uses_same_dataset_id_for_both_deletes():
    """Use the requested dataset identifier for every related-record delete."""
    pool = FakePool()

    repository = DatasetRepository(
        pool=pool,
    )

    dataset_id = UUID("22222222-2222-2222-2222-222222222222")

    await repository.delete_related_records(
        dataset_id=dataset_id,
    )

    executed_dataset_ids = [
        execution_dataset_id for _, execution_dataset_id in pool.connection.executions
    ]

    assert executed_dataset_ids == [
        dataset_id,
        dataset_id,
    ]


@pytest.mark.asyncio
async def test_delete_related_records_wraps_database_failure():
    """Raise a domain exception when PostgreSQL cleanup fails."""
    pool = FakePool(
        fail=True,
    )

    repository = DatasetRepository(
        pool=pool,
    )

    dataset_id = UUID("33333333-3333-3333-3333-333333333333")

    with pytest.raises(DatasetRelatedRecordsDeletionException) as exc:
        await repository.delete_related_records(
            dataset_id=dataset_id,
        )

    assert str(exc.value) == (
        f"Failed to delete related records for dataset {dataset_id}."
    )
