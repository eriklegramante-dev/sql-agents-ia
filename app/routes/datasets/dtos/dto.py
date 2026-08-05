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
        created_at: Dataset creation timestamp.
        updated_at: Dataset last update timestamp.

    Args:
        dataset_id: Dataset identifier used to create the response.
        name: Dataset name used to create the response.
        original_filename: Original filename used to create the response.
        content_type: Content type used to create the response.
        file_size_bytes: File size used to create the response.
        status: Dataset status used to create the response.
        object_key: Object storage key used to create the response.
        description: Dataset description used to create the response.
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
    created_at: datetime
    updated_at: datetime


class DatasetResponseDTO(BaseModel):
    """Standard response returned by the dataset retrieval route.

    Attributes:
        success: Indicates whether the request was successful.
        message: Human-readable response message.
        data: Retrieved dataset metadata.
        errors: Optional validation or processing errors.

    Args:
        success: Success flag used to create the response.
        message: Response message used to create the response.
        data: Dataset metadata used to create the response.
        errors: Errors used to create the response.
    """

    success: bool
    message: str
    data: DatasetResponseDataDTO | None = None
    errors: list[str] | None = None