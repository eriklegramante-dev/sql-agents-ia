from pathlib import Path

from app.adapters.storage.base import StorageAdapter


class LocalStorageAdapter(StorageAdapter):
    """
    Adapter responsible for providing a local filesystem implementation of the
    storage contract.

    This class implements the StorageAdapter interface using the local file
    system instead of a cloud storage provider. It maps logical storage
    containers to directories under a configurable base path, allowing the
    application to perform file operations during local development, testing,
    and environments where Azure Blob Storage is not required.

    Attributes:
        base_path (Path):
            Root directory where logical storage containers are created and
            managed.
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, container: str, path: str) -> Path:
        return self.base_path / container / path


    async def read_file(self, container: str, path: str) -> bytes:
        """
        Reads a file from the local filesystem.

        Resolves the file location based on the configured base path and the
        provided logical container before returning its binary content.

        Args:
            container (str):
                Logical storage container mapped to a local directory.
            path (str):
                Relative path of the file inside the container.

        Returns:
            bytes:
                Raw content of the requested file.

        Raises:
            FileNotFoundError:
                If the requested file does not exist.
        """
        full_path = self._get_full_path(container, path)

        if not full_path.exists():
            raise FileNotFoundError(
                f"File {path} not found in container {container}"
            )

        return full_path.read_bytes()


    async def write_file(self, container: str, path: str, data: bytes) -> str:
        """
        Writes a file to the local filesystem.

        Creates the destination directory structure when necessary and writes the
        provided binary content to the resolved file path.

        Args:
            container (str):
                Logical storage container mapped to a local directory.
            path (str):
                Relative path where the file will be stored.
            data (bytes):
                Binary content to be written.

        Returns:
            str:
                Relative object key of the stored file.
        """
        full_path = self._get_full_path(container, path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)

        return path


    async def file_exists(self, container: str, path: str) -> bool:
        """
        Checks whether a file exists in the local filesystem.

        Args:
            container (str):
                Logical storage container mapped to a local directory.
            path (str):
                Relative path of the file to verify.

        Returns:
            bool:
                True if the file exists, otherwise False.
        """
        return self._get_full_path(container, path).exists()


    async def delete_file(self, container: str, path: str) -> bool:
        """
        Deletes a file from the local filesystem.

        Args:
            container (str):
                Logical storage container mapped to a local directory.
            path (str):
                Relative path of the file to delete.

        Returns:
            bool:
                True if the file was deleted successfully, or False if the file
                does not exist.
        """
        full_path = self._get_full_path(container, path)

        if not full_path.exists():
            return False

        full_path.unlink()
        return True