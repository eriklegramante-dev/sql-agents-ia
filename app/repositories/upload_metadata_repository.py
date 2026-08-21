from abc import ABC, abstractmethod
from typing import Any

from uuid import UUID


class UploadMetadataRepository(ABC):
    """Repository abstraction responsible for upload metadata persistence."""

    @abstractmethod
    async def create(
        self,
        metadata: dict[str, Any],
    ) -> None:
        """Persist upload metadata."""
        raise NotImplementedError

    @abstractmethod
    async def find_by_dataset_and_upload(
        self,
        dataset_id: UUID,
        upload_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve upload metadata."""
        raise NotImplementedError

    @abstractmethod
    async def update_status(
        self,
        dataset_id: UUID,
        upload_id: str,
        upload_status: str,
        dataset_status: str,
    ) -> None:
        """Update upload and dataset statuses."""
        raise NotImplementedError

    @abstractmethod
    async def store_completed_parts(
        self,
        dataset_id: UUID,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> None:
        """Store completed multipart upload information."""
        raise NotImplementedError
