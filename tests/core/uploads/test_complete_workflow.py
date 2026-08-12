import pytest

from app.adapters.storage.exceptions import StorageOperationError
from app.core.uploads.complete_workflow import UploadCompletionWorkflow
from app.core.uploads.enums import DatasetStatus, UploadStatus
from app.core.uploads.exceptions import UploadCompletionError


class FakeUploadMetadataRepository:
    def __init__(self, metadata=None):
        self.metadata = metadata
        self.updated_status = None
        self.completed_parts = None

    async def create(self, metadata):
        self.metadata = metadata

    async def find_by_dataset_and_upload(
        self,
        dataset_id,
        upload_id,
    ):
        return self.metadata

    async def update_status(
        self,
        dataset_id,
        upload_id,
        upload_status,
        dataset_status,
    ):
        self.updated_status = {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "upload_status": upload_status,
            "dataset_status": dataset_status,
        }

    async def store_completed_parts(
        self,
        dataset_id,
        upload_id,
        parts,
    ):
        self.completed_parts = {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "parts": parts,
        }


class FakeStorageAdapter:
    def __init__(self):
        self.completed_upload = None

    def complete_multipart_upload(
        self,
        object_key,
        upload_id,
        parts,
    ):
        self.completed_upload = {
            "object_key": object_key,
            "upload_id": upload_id,
            "parts": parts,
        }


class FailingStorageAdapter:
    def complete_multipart_upload(
        self,
        object_key,
        upload_id,
        parts,
    ):
        raise StorageOperationError(
            operation="complete multipart upload"
        )


def build_metadata(
    status=UploadStatus.UPLOADING.value,
):
    return {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "upload_status": status,
        "dataset_status": DatasetStatus.UPLOADING.value,
        "object_key": "datasets/file.csv",
        "chunks_count": 2,
    }


@pytest.mark.asyncio
async def test_complete_upload_successfully():

    repository = FakeUploadMetadataRepository(
        build_metadata()
    )

    storage = FakeStorageAdapter()

    workflow = UploadCompletionWorkflow(
        repository,
        storage,
    )

    result = await workflow.run(
        dataset_id="dataset-1",
        upload_id="upload-1",
        parts=[
            {
                "part_number": 2,
                "etag": "etag-2",
            },
            {
                "part_number": 1,
                "etag": "etag-1",
            },
        ],
    )


    assert result["status"] == UploadStatus.COMPLETED.value
    assert result["completed_parts_count"] == 2

    assert storage.completed_upload["parts"] == [
        {
            "part_number": 1,
            "etag": "etag-1",
        },
        {
            "part_number": 2,
            "etag": "etag-2",
        },
    ]

    assert repository.updated_status["upload_status"] == (
        UploadStatus.COMPLETED.value
    )


@pytest.mark.asyncio
async def test_complete_upload_metadata_not_found():

    workflow = UploadCompletionWorkflow(
        FakeUploadMetadataRepository(None),
        FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload metadata not found",
    ):
        await workflow.run(
            "dataset-1",
            "upload-1",
            [{"part_number": 1, "etag": "abc"}],
        )


@pytest.mark.asyncio
async def test_complete_upload_invalid_status():

    repository = FakeUploadMetadataRepository(
        build_metadata(
            status=UploadStatus.COMPLETED.value
        )
    )

    workflow = UploadCompletionWorkflow(
        repository,
        FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload status cannot be completed",
    ):
        await workflow.run(
            "dataset-1",
            "upload-1",
            [{"part_number":1,"etag":"abc"}],
        )


@pytest.mark.asyncio
async def test_complete_upload_without_object_key():

    metadata = build_metadata()
    metadata["object_key"] = None

    workflow = UploadCompletionWorkflow(
        FakeUploadMetadataRepository(metadata),
        FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload object key not found",
    ):
        await workflow.run(
            "dataset-1",
            "upload-1",
            [{"part_number":1,"etag":"abc"}],
        )


@pytest.mark.asyncio
async def test_complete_upload_empty_parts():

    workflow = UploadCompletionWorkflow(
        FakeUploadMetadataRepository(build_metadata()),
        FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload parts must not be empty",
    ):
        await workflow.run(
            "dataset-1",
            "upload-1",
            [],
        )


@pytest.mark.asyncio
async def test_complete_upload_duplicate_parts():

    workflow = UploadCompletionWorkflow(
        FakeUploadMetadataRepository(build_metadata()),
        FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Duplicated part numbers",
    ):
        await workflow.run(
            "dataset-1",
            "upload-1",
            [
                {
                    "part_number":1,
                    "etag":"a",
                },
                {
                    "part_number":1,
                    "etag":"b",
                },
            ],
        )


@pytest.mark.asyncio
async def test_complete_upload_invalid_part_number():

    workflow = UploadCompletionWorkflow(
        FakeUploadMetadataRepository(build_metadata()),
        FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Part numbers must be positive integers",
    ):
        await workflow.run(
            "dataset-1",
            "upload-1",
            [
                {
                    "part_number":0,
                    "etag":"abc",
                },
                {
                    "part_number":2,
                    "etag":"def",
                },
            ],
        )


@pytest.mark.asyncio
async def test_complete_upload_invalid_etag():

    workflow = UploadCompletionWorkflow(
        FakeUploadMetadataRepository(build_metadata()),
        FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="valid ETag",
    ):
        await workflow.run(
            "dataset-1",
            "upload-1",
            [
                {
                    "part_number":1,
                    "etag":"",
                },
                {
                    "part_number":2,
                    "etag":"abc",
                },
            ],
        )


@pytest.mark.asyncio
async def test_complete_upload_wrong_chunks_count():

    workflow = UploadCompletionWorkflow(
        FakeUploadMetadataRepository(build_metadata()),
        FakeStorageAdapter(),
    )


    with pytest.raises(
        ValueError,
        match="does not match expected chunks count",
    ):
        await workflow.run(
            "dataset-1",
            "upload-1",
            [
                {
                    "part_number":1,
                    "etag":"abc",
                }
            ],
        )


@pytest.mark.asyncio
async def test_complete_upload_storage_failure():

    workflow = UploadCompletionWorkflow(
        FakeUploadMetadataRepository(build_metadata()),
        FailingStorageAdapter(),
    )


    with pytest.raises(
        UploadCompletionError,
        match="Upload completion failed",
    ):
        await workflow.run(
            "dataset-1",
            "upload-1",
            [
                {
                    "part_number":1,
                    "etag":"abc",
                },
                {
                    "part_number":2,
                    "etag":"def",
                },
            ],
        )