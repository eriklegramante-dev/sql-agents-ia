import json
from typing import Any
from uuid import UUID

import asyncpg

from app.core.datasets.exceptions import (
    DatasetRelatedRecordsDeletionException,
)
from app.core.datasets.models import DatasetMetadata, DatasetProfileSummary
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

    def _build_dataset(
        self,
        row: Any,
    ) -> DatasetTable:
        """
        Build a DatasetTable instance from a database row.

        This helper centralizes the conversion between database records and the
        application model, avoiding duplicated mapping logic across repository
        methods.

        Args:
            row:
                Database row returned by asyncpg.

        Returns:
            DatasetTable:
                Fully populated dataset model.
        """
        return DatasetTable(
            id=row["id"],
            name=row["name"],
            filename=row["filename"],
            status=DatasetStatus(row["status"]),
            raw_object_key=row["raw_object_key"],
            prepared_object_key=row["prepared_object_key"],
            user_id=row["user_id"],
            description=row["description"],
            file_type=row["file_type"],
            content_type=row["content_type"],
            file_size_bytes=row["file_size_bytes"],
            current_upload_job_id=row["current_upload_job_id"],
            rows_count=row["rows_count"],
            columns_count=row["columns_count"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _build_dataset_metadata(
        self,
        row: Any,
    ) -> DatasetMetadata:
        """Build domain dataset metadata from a database row.

        Args:
            row:
                Database row containing dataset and optional profile data.

        Returns:
            DatasetMetadata:
                Dataset metadata represented by the core domain model.
        """
        profile_data = row["profile"]
        profile = None

        if profile_data is not None:
            if isinstance(profile_data, str):
                profile_data = json.loads(profile_data)

            columns = profile_data.get("columns", [])
            nulls_summary = profile_data.get("nulls_summary", {})
            quality_warnings = profile_data.get("quality_warnings", [])

            profile = DatasetProfileSummary(
                total_nulls=int(
                    nulls_summary.get("total_nulls", 0)
                ),
                columns_with_nulls=int(
                    nulls_summary.get("columns_with_nulls", 0)
                ),
                numeric_columns=sum(
                    column.get("type") == "numeric"
                    for column in columns
                ),
                datetime_columns=sum(
                    column.get("type") == "datetime"
                    for column in columns
                ),
                text_columns=sum(
                    column.get("type") == "text"
                    for column in columns
                ),
                quality_warnings=tuple(quality_warnings),
            )

        return DatasetMetadata(
            dataset_id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            original_filename=row["filename"],
            content_type=row["content_type"],
            file_size_bytes=row["file_size_bytes"],
            status=DatasetStatus(row["status"]).value,
            object_key=row["raw_object_key"],
            description=row["description"],
            rows_count=row["rows_count"],
            columns_count=row["columns_count"],
            profile=profile,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create(
        self,
        dataset: DatasetTable,
    ) -> DatasetTable:
        """
        Persist a newly created dataset.

        This method is used during upload initialization to register the
        dataset metadata before the multipart upload begins.

        Args:
            dataset:
                Dataset metadata to be persisted.

        Returns:
            DatasetTable:
                The persisted dataset metadata.
        """
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO datasets (
                    id,
                    name,
                    filename,
                    status,
                    raw_object_key,
                    prepared_object_key,
                    user_id,
                    description,
                    file_type,
                    content_type,
                    file_size_bytes,
                    current_upload_job_id,
                    rows_count,
                    columns_count
                )
                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7,
                    $8,
                    $9,
                    $10,
                    $11,
                    $12,
                    $13,
                    $14
                )
                """,
                dataset.id,
                dataset.name,
                dataset.filename,
                dataset.status.value,
                dataset.raw_object_key,
                dataset.prepared_object_key,
                dataset.user_id,
                dataset.description,
                dataset.file_type,
                dataset.content_type,
                dataset.file_size_bytes,
                dataset.current_upload_job_id,
                dataset.rows_count,
                dataset.columns_count,
            )

        return dataset

    async def get_by_id(
        self,
        dataset_id: UUID,
    ) -> DatasetTable | None:
        """
        Retrieve dataset metadata by its unique identifier.

        Args:
            dataset_id:
                Unique identifier of the dataset.

        Returns:
            DatasetTable:
                Dataset metadata when found.

            None:
                If the dataset does not exist.
        """
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT
                    id,
                    name,
                    filename,
                    status,
                    raw_object_key,
                    prepared_object_key,
                    user_id,
                    description,
                    file_type,
                    content_type,
                    file_size_bytes,
                    current_upload_job_id,
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

        return self._build_dataset(row)

    async def get_metadata_by_id(
        self,
        dataset_id: UUID,
    ) -> DatasetMetadata | None:
        """
        Retrieve dataset metadata using the domain model.

        This method adapts dataset persistence data and its optional profiling
        summary into the domain model required by the dataset core layer,
        keeping database-specific structures isolated from workflows.

        Args:
            dataset_id:
                Unique identifier of the dataset.

        Returns:
            DatasetMetadata:
                Domain dataset metadata when the dataset exists.

            None:
                If the dataset does not exist.
        """
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT
                    d.id,
                    d.user_id,
                    d.name,
                    d.filename,
                    d.status,
                    d.raw_object_key,
                    d.description,
                    d.content_type,
                    d.file_size_bytes,
                    d.rows_count,
                    d.columns_count,
                    d.created_at,
                    d.updated_at,
                    dp.profile
                FROM datasets AS d
                LEFT JOIN dataset_profiles AS dp
                    ON dp.dataset_id = d.id
                WHERE d.id = $1
                """,
                dataset_id,
            )

        if row is None:
            return None

        return self._build_dataset_metadata(row)

    async def list_metadata(
        self,
        *,
        user_id: int,
    ) -> list[DatasetMetadata]:
        """Retrieve non-deleted metadata with a parameterized owner filter.

        Args:
            user_id: Trusted caller identity used to scope the repository lookup.

        Returns:
            Dataset metadata with optional profiling, newest first.

        Repository failures propagate to the caller.
        """
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT
                    d.id,
                    d.user_id,
                    d.name,
                    d.filename,
                    d.status,
                    d.raw_object_key,
                    d.description,
                    d.content_type,
                    d.file_size_bytes,
                    d.rows_count,
                    d.columns_count,
                    d.created_at,
                    d.updated_at,
                    dp.profile
                FROM datasets AS d
                LEFT JOIN dataset_profiles AS dp
                    ON dp.dataset_id = d.id
                WHERE d.status <> $1
                  AND d.user_id = $2
                ORDER BY d.created_at DESC
                """,
                DatasetStatus.DELETED.value,
                user_id,
            )

        return [
            self._build_dataset_metadata(row)
            for row in rows
        ]

    async def find_by_upload(
        self,
        dataset_id: UUID,
        upload_id: str,
    ) -> DatasetTable | None:
        """
        Retrieve dataset metadata associated with an active multipart upload.

        This method is used during upload completion and abort workflows to
        locate the dataset linked to the provided upload identifier.

        Args:
            dataset_id:
                Dataset identifier.
            upload_id:
                Multipart upload identifier.

        Returns:
            DatasetTable:
                Dataset metadata when found.

            None:
                If no matching upload exists.
        """
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT
                    id,
                    name,
                    filename,
                    status,
                    raw_object_key,
                    prepared_object_key,
                    user_id,
                    description,
                    file_type,
                    content_type,
                    file_size_bytes,
                    current_upload_job_id,
                    rows_count,
                    columns_count,
                    error_message,
                    created_at,
                    updated_at
                FROM datasets
                WHERE
                    id = $1
                AND current_upload_job_id = $2
                """,
                dataset_id,
                upload_id,
            )

        if row is None:
            return None

        return self._build_dataset(row)

    async def update_upload_status(
        self,
        dataset_id: UUID,
        upload_id: str,
        status: DatasetStatus,
    ) -> bool:
        """
        Update the status of a dataset identified by both the dataset ID and
        the active multipart upload ID.

        This method guarantees that only the dataset currently associated with
        the specified multipart upload is updated.

        Args:
            dataset_id:
                Dataset identifier.
            upload_id:
                Multipart upload identifier.
            status:
                New dataset status.

        Returns:
            True when exactly one dataset row is updated, otherwise False.
        """
        async with self.pool.acquire() as connection:
            result = await connection.execute(
                """
                UPDATE datasets
                SET
                    status = $3,
                    updated_at = NOW()
                WHERE
                    id = $1
                AND current_upload_job_id = $2
                """,
                dataset_id,
                upload_id,
                status.value,
            )

        return result == "UPDATE 1"

    async def update_status(
        self,
        dataset_id: UUID,
        status: DatasetStatus,
        error_message: str | None = None,
    ) -> bool:
        """
        Update the processing status of a dataset.

        Args:
            dataset_id:
                Unique identifier of the dataset.
            status:
                New dataset processing status.
            error_message:
                Optional error message associated with the update.

        Returns:
            bool:
                True when exactly one dataset row is updated.
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
    ) -> DatasetTable | None:
        """
        Persist metadata generated after successful dataset preparation.

        Args:
            dataset_id:
                Dataset identifier.
            prepared_object_key:
                Generated Parquet object key.
            rows_count:
                Dataset row count.
            columns_count:
                Dataset column count.

        Returns:
            Updated dataset metadata.
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
                    filename,
                    status,
                    raw_object_key,
                    prepared_object_key,
                    user_id,
                    description,
                    file_type,
                    content_type,
                    file_size_bytes,
                    current_upload_job_id,
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

        return self._build_dataset(row)

    async def save_schema(
        self,
        dataset_id: UUID,
        schema_data: list[ColumnSchema],
    ) -> bool:
        """
        Persist the inferred schema generated for a dataset.

        Args:
            dataset_id:
                Dataset identifier.
            schema_data:
                Collection of inferred dataset columns.

        Returns:
            bool:
                True when the schema is successfully persisted.
        """
        schema_json = json.dumps(
            [column.model_dump(mode="json") for column in schema_data]
        )

        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO dataset_schemas (
                    dataset_id,
                    columns,
                    created_at,
                    updated_at
                )
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

    async def get_schema(
        self,
        dataset_id: UUID,
    ) -> list[ColumnSchema] | None:
        """
        Retrieve the persisted schema associated with a dataset.

        Args:
            dataset_id:
                Dataset identifier.

        Returns:
            list[ColumnSchema]:
                Persisted schema when available.

            None:
                If no schema has been stored.
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
        Persist profiling metadata generated for a dataset.

        Args:
            dataset_id:
                Dataset identifier.
            profile:
                Generated profiling information.

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

    async def delete_related_records(
        self,
        dataset_id: UUID,
    ) -> None:
        """Remove persistence records related to a dataset.

        Both delete operations run inside the same PostgreSQL transaction.
        The dataset metadata itself is preserved for soft-delete tracking.

        Args:
            dataset_id:
                Unique identifier of the dataset.

        Raises:
            DatasetRelatedRecordsDeletionException:
                If PostgreSQL cannot complete the related-record cleanup.
        """
        try:
            async with (
                self.pool.acquire() as connection,
                connection.transaction(),
            ):
                await connection.execute(
                    """
                    DELETE FROM dataset_schemas
                    WHERE dataset_id = $1
                    """,
                    dataset_id,
                )

                await connection.execute(
                    """
                    DELETE FROM dataset_profiles
                    WHERE dataset_id = $1
                    """,
                    dataset_id,
                )

        except asyncpg.PostgresError as error:
            raise DatasetRelatedRecordsDeletionException(
                dataset_id=dataset_id,
            ) from error
