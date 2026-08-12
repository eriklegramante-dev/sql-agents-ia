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

    Args:
        filename: File name provided when creating the request instance.
        content_type: MIME type provided when creating the request instance.
        file_size_bytes: File size provided when creating the request instance.
        dataset_name: Dataset name provided when creating the request instance.
        description: Optional description provided when creating the request instance.
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

    Args:
        part_number: Multipart part number used to create the DTO instance.
        upload_url: Signed URL used to create the DTO instance.
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

    Args:
        dataset_id: Dataset identifier used to create the response data.
        upload_id: Upload identifier used to create the response data.
        object_key: Object storage key used to create the response data.
        status: Upload status used to create the response data.
        chunk_size_bytes: Chunk size used to create the response data.
        chunks_count: Chunks count used to create the response data.
        parts: Signed parts used to create the response data.
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

    Args:
        success: Success flag used to create the response instance.
        message: Response message used to create the response instance.
        data: Response data used to create the response instance.
    """

    success: bool
    message: str
    data: UploadInitResponseDataDTO


class UploadPartDTO(BaseModel):
    """Uploaded multipart part received by the completion route.

    Attributes:
        part_number: Uploaded multipart part number.
        etag: Entity tag returned by object storage for the uploaded part.

    Args:
        part_number: Uploaded part number used to create the DTO instance.
        etag: Entity tag used to create the DTO instance.
    """

    part_number: int = Field(..., gt=0)
    etag: str = Field(..., min_length=1)

    @field_validator("etag")
    @classmethod
    def validate_etag_not_blank(cls, value: str) -> str:
        """Validate that the ETag is not blank.

        Args:
            value: ETag value to validate.

        Returns:
            The stripped ETag value.

        Raises:
            ValueError: If the ETag is empty after stripping spaces.
        """
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("ETag must not be blank.")
        return stripped_value


class UploadCompleteRequestDTO(BaseModel):
    """Request payload used to complete a multipart upload.

    Attributes:
        dataset_id: Dataset identifier associated with the upload.
        upload_id: Multipart upload identifier to complete.
        parts: Uploaded multipart parts to finalize.

    Args:
        dataset_id: Dataset identifier used to create the request instance.
        upload_id: Upload identifier used to create the request instance.
        parts: Uploaded parts used to create the request instance.
    """

    dataset_id: UUID 
    upload_id: str = Field(..., min_length=1)
    parts: list[UploadPartDTO] = Field(..., min_length=1)


class UploadCompleteResponseDataDTO(BaseModel):
    """Response data returned after upload completion execution.

    Attributes:
        dataset_id: Dataset identifier associated with the upload.
        upload_id: Multipart upload identifier.
        status: Final upload status after completion.
        object_key: Raw file object key in storage.
        completed_parts_count: Total number of completed parts.

    Args:
        dataset_id: Dataset identifier used to create the response data.
        upload_id: Upload identifier used to create the response data.
        status: Upload status used to create the response data.
        object_key: Object key used to create the response data.
        completed_parts_count: Completed parts count used to create the response data.
    """

    dataset_id: UUID 
    upload_id: str
    status: str
    object_key: str
    completed_parts_count: int


class UploadCompleteResponseDTO(BaseModel):
    """Standard response returned by the upload completion route.

    Attributes:
        success: Indicates whether the request was processed successfully.
        message: Human-readable response message.
        data: Upload completion response data.

    Args:
        success: Success flag used to create the response instance.
        message: Response message used to create the response instance.
        data: Response data used to create the response instance.
    """

    success: bool
    message: str
    data: UploadCompleteResponseDataDTO


class UploadAbortRequestDTO(BaseModel):
    """Request payload used to abort a multipart upload.

    Attributes:
        dataset_id: Dataset identifier associated with the upload.
        upload_id: Multipart upload identifier to abort.

    Args:
        dataset_id: Dataset identifier used to create the request instance.
        upload_id: Upload identifier used to create the request instance.
    """

    dataset_id: UUID 
    upload_id: str = Field(..., min_length=1)


class UploadAbortResponseDataDTO(BaseModel):
    """Response data returned after upload abort execution.

    Attributes:
        dataset_id: Dataset identifier associated with the upload.
        upload_id: Multipart upload identifier.
        upload_status: Final upload status after abort processing.
        dataset_status: Final dataset status after abort processing.

    Args:
        dataset_id: Dataset identifier used to create the response data.
        upload_id: Upload identifier used to create the response data.
        upload_status: Upload status used to create the response data.
        dataset_status: Dataset status used to create the response data.
    """

    dataset_id: UUID
    upload_id: str
    upload_status: str
    dataset_status: str


class UploadAbortResponseDTO(BaseModel):
    """Standard response returned by the upload abort route.

    Attributes:
        success: Indicates whether the request was processed successfully.
        message: Human-readable response message.
        data: Upload abort response data.

    Args:
        success: Success flag used to create the response instance.
        message: Response message used to create the response instance.
        data: Response data used to create the response instance.
    """

    success: bool
    message: str
    data: UploadAbortResponseDataDTO
