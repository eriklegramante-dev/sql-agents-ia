from uuid import uuid4

from app.adapters.storage.blob_storage_adapter import BlobStorageAdapter


class FakeBlobStorageAdapter(BlobStorageAdapter):
    """Fake storage adapter used for local multipart upload simulation."""

    def initialize_multipart_upload(
        self,
        object_key: str,
        content_type: str,
    ) -> str:
        """Start a fake multipart upload session.

        Args:
            object_key: Object storage key.
            content_type: File content type.

        Returns:
            Generated fake upload identifier.
        """
        return f"fake-upload-{uuid4()}"

    def generate_signed_part_url(
        self,
        object_key: str,
        upload_id: str,
        part_number: int,
    ) -> str:
        """Generate a fake signed URL for a multipart upload part.

        Args:
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
            part_number: Multipart part number.

        Returns:
            Fake signed upload URL.
        """
        return (
            "https://fake-storage.local/upload"
            f"?object_key={object_key}"
            f"&upload_id={upload_id}"
            f"&part_number={part_number}"
        )

    def complete_multipart_upload(
        self,
        object_key: str,
        upload_id: str,
        parts: list[dict[str, str]],
    ) -> None:
        """Finalize a fake multipart upload.

        Args:
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
            parts: Uploaded parts information.
        """

    def abort_multipart_upload(
        self,
        object_key: str,
        upload_id: str,
    ) -> None:
        """Abort a fake multipart upload.

        Args:
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
        """

    def cleanup_temporary_parts(
        self,
        object_key: str,
        upload_id: str,
    ) -> None:
        """Remove fake temporary multipart upload data.

        Args:
            object_key: Object storage key.
            upload_id: Multipart upload identifier.
        """