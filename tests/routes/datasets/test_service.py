from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.datasets.deletion_workflow import DatasetDeletionResult
from app.core.datasets.models import DatasetMetadata
from app.enums.dataset_status import DatasetStatus
from app.prepare.exceptions import NotFoundException
from app.routes.datasets.dtos.dto import DatasetResponseDataDTO
from app.routes.datasets.services.service import DatasetService


class FakeWorkflow:
    """Fake retrieval workflow that mirrors the core workflow contract."""

    def __init__(self) -> None:
        self.error: Exception | None = None
        self.received_dataset_id: UUID | None = None

    async def execute(
        self,
        dataset_id: UUID,
    ) -> DatasetMetadata:
        """Return domain dataset metadata or raise the configured error."""
        self.received_dataset_id = dataset_id

        if self.error is not None:
            raise self.error

        now = datetime.now(UTC)

        return DatasetMetadata(
            dataset_id=dataset_id,
            name="Customers",
            original_filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1024,
            status=DatasetStatus.COMPLETED.value,
            object_key="datasets/customers.csv",
            description="Dataset for tests",
            created_at=now,
            updated_at=now,
        )


class FakeDeletionWorkflow:
    """Fake deletion workflow used by dataset service tests."""

    def __init__(self) -> None:
        self.error: Exception | None = None
        self.received_dataset_id: UUID | None = None
        self.already_deleted = False

    async def execute(
        self,
        dataset_id: UUID,
    ) -> DatasetDeletionResult:
        """Return a simulated dataset deletion result."""
        self.received_dataset_id = dataset_id

        if self.error is not None:
            raise self.error

        now = datetime.now(UTC)

        dataset = DatasetMetadata(
            dataset_id=dataset_id,
            name="Customers",
            original_filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1024,
            status=DatasetStatus.DELETED.value,
            object_key="datasets/customers.csv",
            description="Dataset for tests",
            created_at=now,
            updated_at=now,
        )

        return DatasetDeletionResult(
            dataset=dataset,
            already_deleted=self.already_deleted,
        )


@pytest.mark.asyncio
async def test_get_dataset_returns_response_data():
    """Convert workflow domain metadata into dataset response data."""
    workflow = FakeWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    service = DatasetService(
        workflow=workflow,
        deletion_workflow=deletion_workflow,
    )

    dataset_id = uuid4()

    response = await service.get_dataset(
        dataset_id=dataset_id,
    )

    assert isinstance(
        response,
        DatasetResponseDataDTO,
    )

    assert response.dataset_id == dataset_id
    assert workflow.received_dataset_id == dataset_id
    assert response.name == "Customers"
    assert response.original_filename == "customers.csv"
    assert response.status == DatasetStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_get_dataset_propagates_not_found_exception():
    """Propagate retrieval errors raised by the dataset workflow."""
    workflow = FakeWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    workflow.error = NotFoundException("Dataset not found.")

    service = DatasetService(
        workflow=workflow,
        deletion_workflow=deletion_workflow,
    )

    with pytest.raises(NotFoundException):
        await service.get_dataset(
            dataset_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_delete_dataset_returns_deletion_result():
    """Return the result produced by the dataset deletion workflow."""
    workflow = FakeWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    service = DatasetService(
        workflow=workflow,
        deletion_workflow=deletion_workflow,
    )

    dataset_id = uuid4()

    result = await service.delete_dataset(
        dataset_id=dataset_id,
    )

    assert deletion_workflow.received_dataset_id == dataset_id
    assert result.dataset.dataset_id == dataset_id
    assert result.dataset.status == DatasetStatus.DELETED.value
    assert result.already_deleted is False


@pytest.mark.asyncio
async def test_delete_dataset_returns_already_deleted_result():
    """Preserve the already-deleted state returned by the workflow."""
    workflow = FakeWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    deletion_workflow.already_deleted = True

    service = DatasetService(
        workflow=workflow,
        deletion_workflow=deletion_workflow,
    )

    result = await service.delete_dataset(
        dataset_id=uuid4(),
    )

    assert result.already_deleted is True
    assert result.dataset.status == DatasetStatus.DELETED.value


@pytest.mark.asyncio
async def test_delete_dataset_propagates_not_found_exception():
    """Propagate deletion errors raised by the deletion workflow."""
    workflow = FakeWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    deletion_workflow.error = NotFoundException("Dataset not found.")

    service = DatasetService(
        workflow=workflow,
        deletion_workflow=deletion_workflow,
    )

    with pytest.raises(NotFoundException):
        await service.delete_dataset(
            dataset_id=uuid4(),
        )
