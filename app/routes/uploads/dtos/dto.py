from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UploadInitRequestDTO(BaseModel):
    """Request payload used to initialize a multipart upload.

    Attributes:
        filename: Original file name sent by the client.
        content_type: MIME type of the uploaded file.
        file_size_bytes: Total file size in bytes.
        dataset_name: Human-readable dataset name.
        description: Optional dataset description.
    """

    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1, max_length=100)
    file_size_bytes: int = Field(..., gt=0)
    dataset_name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("filename", "content_type", "dataset_name")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        """Validate that string fields are not blank.

        Args:
            value: Field value to validate.

        Returns:
            The stripped field value.

        Raises:
            ValueError: If the value is empty after stripping spaces.
        """
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("Field must not be blank.")
        return stripped_value


class UploadSignedPartDTO(BaseModel):
    """Signed upload URL returned for each multipart part.

    Attributes:
        part_number: Multipart part number.
        upload_url: Signed URL used by the frontend to upload the part.
    """

    part_number: int
    upload_url: str


class UploadInitResponseDataDTO(BaseModel):
    """Response data returned after upload initialization.

    Attributes:
        dataset_id: Generated dataset identifier.
        upload_id: Multipart upload identifier.
        object_key: Raw file object key in storage.
        status: Current upload status.
        chunk_size_bytes: Chunk size used for upload planning.
        chunks_count: Total expected number of chunks.
        parts: Signed upload URLs for all expected chunks.
    """

    dataset_id: UUID
    upload_id: str
    object_key: str
    status: str
    chunk_size_bytes: int
    chunks_count: int
    parts: list[UploadSignedPartDTO]


class UploadInitResponseDTO(BaseModel):
    """Standard response returned by the upload initialization route.

    Attributes:
        success: Indicates whether the request was processed successfully.
        message: Human-readable response message.
        data: Upload initialization response data.
    """

    success: bool
    message: str
    data: UploadInitResponseDataDTO
    

class UploadAbortRequestDTO(BaseModel):
    """Request payload used to abort a multipart upload.

    Attributes:
        dataset_id: Dataset identifier associated with the upload.
        upload_id: Multipart upload identifier to abort.
    """

    dataset_id: UUID | str = Field(...)
    upload_id: str = Field(..., min_length=1)


class UploadAbortResponseDataDTO(BaseModel):
    """Response data returned after upload abort execution.

    Attributes:
        dataset_id: Dataset identifier associated with the upload.
        upload_id: Multipart upload identifier.
        upload_status: Final upload status after abort processing.
        dataset_status: Final dataset status after abort processing.
    """

    dataset_id: UUID | str
    upload_id: str
    upload_status: str
    dataset_status: str


class UploadAbortResponseDTO(BaseModel):
    """Standard response returned by the upload abort route.

    Attributes:
        success: Indicates whether the request was processed successfully.
        message: Human-readable response message.
        data: Upload abort response data.
    """

    success: bool
    message: str
    data: UploadAbortResponseDataDTO