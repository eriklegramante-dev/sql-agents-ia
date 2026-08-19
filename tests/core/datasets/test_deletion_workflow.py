from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.adapters.storage.exceptions import StorageOperationError
from app.core.datasets.deletion_workflow import DatasetDeletionWorkflow
from app.core.datasets.exceptions import (
    DatasetRelatedRecordsDeletionException,
)
from app.core.datasets.models import DatasetMetadata
from app.enums.dataset_status import DatasetStatus
from app.prepare.exceptions import NotFoundException


class FakeLogger:
    """Fake logger used by dataset deletion workflow tests."""

    def log_info(self, message: str) -> None:
        """Accept informational log messages."""

    def log_error(self, message: str) -> None:
        """Accept error log messages."""


class FakeRepository:
    """Fake dataset repository used by deletion workflow tests."""

    def __init__(self) -> None:
        self.dataset: DatasetMetadata | None = None
        self.related_records_deleted = False
        self.related_records_error: Exception | None = None
        self.status_updates: list[tuple[UUID, DatasetStatus, str | None]] = []
        self.update_status_result = True
        self.return_none_after_deleted_status = False

    async def get_metadata_by_id(
        self,
        dataset_id: UUID,
    ) -> DatasetMetadata | None:
        """Return configured metadata for the requested dataset."""
        if (
            self.return_none_after_deleted_status
            and self.status_updates
            and self.status_updates[-1][1] == DatasetStatus.DELETED
        ):
            return None

        return self.dataset

    async def delete_related_records(
        self,
        dataset_id: UUID,
    ) -> None:
        """Simulate related-record cleanup."""
        if self.related_records_error is not None:
            raise self.related_records_error

        self.related_records_deleted = True

    async def update_status(
        self,
        dataset_id: UUID,
        status: DatasetStatus,
        error_message: str | None = None,
    ) -> bool:
        """Register and apply a dataset status update."""
        self.status_updates.append(
            (
                dataset_id,
                status,
                error_message,
            )
        )

        if self.dataset is not None and self.update_status_result:
            self.dataset = DatasetMetadata(
                dataset_id=self.dataset.dataset_id,
                name=self.dataset.name,
                original_filename=self.dataset.original_filename,
                content_type=self.dataset.content_type,
                file_size_bytes=self.dataset.file_size_bytes,
                status=status.value,
                object_key=self.dataset.object_key,
                description=self.dataset.description,
                created_at=self.dataset.created_at,
                updated_at=datetime.now(UTC),
            )

        return self.update_status_result


class FakeStorage:
    """Fake storage adapter used by deletion workflow tests."""

    def __init__(self) -> None:
        self.deleted = True
        self.error: Exception | None = None
        self.received_container: str | None = None
        self.received_path: str | None = None

    async def delete_file(
        self,
        container: str,
        path: str,
    ) -> bool:
        """Simulate deletion of a dataset storage object."""
        self.received_container = container
        self.received_path = path

        if self.error is not None:
            raise self.error

        return self.deleted


def make_dataset(
    status: DatasetStatus = DatasetStatus.COMPLETED,
) -> DatasetMetadata:
    """Create dataset metadata for deletion workflow scenarios."""
    now = datetime.now(UTC)

    return DatasetMetadata(
        dataset_id=uuid4(),
        name="Customers",
        original_filename="customers.csv",
        content_type="text/csv",
        file_size_bytes=1024,
        status=status.value,
        object_key="datasets/customers.csv",
        description="Dataset used in deletion tests",
        created_at=now,
        updated_at=now,
    )


def build_workflow(
    repository: FakeRepository,
    storage: FakeStorage,
) -> DatasetDeletionWorkflow:
    """Build the deletion workflow with explicit fake dependencies."""
    return DatasetDeletionWorkflow(
        dataset_repository=repository,
        storage=storage,
        raw_container="sql-agents-raw",
        logger=FakeLogger(),
    )


