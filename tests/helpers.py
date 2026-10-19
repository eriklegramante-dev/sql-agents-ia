from datetime import datetime
from uuid import UUID

from app.enums.dataset_status import DatasetStatus
from app.models.dataset_table import DatasetTable

DATASET_ID = UUID("11111111-1111-1111-1111-111111111111")
NOW = datetime(2026, 6, 23, 12, 0, 0)


def make_dataset(
    *,
    user_id: int | None = 17,
    status: DatasetStatus = DatasetStatus.COMPLETED,
    raw_object_key: str = "uploads/input.csv",
    prepared_object_key: str | None = None,
    rows_count: int | None = None,
    columns_count: int | None = None,
) -> DatasetTable:
    return DatasetTable(
        id=DATASET_ID,
        user_id=user_id,
        name="dataset.csv",
        status=status,
        raw_object_key=raw_object_key,
        prepared_object_key=prepared_object_key,
        rows_count=rows_count,
        columns_count=columns_count,
        error_message=None,
        created_at=NOW,
        updated_at=NOW,
    )


class FakeDatasetRepository:
    def __init__(self, dataset: DatasetTable | None):
        self.dataset = dataset
        self.status_updates: list[tuple[UUID, DatasetStatus, str | None]] = []
        self.saved_schema = None
        self.prepared_info = None

    async def get_by_id(self, dataset_id: UUID):
        return self.dataset

    async def update_status(
        self,
        dataset_id: UUID,
        status: DatasetStatus,
        error_message: str | None = None,
    ) -> bool:
        self.status_updates.append((dataset_id, status, error_message))
        return True

    async def save_schema(self, dataset_id: UUID, schema_data):
        self.saved_schema = (dataset_id, schema_data)
        return True

    async def update_prepared_info(
        self,
        dataset_id: UUID,
        prepared_object_key: str,
        rows_count: int,
        columns_count: int,
    ):
        self.prepared_info = (
            dataset_id,
            prepared_object_key,
            rows_count,
            columns_count,
        )
        return make_dataset(
            status=DatasetStatus.PREPARED,
            prepared_object_key=prepared_object_key,
            rows_count=rows_count,
            columns_count=columns_count,
        )


class FakeStorage:
    def __init__(self, files: dict[tuple[str, str], bytes] | None = None):
        self.files = files or {}
        self.writes: list[tuple[str, str, bytes]] = []

    async def read_file(self, container: str, path: str) -> bytes:
        key = (container, path)
        if key not in self.files:
            raise FileNotFoundError(f"{container}/{path} not found")
        return self.files[key]

    async def write_file(self, container: str, path: str, data: bytes) -> str:
        self.writes.append((container, path, data))
        return path

    async def file_exists(self, container: str, path: str) -> bool:
        return (container, path) in self.files

    async def delete_file(self, container: str, path: str) -> bool:
        self.files.pop((container, path), None)
        return True


class FixedDatetime:
    @staticmethod
    def utcnow() -> datetime:
        return datetime(2026, 6, 23, 15, 30, 45)
