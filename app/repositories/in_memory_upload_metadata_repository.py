from typing import Any

from app.repositories.upload_metadata_repository import UploadMetadataRepository


class InMemoryUploadMetadataRepository(UploadMetadataRepository):
    """In-memory repository used for local upload metadata persistence.

    Attributes:
        storage: Dictionary used to store upload metadata by composite key.
    """

    def __init__(self) -> None:
        """Initialize the in-memory upload metadata repository."""
        self.storage: dict[str, dict[str, Any]] = {}

    def create(self, metadata: dict[str, Any]) -> None:
        """Persist upload metadata.

        Args:
            metadata: Upload metadata payload.
        """
        key = self._build_key(
            dataset_id=metadata["dataset_id"],
            upload_id=metadata["upload_id"],
        )
        self.storage[key] = metadata

    def find_by_dataset_and_upload(
        self,
        dataset_id: str,
        upload_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve upload metadata.

        Args:
            dataset_id: Dataset identifier.
            upload_id: Upload identifier.

        Returns:
            Upload metadata if found, otherwise None.
        """
        key = self._build_key(dataset_id=dataset_id, upload_id=upload_id)
        return self.storage.get(key)

    def update_status(
        self,
        dataset_id: str,
        upload_id: str,
        upload_status: str,
        dataset_status: str,
    ) -> None:
        """Update upload and dataset statuses.

        Args:
            dataset_id: Dataset identifier.
            upload_id: Upload identifier.
            upload_status: Upload status value.
            dataset_status: Dataset status value.
        """
        metadata = self.find_by_dataset_and_upload(
            dataset_id=dataset_id,
            upload_id=upload_id,
        )

        if metadata is None:
            return

        metadata["upload_status"] = upload_status
        metadata["dataset_status"] = dataset_status

    def store_completed_parts(
        self,
        dataset_id: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> None:
        """Store completed multipart upload information.

        Args:
            dataset_id: Dataset identifier.
            upload_id: Upload identifier.
            parts: Completed upload parts.
        """
        metadata = self.find_by_dataset_and_upload(
            dataset_id=dataset_id,
            upload_id=upload_id,
        )

        if metadata is None:
            return

        metadata["completed_parts"] = parts

    def _build_key(self, dataset_id: str, upload_id: str) -> str:
        """Build the internal metadata storage key.

        Args:
            dataset_id: Dataset identifier.
            upload_id: Upload identifier.

        Returns:
            Composite metadata key.
        """
        return f"{dataset_id}:{upload_id}"