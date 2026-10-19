from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.datasets.deletion_workflow import DatasetDeletionResult
from app.core.datasets.models import DatasetMetadata, DatasetProfileSummary
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
        *,
        user_id: int,
    ) -> DatasetMetadata:
        """Return domain dataset metadata or raise the configured error."""
        self.received_dataset_id = dataset_id
        self.received_user_id = user_id

        if self.error is not None:
            raise self.error

        now = datetime.now(UTC)

        return DatasetMetadata(
            user_id=17,
            dataset_id=dataset_id,
            name="Customers",
            original_filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1024,
            status=DatasetStatus.COMPLETED.value,
            object_key="datasets/customers.csv",
            description="Dataset for tests",
            rows_count=100,
            columns_count=5,
            profile=None,
            created_at=now,
            updated_at=now,
        )


class FakeListWorkflow:
    """Fake listing workflow used by dataset service tests."""

    def __init__(self, datasets=None) -> None:
        self.datasets: list[DatasetMetadata] = datasets if datasets is not None else []
        self.received_user_id = None
        self.execute_called = False

    async def execute(self, *, user_id: int) -> list[DatasetMetadata]:
        """Return the configured dataset metadata collection."""
        self.execute_called = True
        self.received_user_id = user_id
        return self.datasets


class FakeDeletionWorkflow:
    """Fake deletion workflow used by dataset service tests."""

    def __init__(self) -> None:
        self.error: Exception | None = None
        self.received_dataset_id: UUID | None = None
        self.already_deleted = False

    async def execute(
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
            description="Dataset for tests",
            rows_count=100,
            columns_count=5,
            profile=None,
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
    list_workflow = FakeListWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    service = DatasetService(
        workflow=workflow,
        list_workflow=list_workflow,
        deletion_workflow=deletion_workflow,
    )

    dataset_id = uuid4()

    response = await service.get_dataset(
        dataset_id=dataset_id,
        user_id=17,
    )

    assert isinstance(
        response,
        DatasetResponseDataDTO,
    )

    assert response.dataset_id == dataset_id
    assert workflow.received_dataset_id == dataset_id
    assert workflow.received_user_id == 17
    assert response.name == "Customers"
    assert response.original_filename == "customers.csv"
    assert response.status == DatasetStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_get_dataset_propagates_not_found_exception():
    """Propagate retrieval errors raised by the dataset workflow."""
    workflow = FakeWorkflow()
    list_workflow = FakeListWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    workflow.error = NotFoundException("Dataset not found.")

    service = DatasetService(
        workflow=workflow,
        list_workflow=list_workflow,
        deletion_workflow=deletion_workflow,
    )

    with pytest.raises(NotFoundException):
        await service.get_dataset(
            dataset_id=uuid4(),
            user_id=17,
        )


@pytest.mark.asyncio
async def test_list_datasets_returns_response_data():
    """Convert listed domain metadata into dataset response data."""
    workflow = FakeWorkflow()
    list_workflow = FakeListWorkflow()
    deletion_workflow = FakeDeletionWorkflow()
    now = datetime.now(UTC)

    list_workflow.datasets = [
        DatasetMetadata(
            user_id=17,
            dataset_id=uuid4(),
            name="Customers",
            original_filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1024,
            status=DatasetStatus.PROFILED.value,
            object_key="datasets/customers.csv",
            description="Dataset for tests",
            rows_count=100,
            columns_count=5,
            profile=DatasetProfileSummary(
                total_nulls=0,
                columns_with_nulls=0,
                numeric_columns=2,
                datetime_columns=1,
                text_columns=2,
                quality_warnings=(
                    "Dataset warning.",
                ),
            ),
            created_at=now,
            updated_at=now,
        ),
    ]

    service = DatasetService(
        workflow=workflow,
        list_workflow=list_workflow,
        deletion_workflow=deletion_workflow,
    )

    response = await service.list_datasets(user_id=37)

    assert list_workflow.execute_called is True
    assert list_workflow.received_user_id == 37
    assert len(response) == 1

    dataset = response[0]

    assert isinstance(
        dataset,
        DatasetResponseDataDTO,
    )
    assert dataset.dataset_id == list_workflow.datasets[0].dataset_id
    assert dataset.name == "Customers"
    assert dataset.rows_count == 100
    assert dataset.columns_count == 5
    assert dataset.total_nulls == 0
    assert dataset.columns_with_nulls == 0
    assert dataset.numeric_columns == 2
    assert dataset.datetime_columns == 1
    assert dataset.text_columns == 2
    assert dataset.quality_warnings == [
        "Dataset warning.",
    ]


@pytest.mark.asyncio
async def test_list_datasets_preserves_unavailable_profile():
    """Keep profiling fields unavailable when no profile exists."""
    workflow = FakeWorkflow()
    list_workflow = FakeListWorkflow()
    deletion_workflow = FakeDeletionWorkflow()
    now = datetime.now(UTC)

    list_workflow.datasets = [
        DatasetMetadata(
            user_id=17,
            dataset_id=uuid4(),
            name="Customers",
            original_filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1024,
            status=DatasetStatus.COMPLETED.value,
            object_key="datasets/customers.csv",
            description="Dataset for tests",
            rows_count=100,
            columns_count=5,
            profile=None,
            created_at=now,
            updated_at=now,
        ),
    ]

    service = DatasetService(
        workflow=workflow,
        list_workflow=list_workflow,
        deletion_workflow=deletion_workflow,
    )

    response = await service.list_datasets(user_id=37)

    assert len(response) == 1

    dataset = response[0]

    assert dataset.total_nulls is None
    assert dataset.columns_with_nulls is None
    assert dataset.numeric_columns is None
    assert dataset.datetime_columns is None
    assert dataset.text_columns is None
    assert dataset.quality_warnings is None


@pytest.mark.asyncio
async def test_list_datasets_returns_empty_list():
    """Return an empty collection when the workflow has no datasets."""
    workflow = FakeWorkflow()
    list_workflow = FakeListWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    service = DatasetService(
        workflow=workflow,
        list_workflow=list_workflow,
        deletion_workflow=deletion_workflow,
    )

    response = await service.list_datasets(user_id=37)

    assert list_workflow.execute_called is True
    assert list_workflow.received_user_id == 37
    assert response == []


@pytest.mark.asyncio
async def test_delete_dataset_returns_deletion_result():
    """Return the result produced by the dataset deletion workflow."""
    workflow = FakeWorkflow()
    list_workflow = FakeListWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    service = DatasetService(
        workflow=workflow,
        list_workflow=list_workflow,
        deletion_workflow=deletion_workflow,
    )

    dataset_id = uuid4()

    result = await service.delete_dataset(
        dataset_id=dataset_id,
        user_id=17,
    )

    assert deletion_workflow.received_dataset_id == dataset_id
    assert deletion_workflow.received_user_id == 17
    assert result.dataset.dataset_id == dataset_id
    assert result.dataset.status == DatasetStatus.DELETED.value
    assert result.already_deleted is False


@pytest.mark.asyncio
async def test_delete_dataset_returns_already_deleted_result():
    """Preserve the already-deleted state returned by the workflow."""
    workflow = FakeWorkflow()
    list_workflow = FakeListWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    deletion_workflow.already_deleted = True

    service = DatasetService(
        workflow=workflow,
        list_workflow=list_workflow,
        deletion_workflow=deletion_workflow,
    )

    result = await service.delete_dataset(
        dataset_id=uuid4(),
        user_id=17,
    )

    assert result.already_deleted is True
    assert result.dataset.status == DatasetStatus.DELETED.value


@pytest.mark.asyncio
async def test_delete_dataset_propagates_not_found_exception():
    """Propagate deletion errors raised by the deletion workflow."""
    workflow = FakeWorkflow()
    list_workflow = FakeListWorkflow()
    deletion_workflow = FakeDeletionWorkflow()

    deletion_workflow.error = NotFoundException("Dataset not found.")

    service = DatasetService(
        workflow=workflow,
        list_workflow=list_workflow,
        deletion_workflow=deletion_workflow,
    )

    with pytest.raises(NotFoundException):
        await service.delete_dataset(
            dataset_id=uuid4(),
            user_id=17,
        )


@pytest.mark.parametrize("empty", [False, True])
async def test_list_datasets_forwards_identity_and_maps_all_metadata(empty):
    from dataclasses import asdict

    metadata = await FakeWorkflow().execute(dataset_id=uuid4(), user_id=17)
    listing = FakeListWorkflow([] if empty else [metadata])
    service = DatasetService(
        workflow=FakeWorkflow(), list_workflow=listing,
        deletion_workflow=FakeDeletionWorkflow(),
    )
    result = await service.list_datasets(user_id=37)
    assert listing.received_user_id == 37
    expected = [] if empty else [DatasetResponseDataDTO(**asdict(metadata)).model_dump()]
    assert [item.model_dump() for item in result] == expected
