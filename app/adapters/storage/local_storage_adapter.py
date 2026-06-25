from pathlib import Path

from app.adapters.storage.base import StorageAdapter


class LocalStorageAdapter(StorageAdapter):
    """Filesystem implementation of the storage contract.

    Maps each logical container to a directory under the configured base path,
    making local development and tests use the same adapter interface.
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, container: str, path: str) -> Path:
        container_path = self.base_path / container
        return container_path / path

    async def read_file(self, container: str, path: str) -> bytes:
        full_path = self._get_full_path(container, path)

        if not full_path.exists():
            raise FileNotFoundError(f"File {path} not found in container {container}")

        return full_path.read_bytes()

    async def write_file(self, container: str, path: str, data: bytes) -> str:
        full_path = self._get_full_path(container, path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)

        return path

    async def file_exists(self, container: str, path: str) -> bool:
        return self._get_full_path(container, path).exists()

    async def delete_file(self, container: str, path: str) -> bool:
        full_path = self._get_full_path(container, path)

        if not full_path.exists():
            return False

        full_path.unlink()
        return True
