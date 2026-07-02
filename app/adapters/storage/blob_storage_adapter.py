from azure.storage.blob import BlobServiceClient

from app.adapters.storage.base import StorageAdapter


class BlobStorageAdapter(StorageAdapter):
    """
    Adapter responsible for integrating the application with Azure Blob Storage.

    This class implements the StorageAdapter contract for cloud storage operations,
    allowing workflows and services to read, write, verify, and delete dataset files
    without depending directly on Azure-specific APIs. It is mainly used by
    preparation workflows to load raw uploaded files and persist prepared files,
    such as Parquet datasets.

    Attributes:
        client (BlobServiceClient): Azure Blob Storage client used to access
            containers and blobs.
    """

    def __init__(self, connection_string: str | None):
        if not connection_string:
            raise ValueError("Azure storage connection string is required")

        self.client = BlobServiceClient.from_connection_string(connection_string)

    async def read_file(self, container: str, path: str) -> bytes:
        """
        Reads a file from Azure Blob Storage.

        Retrieves the blob identified by the provided container and object key,
        returning its content as raw bytes.

        Args:
            container (str):
                Name of the blob storage container.
            path (str):
                Object key (blob path) of the file to be read.

        Returns:
            bytes:
                Raw content of the requested blob.

        Raises:
            FileNotFoundError:
                If the blob does not exist in the specified container.
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

        Uploads the provided binary content to the specified container using the
        given object key. Existing blobs are overwritten.

        Args:
            container (str):
                Name of the destination blob container.
            path (str):
                Object key (blob path) where the file will be stored.
            data (bytes):
                Binary content to upload.

        Returns:
            str:
                Object key of the uploaded blob.
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

        Args:
            container (str):
                Name of the blob storage container.
            path (str):
                Object key (blob path) to verify.

        Returns:
            bool:
                True if the blob exists; otherwise False.
        """
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        return blob_client.exists()

    async def delete_file(self, container: str, path: str) -> bool:
        """
        Deletes a file from Azure Blob Storage.

        If the specified blob exists, it is permanently removed from the container.

        Args:
            container (str):
                Name of the blob storage container.
            path (str):
                Object key (blob path) of the file to delete.

        Returns:
            bool:
                True if the file was deleted successfully, or False if the blob
                does not exist.
        """
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        if not blob_client.exists():
            return False

        blob_client.delete_blob()
        return True
