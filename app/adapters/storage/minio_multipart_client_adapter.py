from typing import Any, Protocol

from minio import Minio
from minio.datatypes import Part
from minio.error import S3Error
from urllib3.exceptions import HTTPError

from app.adapters.storage.exceptions import StorageOperationError


class MultipartClientAdapter(Protocol):
    """Contract for low-level multipart storage operations.

    Attributes:
        None.

    Args:
        None.
    """

    def initialize(
        self,
        bucket_name: str,
        object_key: str,
        content_type: str,
    ) -> str:
        """Initialize a multipart upload.

        Args:
            bucket_name: Storage bucket name.
            object_key: Object storage key.
            content_type: Uploaded file content type.

        Returns:
            Multipart upload identifier.
        """
        ...

    def complete(
        self,
        bucket_name: str,
        object_key: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> None:
        """Complete a multipart upload.

        Args:
            bucket_name: Storage bucket name.
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
            parts: Uploaded multipart parts.
        """
        ...

    def abort(
        self,
        bucket_name: str,
        object_key: str,
        upload_id: str,
    ) -> None:
        """Abort a multipart upload.

        Args:
            bucket_name: Storage bucket name.
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
        """
        ...


class MinioMultipartClientAdapter:
    """Adapter responsible for isolating MinIO multipart private APIs.

    Attributes:
        client: MinIO SDK client used for multipart operations.

    Args:
        client: MinIO SDK client instance used by this adapter.
    """

    def __init__(self, client: Minio) -> None:
        """Initialize the MinIO multipart client adapter.

        Args:
            client: MinIO SDK client instance.
        """
        self.client = client

    def initialize(
        self,
        bucket_name: str,
        object_key: str,
        content_type: str,
    ) -> str:
        """Initialize a multipart upload through the MinIO SDK.

        Args:
            bucket_name: Storage bucket name.
            object_key: Object storage key.
            content_type: Uploaded file content type.

        Returns:
            Multipart upload identifier.

        Raises:
            StorageOperationError: If MinIO cannot initialize the upload.
        """
        try:
            return self.client._create_multipart_upload(
                bucket_name=bucket_name,
                object_name=object_key,
                headers={"Content-Type": content_type},
            )
        except (S3Error, HTTPError) as exc:
            raise StorageOperationError(
                operation="initialize multipart upload"
            ) from exc

    def complete(
        self,
        bucket_name: str,
        object_key: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> None:
        """Complete a multipart upload through the MinIO SDK.

        Args:
            bucket_name: Storage bucket name.
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
            parts: Uploaded multipart parts.

        Raises:
            StorageOperationError: If MinIO cannot complete the upload.
        """
        minio_parts = [
            Part(
                part_number=part["part_number"],
                etag=part["etag"],
            )
            for part in parts
        ]

        try:
            self.client._complete_multipart_upload(
                bucket_name=bucket_name,
                object_name=object_key,
                upload_id=upload_id,
                parts=minio_parts,
            )

        except (S3Error, HTTPError) as exc:
            raise StorageOperationError(
                operation="complete multipart upload"
            ) from exc

    def abort(
        self,
        bucket_name: str,
        object_key: str,
        upload_id: str,
    ) -> None:
        """Abort a multipart upload through the MinIO SDK.

        Args:
            bucket_name: Storage bucket name.
            object_key: Object storage key.
            upload_id: Multipart upload identifier.

        Raises:
            StorageOperationError: If MinIO cannot abort the upload.
        """
        try:
            self.client._abort_multipart_upload(
                bucket_name=bucket_name,
                object_name=object_key,
                upload_id=upload_id,
            )
        except (S3Error, HTTPError) as exc:
            raise StorageOperationError(
                operation="abort multipart upload"
            ) from exc
