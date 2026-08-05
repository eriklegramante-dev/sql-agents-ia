from datetime import datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.datasets.workflow import DatasetWorkflow
from app.enums.dataset_status import DatasetStatus
from app.prepare.exceptions import NotFoundException


class FakeRepository:

    def __init__(self):
        self.dataset = None

    async def get_by_id(self, dataset_id):
        return self.dataset


def make_dataset():

    now = datetime.now()

    return SimpleNamespace(
        id=uuid4(),
        name="Customers",
        filename="customers.csv",
        content_type="text/csv",
        file_size_bytes=1024,
        status=DatasetStatus.COMPLETED,
        raw_object_key="datasets/customers.csv",
        description="Dataset used in tests",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_execute_returns_dataset_metadata():

    repository = FakeRepository()

    repository.dataset = make_dataset()

    workflow = DatasetWorkflow(
        dataset_repository=repository
    )

    response = await workflow.execute(
        repository.dataset.id
    )

    assert response.dataset_id == repository.dataset.id
    assert response.name == "Customers"
    assert response.original_filename == "customers.csv"
    assert response.content_type == "text/csv"
    assert response.file_size_bytes == 1024
    assert response.status == DatasetStatus.COMPLETED.value
    assert response.object_key == "datasets/customers.csv"
    assert response.description == "Dataset used in tests"


@pytest.mark.asyncio
async def test_execute_raises_not_found_when_dataset_does_not_exist():

    repository = FakeRepository()

    workflow = DatasetWorkflow(
        dataset_repository=repository
    )

    with pytest.raises(NotFoundException):

        await workflow.execute(
            uuid4()
        )


@pytest.mark.asyncio
async def test_execute_accepts_status_as_plain_string():

    repository = FakeRepository()

    dataset = make_dataset()

    dataset.status = "COMPLETED"

    repository.dataset = dataset

    workflow = DatasetWorkflow(
        dataset_repository=repository
    )

    response = await workflow.execute(
        dataset.id
    )

    assert response.status == "COMPLETED"