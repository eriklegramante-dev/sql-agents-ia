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
        self.datasets: list[DatasetResponseDataDTO] = []
        self.list_datasets_called = False
        self.received_user_id = None

    async def get_dataset(
        self,
        dataset_id: UUID,
        *,
        user_id: int,
    ) -> DatasetResponseDataDTO:
        """Return dataset metadata or raise the configured error."""
        self.received_dataset_id = dataset_id
        self.received_user_id = user_id

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
            rows_count=12,
            columns_count=3,
            created_at=now,
            updated_at=now,
        )

    async def list_datasets(
        self,
        *,
        user_id: int,
    ) -> list[DatasetResponseDataDTO]:
        """Return configured dataset metadata for listing tests."""
        self.list_datasets_called = True
        self.received_user_id = user_id

        if self.error is not None:
            raise self.error

        return self.datasets

    async def delete_dataset(
        self,
        dataset_id: UUID,
        *,
        user_id: int,
    ) -> DatasetDeletionResult:
        """Return a simulated dataset deletion result."""
        self.received_dataset_id = dataset_id
        self.received_user_id = user_id

        if self.error is not None:
            raise self.error

        now = datetime.now(UTC)

        dataset = DatasetMetadata(
            user_id=17,
            dataset_id=dataset_id,
            name="Customers",
            original_filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1024,
            status=DatasetStatus.DELETED.value,
            object_key="datasets/customers.csv",
            description="Dataset used in tests",
            rows_count=12,
            columns_count=3,
            profile=None,
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
        user_id=17,
    )

    assert response.success is True
    assert response.message == "Dataset retrieved successfully."
    assert response.data is not None
    assert response.data.dataset_id == dataset_id
    assert service.received_dataset_id == dataset_id
    assert service.received_user_id == 17


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
            user_id=17,
        )

    assert str(exc.value) == "Dataset not found."


@pytest.mark.asyncio
async def test_list_datasets_returns_success_response():
    """Return a standardized response for successful dataset listing."""
    service = FakeDatasetService()
    now = datetime.now(UTC)
    dataset_id = uuid4()

    service.datasets = [
        DatasetResponseDataDTO(
            dataset_id=dataset_id,
            name="Customers",
            original_filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1024,
            status=DatasetStatus.PROFILED.value,
            object_key="datasets/customers.csv",
            description="Dataset used in tests",
            rows_count=100,
            columns_count=5,
            total_nulls=0,
            columns_with_nulls=0,
            numeric_columns=2,
            datetime_columns=1,
            text_columns=2,
            quality_warnings=[
                "Dataset warning.",
            ],
            created_at=now,
            updated_at=now,
        ),
    ]

    controller = DatasetController(
        service=service,
    )

    response = await controller.list_datasets(user_id=37)

    assert response.success is True
    assert response.message == "Datasets retrieved successfully."
    assert len(response.data) == 1
    assert response.data[0].dataset_id == dataset_id
    assert response.data[0].total_nulls == 0
    assert response.data[0].numeric_columns == 2
    assert response.data[0].datetime_columns == 1
    assert response.data[0].text_columns == 2
    assert response.data[0].quality_warnings == [
        "Dataset warning.",
    ]
    assert service.list_datasets_called is True
    assert service.received_user_id == 37


@pytest.mark.asyncio
async def test_list_datasets_returns_empty_success_response():
    """Return a successful response when no active datasets exist."""
    service = FakeDatasetService()

    controller = DatasetController(
        service=service,
    )

    response = await controller.list_datasets(user_id=37)

    assert response.success is True
    assert response.message == "Datasets retrieved successfully."
    assert response.data == []
    assert service.list_datasets_called is True
    assert service.received_user_id == 37


@pytest.mark.asyncio
async def test_list_datasets_propagates_service_exception():
    """Propagate listing errors raised by the dataset service."""
    service = FakeDatasetService()
    service.error = NotFoundException("Dataset listing failed.")

    controller = DatasetController(
        service=service,
    )

    with pytest.raises(NotFoundException) as exc:
        await controller.list_datasets(user_id=37)

    assert str(exc.value) == "Dataset listing failed."
    assert service.list_datasets_called is True
    assert service.received_user_id == 37


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
        user_id=17,
    )

    assert response.success is True
    assert response.message == "Dataset deleted successfully."
    assert response.data is not None
    assert response.data.dataset_id == dataset_id
    assert response.data.status == DatasetStatus.DELETED.value
    assert service.received_dataset_id == dataset_id
    assert service.received_user_id == 17


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
        user_id=17,
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
            user_id=17,
        )


@pytest.mark.parametrize("empty", [False, True])
async def test_list_datasets_forwards_identity_and_returns_success(empty):
    from unittest.mock import AsyncMock

    service = FakeDatasetService()
    metadata = await service.get_dataset(dataset_id=uuid4(), user_id=17)
    data = [] if empty else [metadata]
    service.list_datasets = AsyncMock(return_value=data)
    response = await DatasetController(service=service).list_datasets(user_id=37)
    service.list_datasets.assert_awaited_once_with(user_id=37)
    assert response.success is True
    assert response.message == "Datasets retrieved successfully."
    assert response.data == data
    assert response.errors is None
