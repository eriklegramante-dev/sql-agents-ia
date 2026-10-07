from datetime import UTC, datetime
from uuid import UUID

import asyncpg
import pytest

from app.core.datasets.exceptions import (
    DatasetRelatedRecordsDeletionException,
)
from app.database.dataset_repository import DatasetRepository
from app.enums.dataset_status import DatasetStatus


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
    """Fake database connection used to record repository operations."""

    def __init__(
        self,
        fail: bool = False,
        fetchrow_result=None,
        fetch_result=None,
    ) -> None:
        self.executions: list[tuple[str, UUID]] = []
        self.fail = fail
        self.fetchrow_result = fetchrow_result
        self.fetch_result = fetch_result or []
        self.fetchrow_query: str | None = None
        self.fetchrow_dataset_id: UUID | None = None
        self.fetch_query: str | None = None
        self.fetch_args: tuple = ()

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

    async def fetchrow(
        self,
        query: str,
        dataset_id: UUID,
    ):
        """Return the configured database row for retrieval tests."""
        self.fetchrow_query = query
        self.fetchrow_dataset_id = dataset_id

        return self.fetchrow_result

    async def fetch(
        self,
        query: str,
        *args,
    ):
        """Return configured database rows for listing tests."""
        self.fetch_query = query
        self.fetch_args = args

        return self.fetch_result


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
        fetchrow_result=None,
        fetch_result=None,
    ) -> None:
        self.connection = FakeConnection(
            fail=fail,
            fetchrow_result=fetchrow_result,
            fetch_result=fetch_result,
        )

    def acquire(self) -> FakeAcquireContext:
        return FakeAcquireContext(
            connection=self.connection,
        )


def make_dataset_row(
    profile=None,
) -> dict:
    """Create a database row used by dataset metadata retrieval tests."""
    now = datetime.now(UTC)

    return {
        "id": UUID("44444444-4444-4444-4444-444444444444"),
        "name": "Customers",
        "filename": "customers.csv",
        "status": DatasetStatus.PROFILED.value,
        "raw_object_key": "raw/customers.csv",
        "description": "Dataset used in repository tests",
        "content_type": "text/csv",
        "file_size_bytes": 1024,
        "rows_count": 100,
        "columns_count": 5,
        "created_at": now,
        "updated_at": now,
        "profile": profile,
    }


@pytest.mark.asyncio
async def test_get_metadata_by_id_returns_profile_summary():
    """Build the domain profile summary from persisted profiling data."""
    profile = {
        "rows_count": 100,
        "columns_count": 5,
        "columns": [
            {
                "name": "id",
                "type": "numeric",
            },
            {
                "name": "amount",
                "type": "numeric",
            },
            {
                "name": "created_at",
                "type": "datetime",
            },
            {
                "name": "name",
                "type": "text",
            },
            {
                "name": "region",
                "type": "text",
            },
        ],
        "nulls_summary": {
            "total_nulls": 7,
            "columns_with_nulls": 2,
        },
        "quality_warnings": [
            "Column 'region' contains only one distinct value.",
        ],
    }

    row = make_dataset_row(
        profile=profile,
    )

    pool = FakePool(
        fetchrow_result=row,
    )

    repository = DatasetRepository(
        pool=pool,
    )

    dataset_id = row["id"]

    result = await repository.get_metadata_by_id(
        dataset_id=dataset_id,
    )

    assert result is not None
    assert result.dataset_id == dataset_id
    assert result.rows_count == 100
    assert result.columns_count == 5

    assert result.profile is not None
    assert result.profile.total_nulls == 7
    assert result.profile.columns_with_nulls == 2
    assert result.profile.numeric_columns == 2
    assert result.profile.datetime_columns == 1
    assert result.profile.text_columns == 2
    assert result.profile.quality_warnings == (
        "Column 'region' contains only one distinct value.",
    )

    assert pool.connection.fetchrow_dataset_id == dataset_id
    assert "LEFT JOIN dataset_profiles" in pool.connection.fetchrow_query


@pytest.mark.asyncio
async def test_get_metadata_by_id_returns_none_profile_when_unavailable():
    """Keep profile unavailable when no profiling record exists."""
    row = make_dataset_row(
        profile=None,
    )

    pool = FakePool(
        fetchrow_result=row,
    )

    repository = DatasetRepository(
        pool=pool,
    )

    result = await repository.get_metadata_by_id(
        dataset_id=row["id"],
    )

    assert result is not None
    assert result.profile is None


