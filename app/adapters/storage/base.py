from abc import ABC, abstractmethod


class StorageAdapter(ABC):
    """Abstract storage contract used by dataset workflows.

    Implementations provide async operations for reading, writing, checking,
    and deleting objects inside logical containers.
    """

    @abstractmethod
    async def read_file(self, container: str, path: str) -> bytes:
        pass

    @abstractmethod
    async def write_file(self, container: str, path: str, data: bytes) -> str:
        pass

    @abstractmethod
    async def file_exists(self, container: str, path: str) -> bool:
        pass

    @abstractmethod
    async def delete_file(self, container: str, path: str) -> bool:
        pass
