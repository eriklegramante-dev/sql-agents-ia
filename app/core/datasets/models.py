from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DatasetMetadata:
    """Domain model representing dataset metadata.

    This model belongs to the core layer and is independent of HTTP,
    Pydantic, FastAPI, and database-specific models.

    Attributes:
        dataset_id: Unique identifier of the dataset.
        name: Dataset display name.
        original_filename: Original uploaded filename.
        content_type: Dataset MIME type.
        file_size_bytes: Original file size in bytes.
        status: Current dataset processing status.
        object_key: Raw object key stored in object storage.
        description: Optional dataset description.
        created_at: Dataset creation timestamp.
        updated_at: Dataset last update timestamp.
    """

    dataset_id: UUID
    name: str
    original_filename: str | None
    content_type: str | None
    file_size_bytes: int | None
    status: str
    object_key: str
    description: str | None
    rows_count: int | None      
    columns_count: int | None   
    created_at: datetime
    updated_at: datetime