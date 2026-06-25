from azure.storage.blob import BlobServiceClient

from app.adapters.storage.base import StorageAdapter


class BlobStorageAdapter(StorageAdapter):
    """Azure Blob Storage implementation of the storage contract.

    Uses a connection string to access blob containers and read or write dataset
    files by object key.
    """

    def __init__(self, connection_string: str | None):
        if not connection_string:
            raise ValueError("Azure storage connection string is required")

        self.client = BlobServiceClient.from_connection_string(connection_string)

    async def read_file(self, container: str, path: str) -> bytes:
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        if not blob_client.exists():
            raise FileNotFoundError(f"File {path} not found in container {container}")

        stream = blob_client.download_blob()
        return stream.readall()

    async def write_file(self, container: str, path: str, data: bytes) -> str:
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        blob_client.upload_blob(data, overwrite=True)

        return path

    async def file_exists(self, container: str, path: str) -> bool:
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        return blob_client.exists()

    async def delete_file(self, container: str, path: str) -> bool:
        blob_client = self.client.get_blob_client(
            container=container,
            blob=path,
        )

        if not blob_client.exists():
            return False

        blob_client.delete_blob()
        return True