@pytest.mark.asyncio
async def test_get_metadata_by_id_preserves_zero_profile_values():
    """Preserve known zero profiling values instead of treating them as absent."""
    profile = {
        "rows_count": 100,
        "columns_count": 0,
        "columns": [],
        "nulls_summary": {
            "total_nulls": 0,
            "columns_with_nulls": 0,
        },
        "quality_warnings": [],
    }

    row = make_dataset_row(
        profile=profile,
    )

    pool = FakePool(
        fetchrow_result=row,
    )

    repository = DatasetRepository(
        pool=pool,
    )

    result = await repository.get_metadata_by_id(
        dataset_id=row["id"],
    )

    assert result is not None
    assert result.profile is not None

    assert result.profile.total_nulls == 0
    assert result.profile.columns_with_nulls == 0
    assert result.profile.numeric_columns == 0
    assert result.profile.datetime_columns == 0
    assert result.profile.text_columns == 0
    assert result.profile.quality_warnings == ()


@pytest.mark.asyncio
async def test_get_metadata_by_id_returns_none_when_dataset_does_not_exist():
    """Return None when the requested dataset does not exist."""
    pool = FakePool(
        fetchrow_result=None,
    )

    repository = DatasetRepository(
        pool=pool,
    )

    dataset_id = UUID("55555555-5555-5555-5555-555555555555")

    result = await repository.get_metadata_by_id(
        dataset_id=dataset_id,
    )

    assert result is None


@pytest.mark.asyncio
async def test_list_metadata_returns_active_dataset_metadata():
    """Return and map all active dataset metadata."""
    first_row = make_dataset_row(
        profile={
            "columns": [
                {
                    "name": "id",
                    "type": "numeric",
                },
                {
                    "name": "created_at",
                    "type": "datetime",
                },
                {
                    "name": "name",
                    "type": "text",
                },
            ],
            "nulls_summary": {
                "total_nulls": 0,
                "columns_with_nulls": 0,
            },
            "quality_warnings": [
                "Dataset warning.",
            ],
        },
    )

    second_row = make_dataset_row(
        profile=None,
    )
    second_row["id"] = UUID(
        "66666666-6666-6666-6666-666666666666"
    )
    second_row["name"] = "Orders"
    second_row["filename"] = "orders.csv"

    pool = FakePool(
        fetch_result=[
            first_row,
            second_row,
        ],
    )

    repository = DatasetRepository(
        pool=pool,
    )

    result = await repository.list_metadata()

    assert len(result) == 2

    assert result[0].dataset_id == first_row["id"]
    assert result[0].name == "Customers"
    assert result[0].profile is not None
    assert result[0].profile.total_nulls == 0
    assert result[0].profile.columns_with_nulls == 0
    assert result[0].profile.numeric_columns == 1
    assert result[0].profile.datetime_columns == 1
    assert result[0].profile.text_columns == 1
    assert result[0].profile.quality_warnings == (
        "Dataset warning.",
    )

    assert result[1].dataset_id == second_row["id"]
    assert result[1].name == "Orders"
    assert result[1].profile is None


@pytest.mark.asyncio
async def test_list_metadata_filters_deleted_and_orders_newest_first():
    """Query active datasets ordered from newest to oldest."""
    pool = FakePool(
        fetch_result=[],
    )

    repository = DatasetRepository(
        pool=pool,
    )

    result = await repository.list_metadata()

    assert result == []
    assert pool.connection.fetch_query is not None
    assert "LEFT JOIN dataset_profiles" in pool.connection.fetch_query
    assert "WHERE d.status <> $1" in pool.connection.fetch_query
    assert "ORDER BY d.created_at DESC" in pool.connection.fetch_query
    assert pool.connection.fetch_args == (
        DatasetStatus.DELETED.value,
    )


@pytest.mark.asyncio
async def test_list_metadata_returns_empty_list_when_no_datasets_exist():
    """Return an empty collection when no active datasets exist."""
    pool = FakePool(
        fetch_result=[],
    )

    repository = DatasetRepository(
        pool=pool,
    )

    result = await repository.list_metadata()

    assert result == []


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
        execution_dataset_id
        for _, execution_dataset_id in pool.connection.executions
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
