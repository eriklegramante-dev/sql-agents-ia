from datetime import timedelta
from io import BytesIO
from typing import Any

from minio import Minio
from minio.error import S3Error

from app.adapters.storage.base import StorageAdapter
from app.adapters.storage.blob_storage_adapter import MultipartStorageAdapter
from app.adapters.storage.exceptions import StorageOperationError
from app.adapters.storage.minio_multipart_client_adapter import (
    MultipartClientAdapter,
)


class MinioBlobStorageAdapter(
    StorageAdapter,
    MultipartStorageAdapter,
):
    """MinIO storage adapter for dataset files and multipart uploads.

    Provides object storage operations required by dataset workflows while
    keeping MinIO-specific SDK calls outside the application core.

    Attributes:
        client: MinIO client used for object operations.
        signing_client: Client used to sign multipart URLs for the caller.
        multipart_client: Adapter used for multipart upload operations.
        bucket_name: Bucket where dataset objects are stored.
        signed_url_expires_seconds: Expiration time for signed part URLs.
    """

    def __init__(
        self,
        client: Minio,
        multipart_client: MultipartClientAdapter,
        bucket_name: str,
        signed_url_expires_seconds: int,
        signing_client: Minio | None = None,
    ) -> None:
        """Initialize storage clients and ensure the configured bucket exists.

        Args:
            client: MinIO client used to access stored objects.
            multipart_client: Client adapter used for multipart operations.
            bucket_name: Bucket used to store dataset files.
            signed_url_expires_seconds: Lifetime of generated signed URLs.
            signing_client: Optional client used to sign part URLs. The object
                storage client is used when this dependency is omitted.

        Bucket lookup and creation failures propagate to the caller.
        """
        self.client = client
        self.signing_client = signing_client if signing_client is not None else client
        self.multipart_client = multipart_client
        self.bucket_name = bucket_name
        self.signed_url_expires_seconds = signed_url_expires_seconds

        self._ensure_bucket_exists()

    async def read_file(
        self,
        container: str,
        path: str,
    ) -> bytes:
        """Read a dataset object from the configured MinIO bucket.

        Args:
            container: Logical container required by the storage contract.
            path: Object key of the file to retrieve.

        Returns:
            Binary content stored at the requested object key.

        Raises:
            FileNotFoundError: If the requested object does not exist.
            StorageOperationError: If MinIO fails while reading the object.
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=path,
            )

            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        except S3Error as error:
            if error.code in {
                "NoSuchKey",
                "NoSuchObject",
                "NoSuchBucket",
            }:
                raise FileNotFoundError(
                    f"Object {path} not found in bucket {self.bucket_name}"
                ) from error

            raise StorageOperationError(operation=f"read object {path}") from error

    async def write_file(
        self,
        container: str,
        path: str,
        data: bytes,
    ) -> str:
        """Store binary dataset content in the configured MinIO bucket.

        Args:
            container: Logical container required by the storage contract.
            path: Object key where the file will be stored.
            data: Binary content to upload.

        Returns:
            Object key of the stored file.

        Raises:
            StorageOperationError: If MinIO fails while writing the object.
        """
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=path,
                data=BytesIO(data),
                length=len(data),
            )

            return path

        except S3Error as error:
            raise StorageOperationError(operation=f"write object {path}") from error

    async def file_exists(
        self,
        container: str,
        path: str,
    ) -> bool:
        """Check whether a dataset object exists in MinIO.

        Args:
            container: Logical container required by the storage contract.
            path: Object key to verify.

        Returns:
            True when the object exists, otherwise False.

        Raises:
            StorageOperationError: If MinIO cannot validate object existence.
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=path,
            )

            return True

        except S3Error as error:
            if error.code in {
                "NoSuchKey",
                "NoSuchObject",
                "NoSuchBucket",
            }:
                return False

            raise StorageOperationError(operation=f"check object {path}") from error

    async def delete_file(
        self,
        container: str,
        path: str,
    ) -> bool:
        """Remove a dataset object from the configured MinIO bucket.

        Args:
            container: Logical container required by the storage contract.
            path: Object key of the file to remove.

        Returns:
            True when the object existed and was removed, otherwise False.

        Raises:
            StorageOperationError: If MinIO fails during object deletion.
        """
        try:
            if not await self.file_exists(
                container=container,
                path=path,
            ):
                return False

            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=path,
            )

            return True

        except S3Error as error:
            raise StorageOperationError(operation=f"delete object {path}") from error

    def initialize_multipart_upload(
        self,
        object_key: str,
        content_type: str,
    ) -> str:
        """Initialize a multipart upload for a dataset object.

        Args:
            object_key: Object key that will receive the uploaded file.
            content_type: MIME type of the uploaded dataset.

        Returns:
            Multipart upload identifier generated by MinIO.
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
        """Generate a signed PUT URL for one multipart upload part.

        Uses the injected signing client and configured expiration. Multipart
        initialization and object access continue to use the storage clients.

        Args:
            object_key: Object key associated with the multipart upload.
            upload_id: Identifier of the active multipart upload.
            part_number: Number of the part to upload.

        Returns:
            Signed MinIO URL containing the upload ID and part number.

        Signing client failures propagate to the caller.
        """
        return self.signing_client.get_presigned_url(
            method="PUT",
            bucket_name=self.bucket_name,
            object_name=object_key,
            expires=timedelta(
                seconds=self.signed_url_expires_seconds,
            ),
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
        """Finalize a multipart dataset upload in MinIO.

        Args:
            object_key: Object key associated with the upload.
            upload_id: Multipart upload identifier.
            parts: Uploaded part numbers and ETags used for completion.
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
        """Abort an active multipart dataset upload.

        Args:
            object_key: Object key associated with the upload.
            upload_id: Multipart upload identifier to cancel.
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
        """Provide the multipart temporary-parts cleanup contract.

        Args:
            object_key: Object key associated with the multipart upload.
            upload_id: Multipart upload identifier whose parts would be cleaned.
        """

    def _ensure_bucket_exists(self) -> None:
        """Ensure the configured dataset bucket exists before storage use."""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
