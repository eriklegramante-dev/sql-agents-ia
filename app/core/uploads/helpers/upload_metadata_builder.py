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
    ) -> dict[str, Any]:
        """
        Build the initial upload metadata payload.
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
        }
