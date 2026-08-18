from uuid import UUID

import pytest

from app.database.dataset_repository import DatasetRepository


class FakeTransaction:
    """Fake async transaction used by dataset repository tests."""

    async def __aenter__(self):
        """Enter the fake transaction context."""
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        """Exit the fake transaction context."""


class FakeConnection:
    """Fake database connection used to record executed SQL statements."""

    def __init__(self) -> None:
        self.executions: list[tuple[str, UUID]] = []

    def transaction(self) -> FakeTransaction:
        """Return a fake transaction context manager."""
        return FakeTransaction()

    async def execute(
        self,
        query: str,
        dataset_id: UUID,
    ) -> str:
        """Record the SQL statement and dataset identifier."""
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
        """Return the configured fake connection."""
        return self.connection

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        """Exit the fake connection context."""


class FakePool:
    """Fake asyncpg pool used by dataset repository tests."""

    def __init__(self) -> None:
        self.connection = FakeConnection()

    def acquire(self) -> FakeAcquireContext:
        """Return a fake connection acquisition context."""
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

    assert result is True
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
