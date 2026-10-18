from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.uploads.enums import DatasetStatus, UploadStatus


class UploadMetadataBuilder:
    """
    Helper responsible for building upload metadata payloads.

    Attributes:
        None.
    """

    def build(
        self,
        dataset_id: UUID,
        upload_id: str,
        filename: str,
        content_type: str,
        file_size_bytes: int,
        dataset_name: str,
        description: str | None,
        object_key: str,
        chunk_size_bytes: int,
        chunks_count: int,
        *,
        user_id: int,
    ) -> dict[str, Any]:
        """Build initial upload metadata including the trusted dataset owner.

        Args:
            dataset_id: Identifier allocated for the new dataset.
            upload_id: Multipart session identifier returned by storage.
            filename: Original upload filename.
            content_type: Validated upload media type.
            file_size_bytes: Declared upload size in bytes.
            dataset_name: Normalized dataset display name.
            description: Optional dataset description.
            object_key: Storage key allocated for the raw upload.
            chunk_size_bytes: Planned size of each multipart chunk.
            chunks_count: Planned number of multipart chunks.
            user_id: Trusted caller identity to persist as dataset owner.

        Returns:
            Metadata dictionary with initial statuses and UTC timestamp strings.
        """
        current_time = datetime.now(timezone.utc).isoformat()

        return {
            "dataset_id": str(dataset_id),
            "upload_id": upload_id,
            "filename": filename,
            "content_type": content_type,
            "file_size_bytes": file_size_bytes,
            "dataset_name": dataset_name,
            "description": description,
            "object_key": object_key,
            "chunk_size_bytes": chunk_size_bytes,
            "chunks_count": chunks_count,
            "upload_status": UploadStatus.UPLOADING.value,
            "dataset_status": DatasetStatus.UPLOADING.value,
            "created_at": current_time,
            "updated_at": current_time,
            "user_id": user_id,
        }
