from uuid import UUID

import pytest

from app.enums.dataset_status import DatasetStatus
from app.models.dataset_table import DatasetTable
from app.repositories.postgres_upload_metadata_repository import (
    PostgresUploadMetadataRepository,
)


class FakeDatasetRepository:

    def __init__(self):
        self.created_dataset = None
        self.updated_status = None


    async def create(self, dataset):
        self.created_dataset = dataset


    async def find_by_upload(
        self,
        dataset_id,
        upload_id,
    ):

        return DatasetTable(
            id=dataset_id,
            name="file.csv",
            filename="file.csv",
            status=DatasetStatus.UPLOADING,
            raw_object_key="raw/file.csv",
            prepared_object_key=None,
            user_id=None,
            description="test",
            file_type=None,
            content_type="text/csv",
            file_size_bytes=100,
            current_upload_job_id=upload_id,
        )


    async def update_upload_status(
        self,
        dataset_id,
        upload_id,
        status,
    ):
        self.updated_status = {
            "dataset_id":dataset_id,
            "upload_id":upload_id,
            "status":status,
        }



@pytest.mark.asyncio
async def test_create_converts_metadata_to_dataset():

    repository = FakeDatasetRepository()

    postgres_repository = PostgresUploadMetadataRepository(
        repository
    )


    await postgres_repository.create(
        {
            "dataset_id":UUID(
                "11111111-1111-1111-1111-111111111111"
            ),
            "dataset_name":"file.csv",
            "filename":"file.csv",
            "dataset_status":"UPLOADING",
            "object_key":"raw/file.csv",
            "content_type":"text/csv",
            "file_size_bytes":100,
            "upload_id":"upload-1",
        }
    )


    assert repository.created_dataset.name == "file.csv"
    assert repository.created_dataset.raw_object_key == (
        "raw/file.csv"
    )


@pytest.mark.asyncio
async def test_find_by_dataset_and_upload_returns_metadata():

    repository = FakeDatasetRepository()

    postgres_repository = PostgresUploadMetadataRepository(
        repository
    )


    result = await postgres_repository.find_by_dataset_and_upload(
        "11111111-1111-1111-1111-111111111111",
        "upload-1",
    )


    assert result["upload_id"] == "upload-1"
    assert result["object_key"] == "raw/file.csv"


@pytest.mark.asyncio
async def test_update_status_delegates_repository():

    repository = FakeDatasetRepository()

    postgres_repository = PostgresUploadMetadataRepository(
        repository
    )


    await postgres_repository.update_status(
        "11111111-1111-1111-1111-111111111111",
        "upload-1",
        "COMPLETED",
        "COMPLETED",
    )


    assert repository.updated_status["status"] == (
        DatasetStatus.COMPLETED
    )


@pytest.mark.asyncio
async def test_store_completed_parts_does_nothing():

    repository = FakeDatasetRepository()

    postgres_repository = PostgresUploadMetadataRepository(
        repository
    )


    result = await postgres_repository.store_completed_parts(
        "dataset",
        "upload",
        [],
    )


    assert result is None