from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.prepare.exceptions import NotFoundException
from app.routes.datasets.controllers.controller import DatasetController
from app.routes.datasets.dtos.dto import DatasetResponseDataDTO


class FakeDatasetService:

    def __init__(self):
        self.error = None
        self.received_dataset_id = None

    async def get_dataset(self, dataset_id: UUID):
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
            description="Dataset used in tests",
            created_at=now,
            updated_at=now,
        )


@pytest.mark.asyncio
async def test_get_dataset_returns_success_response():

    service = FakeDatasetService()

    controller = DatasetController(
        service=service,
    )

    dataset_id = uuid4()

    response = await controller.get_dataset(
        dataset_id=dataset_id,
    )

    assert response["success"] is True
    assert response["message"] == "Dataset retrieved successfully."

    assert (
        UUID(response["data"]["dataset_id"])
        == dataset_id
    )

    assert (
        service.received_dataset_id
        == dataset_id
    )


@pytest.mark.asyncio
async def test_get_dataset_returns_not_found_http_exception():

    service = FakeDatasetService()

    service.error = NotFoundException(
        "Dataset not found."
    )

    controller = DatasetController(
        service=service,
    )

    with pytest.raises(HTTPException) as exc:

        await controller.get_dataset(
            dataset_id=uuid4(),
        )

    assert exc.value.status_code == 404

    assert (
        exc.value.detail["success"]
        is False
    )

    assert (
        exc.value.detail["message"]
        == "Dataset not found."
    )


@pytest.mark.asyncio
async def test_get_dataset_returns_validation_error():

    service = FakeDatasetService()

    controller = DatasetController(
        service=service,
    )

    with pytest.raises(HTTPException) as exc:

        await controller.get_dataset(
            dataset_id="invalid-uuid",
        )

    assert exc.value.status_code == 422