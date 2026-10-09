from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DatasetRequestDTO(BaseModel):
    """Request payload used to retrieve dataset metadata.

    Attributes:
        dataset_id: Unique identifier of the dataset to retrieve.

    Args:
        dataset_id: Dataset identifier used to create the request instance.
    """

    dataset_id: UUID = Field(
        ...,
        description="Unique dataset identifier.",
    )


class DatasetResponseDataDTO(BaseModel):
    """Dataset metadata returned after a successful retrieval.

    Attributes:
        dataset_id: Unique dataset identifier.
        name: Dataset display name.
        original_filename: Original uploaded filename.
        content_type: Dataset MIME type.
        file_size_bytes: Original file size in bytes.
        status: Current dataset processing status.
        object_key: Raw object key stored in object storage.
        description: Optional dataset description.
        rows_count: Number of rows in the prepared dataset.
        columns_count: Number of columns in the prepared dataset.
        total_nulls: Total number of null cells found during profiling.
        columns_with_nulls: Number of columns containing null values.
        numeric_columns: Number of columns classified as numeric.
        datetime_columns: Number of columns classified as datetime.
        text_columns: Number of columns classified as text.
        quality_warnings: Data quality warnings generated during profiling.
        created_at: Dataset creation timestamp.
        updated_at: Dataset last update timestamp.
    """

    dataset_id: UUID
    name: str
    original_filename: str | None = None
    content_type: str | None = None
    file_size_bytes: int | None = None
    status: str
    object_key: str
    description: str | None = None
    rows_count: int | None = None
    columns_count: int | None = None
    total_nulls: int | None = None
    columns_with_nulls: int | None = None
    numeric_columns: int | None = None
    datetime_columns: int | None = None
    text_columns: int | None = None
    quality_warnings: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class DatasetResponseDTO(BaseModel):
    """Standard response returned by the dataset retrieval route.

    Attributes:
        success: Indicates whether the retrieval operation was successful.
        message: Human-readable result of the retrieval operation.
        data: Retrieved dataset metadata when the operation succeeds.
        errors: Optional errors produced during the operation.

    Args:
        success: Success flag used to create the response.
        message: Response message used to create the response.
        data: Dataset metadata included in the response.
        errors: Errors included when the operation fails.
    """

    success: bool
    message: str
    data: DatasetResponseDataDTO | None = None
    errors: list[str] | None = None


class DatasetListResponseDTO(BaseModel):
    """Standard response returned by the dataset listing route.

    Attributes:
        success: Indicates whether the listing operation was successful.
        message: Human-readable result of the listing operation.
        data: Collection of active dataset metadata.
        errors: Optional errors produced during the operation.

    Args:
        success: Success flag used to create the response.
        message: Response message used to create the response.
        data: Dataset metadata collection included in the response.
        errors: Errors included when the operation fails.
    """

    success: bool
    message: str
    data: list[DatasetResponseDataDTO]
    errors: list[str] | None = None


class DatasetDeleteResponseDataDTO(BaseModel):
    """Dataset state returned after a successful deletion operation.

    Attributes:
        dataset_id: Unique identifier of the deleted dataset.
        status: Final dataset status after the deletion operation.
        updated_at: Timestamp of the dataset deletion status update.

    Args:
        dataset_id: Identifier of the dataset affected by the deletion.
        status: Final status assigned to the dataset.
        updated_at: Timestamp of the final dataset update.
    """

    dataset_id: UUID
    status: str
    updated_at: datetime


class DatasetDeleteResponseDTO(BaseModel):
    """Standard response returned by the dataset deletion route.

    Attributes:
        success: Indicates whether the deletion operation was successful.
        message: Human-readable result of the deletion operation.
        data: Final state of the dataset after a successful deletion.
        errors: Optional errors produced during the deletion operation.

    Args:
        success: Success flag used to create the response.
        message: Response message used to create the response.
        data: Deleted dataset information included in the response.
        errors: Errors included when the deletion operation fails.
    """

    success: bool
    message: str
    data: DatasetDeleteResponseDataDTO | None = None
    errors: list[str] | None = None

class DatasetListResponseDTO(BaseModel):
    """Standard response returned by the dataset listing route.

    Attributes:
        success: Indicates whether the listing operation was successful.
        message: Human-readable result of the listing operation.
        data: Dataset metadata returned by the listing operation.
        errors: Optional errors produced during the listing operation.

    Args:
        success: Success flag used to create the response.
        message: Response message used to create the response.
        data: Dataset metadata included in the response.
        errors: Errors included when the listing operation fails.
    """

    success: bool
    message: str
    data: list[DatasetResponseDataDTO]
    errors: list[str] | None = None
