from uuid import uuid4

import pytest

from app.prepare.exceptions import NotFoundException
from app.routes.datasets.dtos.dto import DatasetResponseDataDTO
from app.routes.datasets.services.service import DatasetService

from datetime import datetime


class FakeWorkflow:
    def __init__(self):
        self.error = None
        self.received_dataset_id = None

    async def execute(self, dataset_id):
        self.received_dataset_id = dataset_id

        if self.error:
            raise self.error

        now = datetime.now()

        return DatasetResponseDataDTO(
            dataset_id=dataset_id,
            name="Customers",
            original_filename="customers.csv",
            content_type="text/csv",
            file_size_bytes=1024,
            status="COMPLETED",
            object_key="datasets/customers.csv",
            description="Dataset for tests",
            created_at=now,
            updated_at=now,
        )


@pytest.mark.asyncio
async def test_get_dataset_returns_dataset_metadata():

    workflow = FakeWorkflow()

    service = DatasetService(
        workflow=workflow,
    )

    dataset_id = uuid4()

    response = await service.get_dataset(
        dataset_id=dataset_id,
    )

    assert response.dataset_id == dataset_id

    assert workflow.received_dataset_id == dataset_id

    assert response.status == "COMPLETED"


@pytest.mark.asyncio
async def test_get_dataset_propagates_not_found_exception():

    workflow = FakeWorkflow()

    workflow.error = NotFoundException("Dataset not found.")

    service = DatasetService(
        workflow=workflow,
    )

    with pytest.raises(NotFoundException):
        await service.get_dataset(
            dataset_id=uuid4(),
        )
