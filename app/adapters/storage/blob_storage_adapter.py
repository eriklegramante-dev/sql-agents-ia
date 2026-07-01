from abc import ABC, abstractmethod
from typing import Any

from azure.storage.blob import BlobServiceClient

from app.adapters.storage.base import StorageAdapter


class MultipartStorageAdapter(ABC):
    """
    Storage abstraction responsible for multipart upload operations.

    This contract is used by upload workflows that need to initialize,
    sign, complete, abort, or clean multipart upload sessions.

    Attributes:
        None.
    """

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


class BlobStorageAdapter(StorageAdapter):
    """
    Adapter responsible for integrating the application with Azure Blob Storage.

    This class implements the StorageAdapter contract for cloud storage operations,
    allowing workflows and services to read, write, verify, and delete dataset files
    without depending directly on Azure-specific APIs.

    Attributes:
        client: Azure Blob Storage client used to access containers and blobs.
    """

    def __init__(self, connection_string: str | None):
        if not connection_string:
            raise ValueError("Azure storage connection string is required")

        self.client = BlobServiceClient.from_connection_string(connection_string)

    async def read_file(self, container: str, path: str) -> bytes:
        """
        Reads a file from Azure Blob Storage.
        """
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        if not blob_client.exists():
            raise FileNotFoundError(f"File {path} not found in container {container}")

        stream = blob_client.download_blob()
        return stream.readall()

    async def write_file(self, container: str, path: str, data: bytes) -> str:
        """
        Writes a file to Azure Blob Storage.
        """
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        blob_client.upload_blob(data, overwrite=True)
        return path

    async def file_exists(self, container: str, path: str) -> bool:
        """
        Checks whether a file exists in Azure Blob Storage.
        """
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        return blob_client.exists()

    async def delete_file(self, container: str, path: str) -> bool:
        """
        Deletes a file from Azure Blob Storage.
        """
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        if not blob_client.exists():
            return False

        blob_client.delete_blob()
        return True
