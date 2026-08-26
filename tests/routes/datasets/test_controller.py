from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.datasets.deletion_workflow import DatasetDeletionResult
from app.core.datasets.models import DatasetMetadata
from app.enums.dataset_status import DatasetStatus
from app.prepare.exceptions import NotFoundException
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.dtos.dto import DatasetResponseDataDTO


class FakeDatasetService:
    """Fake dataset service used by controller tests."""

    def __init__(self) -> None:
        self.error: Exception | None = None
        self.received_dataset_id: UUID | None = None
        self.already_deleted = False

    async def get_dataset(
        self,
        dataset_id: UUID,
    ) -> DatasetResponseDataDTO:
        """Return dataset metadata or raise the configured error."""
        self.received_dataset_id = dataset_id

        if self.error is not None:
            raise self.error

        now = datetime.now(UTC)

        return DatasetResponseDataDTO(
            dataset_id=dataset_id,
            name="Customers",
            original_filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1024,
            status=DatasetStatus.COMPLETED.value,
            object_key="datasets/customers.csv",
            description="Dataset used in tests",
            created_at=now,
            updated_at=now,
        )

    async def delete_dataset(
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
            description="Dataset used in tests",
            created_at=now,
            updated_at=now,
        )

        return DatasetDeletionResult(
            dataset=dataset,
            already_deleted=self.already_deleted,
        )


@pytest.mark.asyncio
async def test_get_dataset_returns_success_response():
    """Return a standardized response for successful dataset retrieval."""
    service = FakeDatasetService()

    controller = DatasetController(
        service=service,
    )

    dataset_id = uuid4()

    response = await controller.get_dataset(
        dataset_id=dataset_id,
    )

    assert response.success is True
    assert response.message == "Dataset retrieved successfully."
    assert response.data is not None
    assert response.data.dataset_id == dataset_id
    assert service.received_dataset_id == dataset_id


@pytest.mark.asyncio
async def test_get_dataset_propagates_not_found_exception():
    """Propagate retrieval errors raised by the dataset service."""
    service = FakeDatasetService()

    service.error = NotFoundException("Dataset not found.")

    controller = DatasetController(
        service=service,
    )

    with pytest.raises(NotFoundException) as exc:
        await controller.get_dataset(
            dataset_id=uuid4(),
        )

    assert str(exc.value) == "Dataset not found."


@pytest.mark.asyncio
async def test_delete_dataset_returns_success_response():
    """Return deletion metadata after a successful dataset deletion."""
    service = FakeDatasetService()

    controller = DatasetController(
        service=service,
    )

    dataset_id = uuid4()

    response = await controller.delete_dataset(
        dataset_id=dataset_id,
    )

    assert response.success is True
    assert response.message == "Dataset deleted successfully."
    assert response.data is not None
    assert response.data.dataset_id == dataset_id
    assert response.data.status == DatasetStatus.DELETED.value
    assert service.received_dataset_id == dataset_id


@pytest.mark.asyncio
async def test_delete_dataset_returns_already_deleted_message():
    """Return an idempotent response when the dataset was already deleted."""
    service = FakeDatasetService()
    service.already_deleted = True

    controller = DatasetController(
        service=service,
    )

    response = await controller.delete_dataset(
        dataset_id=uuid4(),
    )

    assert response.success is True
    assert response.message == "Dataset was already deleted."
    assert response.data is not None
    assert response.data.status == DatasetStatus.DELETED.value


@pytest.mark.asyncio
async def test_delete_dataset_propagates_not_found_exception():
    """Propagate deletion errors raised by the dataset service."""
    service = FakeDatasetService()

    service.error = NotFoundException("Dataset not found.")

    controller = DatasetController(
        service=service,
    )

    with pytest.raises(NotFoundException):
        await controller.delete_dataset(
            dataset_id=uuid4(),
        )
