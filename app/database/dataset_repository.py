import json
from typing import Optional
from uuid import UUID

from app.database.repository import BaseRepository
from app.enums.dataset_status import DatasetStatus
from app.models.dataset_schema_table import ColumnSchema
from app.models.dataset_table import DatasetTable


class DatasetRepository(BaseRepository[DatasetTable]):
    """
    Repository responsible for persisting and retrieving dataset metadata.

    This class belongs to the persistence layer and centralizes all database
    operations related to datasets used by the preparation workflow. It reads
    dataset metadata, updates processing status and prepared file information,
    and persists the inferred schema generated during dataset preparation.

    The repository keeps SQL details isolated from routes, controllers,
    services, and workflows, allowing the business flow to depend on clear
    persistence operations instead of raw database queries.

    Attributes:
        pool (asyncpg.Pool):
            Asynchronous PostgreSQL connection pool used to execute dataset
            and schema persistence operations.
    """

    async def get_by_id(self, dataset_id: UUID) -> Optional[DatasetTable]:
        """
        Retrieves dataset metadata by its unique identifier.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset.

        Returns:
            Optional[DatasetTable]:
                Dataset metadata when found, otherwise None.
        """
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT
                    id,
                    name,
                    status,
                    raw_object_key,
                    prepared_object_key,
                    rows_count,
                    columns_count,
                    error_message,
                    created_at,
                    updated_at
                FROM datasets
                WHERE id = $1
                """,
                dataset_id,
            )

        if row is None:
            return None

        return DatasetTable(
            id=row["id"],
            name=row["name"],
            status=DatasetStatus(row["status"]),
            raw_object_key=row["raw_object_key"],
            prepared_object_key=row["prepared_object_key"],
            rows_count=row["rows_count"],
            columns_count=row["columns_count"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def update_status(
        self,
        dataset_id: UUID,
        status: DatasetStatus,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Updates the processing status of a dataset.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset.
            status (DatasetStatus):
                New dataset processing status.
            error_message (Optional[str]):
                Optional error message to persist when processing fails.

        Returns:
            bool:
                True when exactly one dataset row is updated, otherwise False.
        """
        async with self.pool.acquire() as connection:
            result = await connection.execute(
                """
                UPDATE datasets
                SET
                    status = $2,
                    error_message = $3,
                    updated_at = NOW()
                WHERE id = $1
                """,
                dataset_id,
                status.value,
                error_message,
            )

        return result == "UPDATE 1"

    async def update_prepared_info(
        self,
        dataset_id: UUID,
        prepared_object_key: str,
        rows_count: int,
        columns_count: int,
    ) -> Optional[DatasetTable]:
        """
        Persists metadata generated after successful dataset preparation.

        Updates the prepared object key, row count, column count, status,
        error message, and update timestamp. The updated row is returned so the
        workflow can build its response from persisted metadata.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset.
            prepared_object_key (str):
                Object key of the generated prepared Parquet file.
            rows_count (int):
                Number of rows in the prepared dataset.
            columns_count (int):
                Number of columns in the prepared dataset.

        Returns:
            Optional[DatasetTable]:
                Updated dataset metadata when the row exists, otherwise None.
        """
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                UPDATE datasets
                SET
                    status = $2,
                    prepared_object_key = $3,
                    rows_count = $4,
                    columns_count = $5,
                    error_message = NULL,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING
                    id,
                    name,
                    status,
                    raw_object_key,
                    prepared_object_key,
                    rows_count,
                    columns_count,
                    error_message,
                    created_at,
                    updated_at
                """,
                dataset_id,
                DatasetStatus.PREPARED.value,
                prepared_object_key,
                rows_count,
                columns_count,
            )

        if row is None:
            return None

        return DatasetTable(
            id=row["id"],
            name=row["name"],
            status=DatasetStatus(row["status"]),
            raw_object_key=row["raw_object_key"],
            prepared_object_key=row["prepared_object_key"],
            rows_count=row["rows_count"],
            columns_count=row["columns_count"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def save_schema(
        self,
        dataset_id: UUID,
        schema_data: list[ColumnSchema],
    ) -> bool:
        """
        Persists the inferred schema for a dataset.

        Serializes the inferred column definitions to JSON and upserts them in
        the dataset schema table. Existing schema metadata for the same dataset
        is replaced with the latest inferred schema.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset.
            schema_data (list[ColumnSchema]):
                Inferred schema generated during dataset preparation.

        Returns:
            bool:
                True when the schema persistence operation completes.
        """
        schema_json = json.dumps(
            [column.model_dump(mode="json") for column in schema_data]
        )

        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO dataset_schemas (dataset_id, columns, created_at, updated_at)
                VALUES ($1, $2, NOW(), NOW())
                ON CONFLICT (dataset_id)
                DO UPDATE SET
                    columns = EXCLUDED.columns,
                    updated_at = NOW()
                """,
                dataset_id,
                schema_json,
            )

        return True

    async def get_schema(self, dataset_id: UUID) -> Optional[list[ColumnSchema]]:
        """
        Retrieves the persisted inferred schema of a dataset.

        Args:
            dataset_id (UUID):
                Unique identifier of the dataset.

        Returns:
            Optional[list[ColumnSchema]]:
                Persisted column schema when available, otherwise None.
        """
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT columns
                FROM dataset_schemas
                WHERE dataset_id = $1
                """,
                dataset_id,
            )

        if row is None:
            return None

        columns = row["columns"]

        if isinstance(columns, str):
            columns = json.loads(columns)

        return [ColumnSchema(**column) for column in columns]


    async def save_profile(
        self,
        dataset_id: UUID,
        profile: dict,
    ) -> bool:
        """
        Persist dataset profiling metadata.

        Creates or updates the profiling metadata associated with a dataset.
        The profile is stored as JSONB in the ``dataset_profiles`` table.

        Args:
            dataset_id:
                Identifier of the dataset.
            profile:
                Generated profiling metadata.

        Returns:
            bool:
                True when the profile is successfully persisted.
        """
        async with self.pool.acquire() as connection:
            result = await connection.execute(
                """
                INSERT INTO dataset_profiles (
                    id,
                    dataset_id,
                    profile,
                    created_at,
                    updated_at
                )
                VALUES (
                    gen_random_uuid(),
                    $1,
                    $2::jsonb,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (dataset_id)
                DO UPDATE SET
                    profile = EXCLUDED.profile,
                    updated_at = NOW()
                """,
                dataset_id,
                json.dumps(profile),
            )

        return result in ("INSERT 0 1", "UPDATE 1")
