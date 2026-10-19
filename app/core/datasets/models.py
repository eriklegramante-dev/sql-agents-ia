from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DatasetProfileSummary:
    """Domain model representing summarized dataset profiling information.

    Attributes:
        total_nulls: Total number of null cells in the dataset.
        columns_with_nulls: Number of columns containing null values.
        numeric_columns: Number of columns classified as numeric.
        datetime_columns: Number of columns classified as datetime.
        text_columns: Number of columns classified as text.
        quality_warnings: Data quality warnings generated during profiling.
    """

    total_nulls: int
    columns_with_nulls: int
    numeric_columns: int
    datetime_columns: int
    text_columns: int
    quality_warnings: tuple[str, ...]


@dataclass(frozen=True)
class DatasetMetadata:
    """Domain model representing dataset metadata.

    This model belongs to the core layer and is independent of HTTP,
    Pydantic, FastAPI, and database-specific models.

    Attributes:
        dataset_id: Unique identifier of the dataset.
        user_id: Optional dataset owner identifier used for authorization.
        name: Dataset display name.
        original_filename: Original uploaded filename.
        content_type: Dataset MIME type.
        file_size_bytes: Original file size in bytes.
        status: Current dataset processing status.
        object_key: Raw object key stored in object storage.
        description: Optional dataset description.
        rows_count: Number of rows in the prepared dataset.
        columns_count: Number of columns in the prepared dataset.
        profile: Optional summarized profiling information.
        created_at: Dataset creation timestamp.
        updated_at: Dataset last update timestamp.
    """

    dataset_id: UUID
    user_id: int | None
    name: str
    original_filename: str | None
    content_type: str | None
    file_size_bytes: int | None
    status: str
    object_key: str
    description: str | None
    rows_count: int | None
    columns_count: int | None
    profile: DatasetProfileSummary | None
    created_at: datetime
    updated_at: datetime