@pytest.mark.asyncio
async def test_delete_dataset_successfully():
    repository = FakeRepository()
    storage = FakeStorage()

    repository.dataset = make_dataset()

    workflow = build_workflow(
        repository=repository,
        storage=storage,
    )

    result = await workflow.execute(
        dataset_id=repository.dataset.dataset_id,
    )

    assert result.already_deleted is False
    assert result.dataset.status == DatasetStatus.DELETED.value
    assert storage.received_container == "sql-agents-raw"
    assert storage.received_path == "datasets/customers.csv"
    assert repository.related_records_deleted is True
    assert repository.status_updates[-1][1] == DatasetStatus.DELETED


@pytest.mark.asyncio
async def test_delete_raises_not_found_when_dataset_does_not_exist():
    repository = FakeRepository()
    storage = FakeStorage()

    workflow = build_workflow(repository, storage)

    with pytest.raises(NotFoundException):
        await workflow.execute(
            dataset_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_delete_returns_already_deleted_result():
    repository = FakeRepository()
    storage = FakeStorage()

    repository.dataset = make_dataset(
        status=DatasetStatus.DELETED,
    )

    workflow = build_workflow(repository, storage)

    result = await workflow.execute(
        dataset_id=repository.dataset.dataset_id,
    )

    assert result.already_deleted is True
    assert result.dataset.status == DatasetStatus.DELETED.value
    assert storage.received_path is None
    assert repository.related_records_deleted is False
    assert repository.status_updates == []


@pytest.mark.asyncio
async def test_delete_continues_when_storage_object_is_absent():
    repository = FakeRepository()
    storage = FakeStorage()

    repository.dataset = make_dataset()
    storage.deleted = False

    workflow = build_workflow(repository, storage)

    result = await workflow.execute(
        dataset_id=repository.dataset.dataset_id,
    )

    assert result.dataset.status == DatasetStatus.DELETED.value
    assert repository.related_records_deleted is True
    assert repository.status_updates[-1][1] == DatasetStatus.DELETED


@pytest.mark.asyncio
async def test_delete_marks_dataset_failed_when_storage_cleanup_fails():
    repository = FakeRepository()
    storage = FakeStorage()

    repository.dataset = make_dataset()
    storage.error = StorageOperationError(
        operation="delete object",
    )

    workflow = build_workflow(repository, storage)

    with pytest.raises(StorageOperationError):
        await workflow.execute(
            dataset_id=repository.dataset.dataset_id,
        )

    assert repository.related_records_deleted is False
    assert repository.status_updates[-1][1] == DatasetStatus.FAILED
    assert repository.status_updates[-1][2] is not None


@pytest.mark.asyncio
async def test_delete_stops_when_related_record_cleanup_fails():
    """Do not mark the dataset deleted after persistence cleanup failure."""
    repository = FakeRepository()
    storage = FakeStorage()

    repository.dataset = make_dataset()
    repository.related_records_error = DatasetRelatedRecordsDeletionException(
        dataset_id=repository.dataset.dataset_id,
    )

    workflow = build_workflow(repository, storage)

    with pytest.raises(DatasetRelatedRecordsDeletionException):
        await workflow.execute(
            dataset_id=repository.dataset.dataset_id,
        )

    assert repository.related_records_deleted is False
    assert repository.status_updates == []


@pytest.mark.asyncio
async def test_delete_raises_when_deleted_status_cannot_be_persisted():
    repository = FakeRepository()
    storage = FakeStorage()

    repository.dataset = make_dataset()
    repository.update_status_result = False

    workflow = build_workflow(repository, storage)

    with pytest.raises(NotFoundException):
        await workflow.execute(
            dataset_id=repository.dataset.dataset_id,
        )

    assert repository.related_records_deleted is True
    assert repository.status_updates[-1][1] == DatasetStatus.DELETED


@pytest.mark.asyncio
async def test_delete_raises_when_dataset_disappears_after_status_update():
    repository = FakeRepository()
    storage = FakeStorage()

    repository.dataset = make_dataset()
    repository.return_none_after_deleted_status = True

    dataset_id = repository.dataset.dataset_id

    workflow = build_workflow(repository, storage)

    with pytest.raises(NotFoundException):
        await workflow.execute(
            dataset_id=dataset_id,
        )

    assert repository.related_records_deleted is True
    assert repository.status_updates[-1][1] == DatasetStatus.DELETED
