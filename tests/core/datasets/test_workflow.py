from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.datasets.models import DatasetMetadata
from app.core.datasets.workflow import DatasetWorkflow
from app.enums.dataset_status import DatasetStatus
from app.prepare.exceptions import NotFoundException


class FakeRepository:
    """Fake repository used by dataset retrieval workflow tests."""

    def __init__(self) -> None:
        self.dataset: DatasetMetadata | None = None
        self.datasets: list[DatasetMetadata] = []
        self.received_dataset_id: UUID | None = None
        self.list_metadata_called = False

    async def get_metadata_by_id(
        self,
        dataset_id: UUID,
    ) -> DatasetMetadata | None:
        """Return the configured dataset metadata."""
        self.received_dataset_id = dataset_id
        return self.dataset

    async def list_metadata(
        self,
    ) -> list[DatasetMetadata]:
        """Return the configured dataset metadata collection."""
        self.list_metadata_called = True
        return self.datasets


def make_dataset() -> DatasetMetadata:
    """Create dataset metadata used by retrieval workflow tests."""
    now = datetime.now(UTC)

    return DatasetMetadata(
        dataset_id=uuid4(),
        name="Customers",
        original_filename="customers.csv",
        content_type="text/csv",
        file_size_bytes=1024,
        status=DatasetStatus.COMPLETED.value,
        object_key="datasets/customers.csv",
        description="Dataset used in tests",
        rows_count=100,
        columns_count=5,
        profile=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_execute_returns_dataset_metadata():
    """Return dataset metadata when the requested dataset exists."""
    repository = FakeRepository()
    repository.dataset = make_dataset()

    workflow = DatasetWorkflow(
        dataset_repository=repository,
    )

    response = await workflow.execute(
        dataset_id=repository.dataset.dataset_id,
    )

    assert response.dataset_id == repository.dataset.dataset_id
    assert response.name == "Customers"
    assert response.original_filename == "customers.csv"
    assert response.content_type == "text/csv"
    assert response.file_size_bytes == 1024
    assert response.status == DatasetStatus.COMPLETED.value
    assert response.object_key == "datasets/customers.csv"
    assert response.description == "Dataset used in tests"
    assert response.rows_count == 100
    assert response.columns_count == 5
    assert response.profile is None
    assert repository.received_dataset_id == repository.dataset.dataset_id


@pytest.mark.asyncio
async def test_execute_raises_not_found_when_dataset_does_not_exist():
    """Raise not found when the repository cannot locate the dataset."""
    repository = FakeRepository()

    workflow = DatasetWorkflow(
        dataset_repository=repository,
    )

    dataset_id = uuid4()

    with pytest.raises(NotFoundException):
        await workflow.execute(
            dataset_id=dataset_id,
        )

    assert repository.received_dataset_id == dataset_id


@pytest.mark.asyncio
async def test_execute_accepts_status_as_plain_string():
    """Preserve the string status stored in the domain metadata."""
    repository = FakeRepository()
    dataset = make_dataset()
    repository.dataset = dataset

    workflow = DatasetWorkflow(
        dataset_repository=repository,
    )

    response = await workflow.execute(
        dataset_id=dataset.dataset_id,
    )

    assert response.status == "COMPLETED"


@pytest.mark.asyncio
async def test_list_datasets_returns_dataset_metadata():
    """Return all dataset metadata provided by the repository."""
    repository = FakeRepository()
    repository.datasets = [
        make_dataset(),
        make_dataset(),
    ]

    workflow = DatasetWorkflow(
        dataset_repository=repository,
    )

    response = await workflow.list_datasets()

    assert response == repository.datasets
    assert len(response) == 2
    assert repository.list_metadata_called is True


@pytest.mark.asyncio
async def test_list_datasets_returns_empty_list():
    """Return an empty collection when no active datasets exist."""
    repository = FakeRepository()

    workflow = DatasetWorkflow(
        dataset_repository=repository,
    )

    response = await workflow.list_datasets()

    assert response == []
    assert repository.list_metadata_called is True
