from datetime import timedelta
from typing import Any

from minio import Minio
from minio.error import S3Error

from app.adapters.storage.blob_storage_adapter import MultipartStorageAdapter
from app.adapters.storage.minio_multipart_client_adapter import (
    MultipartClientAdapter,
)


class MinioBlobStorageAdapter(MultipartStorageAdapter):
    """MinIO adapter responsible for multipart upload operations.

    Attributes:
        client: MinIO client used for public object storage operations.
        multipart_client: Adapter used for low-level multipart operations.
        bucket_name: Bucket used to store raw uploaded files.
        signed_url_expires_seconds: Expiration time for signed URLs.

    Args:
        client: MinIO SDK client instance used by this adapter.
        multipart_client: Multipart client adapter used by this adapter.
        bucket_name: Bucket used to store raw uploaded files.
        signed_url_expires_seconds: Expiration time for signed URLs.
    """

    def __init__(
        self,
        client: Minio,
        multipart_client: MultipartClientAdapter,
        bucket_name: str,
        signed_url_expires_seconds: int,
    ) -> None:
        """Initialize the MinIO blob storage adapter.

        Args:
            client: MinIO client instance.
            multipart_client: Adapter used for multipart operations.
            bucket_name: Bucket used to store raw uploaded files.
            signed_url_expires_seconds: Expiration time for signed URLs.
        """
        self.client = client
        self.multipart_client = multipart_client
        self.bucket_name = bucket_name
        self.signed_url_expires_seconds = signed_url_expires_seconds
        self._ensure_bucket_exists()

    def initialize_multipart_upload(
        self,
        object_key: str,
        content_type: str,
    ) -> str:
        """Start a multipart upload session.

        Args:
            object_key: Object storage key.
            content_type: File content type.

        Returns:
            Multipart upload identifier.
        """
        return self.multipart_client.initialize(
            bucket_name=self.bucket_name,
            object_key=object_key,
            content_type=content_type,
        )

    def generate_signed_part_url(
        self,
        object_key: str,
        upload_id: str,
        part_number: int,
    ) -> str:
        """Generate a signed URL for a multipart upload part.

        Args:
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
            part_number: Multipart part number.

        Returns:
            Signed upload URL.
        """
        return self.client.get_presigned_url(
            method="PUT",
            bucket_name=self.bucket_name,
            object_name=object_key,
            expires=timedelta(seconds=self.signed_url_expires_seconds),
            extra_query_params={
                "uploadId": upload_id,
                "partNumber": str(part_number),
            },
        )

    def complete_multipart_upload(
        self,
        object_key: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> None:
        """Finalize a multipart upload.

        Args:
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
            parts: Uploaded parts information.
        """
        self.multipart_client.complete(
            bucket_name=self.bucket_name,
            object_key=object_key,
            upload_id=upload_id,
            parts=parts,
        )

    def abort_multipart_upload(
        self,
        object_key: str,
        upload_id: str,
    ) -> None:
        """Abort a multipart upload.

        Args:
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
        """
        self.multipart_client.abort(
            bucket_name=self.bucket_name,
            object_key=object_key,
            upload_id=upload_id,
        )

    def cleanup_temporary_parts(
        self,
        object_key: str,
        upload_id: str,
    ) -> None:
        """Remove temporary multipart upload data.

        Args:
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
        """

    def _ensure_bucket_exists(self) -> None:
        """Create the configured bucket when it does not exist.

        Raises:
            S3Error: If MinIO cannot verify or create the bucket.
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error:
            raise
