from abc import ABC, abstractmethod
from typing import Any


class BlobStorageAdapter(ABC):
    """Storage abstraction responsible for multipart upload operations."""

    @abstractmethod
    def initialize_multipart_upload(
        self,
        object_key: str,
        content_type: str,
    ) -> str:
        """Start a multipart upload session."""
        raise NotImplementedError

    @abstractmethod
    def generate_signed_part_url(
        self,
        object_key: str,
        upload_id: str,
        part_number: int,
    ) -> str:
        """Generate a signed URL for a multipart upload part."""
        raise NotImplementedError

    @abstractmethod
    def complete_multipart_upload(
        self,
        object_key: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> None:
        """Finalize a multipart upload."""
        raise NotImplementedError

    @abstractmethod
    def abort_multipart_upload(
        self,
        object_key: str,
        upload_id: str,
    ) -> None:
        """Abort a multipart upload."""
        raise NotImplementedError

    @abstractmethod
    def cleanup_temporary_parts(
        self,
        object_key: str,
        upload_id: str,
    ) -> None:
        """Remove temporary multipart upload data."""
        raise NotImplementedError