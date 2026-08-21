import pytest

from app.core.uploads.abort_workflow import UploadAbortWorkflow
from app.core.uploads.enums import DatasetStatus, UploadStatus


class FakeUploadMetadataRepository:
    def __init__(self, metadata=None):
        self.metadata = metadata
        self.updated_status = None

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
        return None


class FakeStorageAdapter:
    def __init__(self):
        self.abort_called = False
        self.cleanup_called = False

    def abort_multipart_upload(
        self,
        object_key,
        upload_id,
    ):
        self.abort_called = True

    def cleanup_temporary_parts(
        self,
        object_key,
        upload_id,
    ):
        self.cleanup_called = True


class FailingStorageAdapter(FakeStorageAdapter):
    def abort_multipart_upload(
        self,
        object_key,
        upload_id,
    ):
        raise RuntimeError("Storage failure")


def build_metadata(
    status=UploadStatus.UPLOADING.value,
):
    return {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "upload_status": status,
        "dataset_status": DatasetStatus.UPLOADING.value,
        "object_key": "datasets/dataset-1/raw/file.csv",
    }


@pytest.mark.asyncio
async def test_abort_upload_successfully():
    metadata = build_metadata()

    repository = FakeUploadMetadataRepository(metadata=metadata)
    storage_adapter = FakeStorageAdapter()

    workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )

    result = await workflow.run(
        dataset_id="dataset-1",
        upload_id="upload-1",
    )

    assert result == {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "upload_status": UploadStatus.ABORTED.value,
        "dataset_status": DatasetStatus.FAILED.value,
    }

    assert storage_adapter.abort_called is True
    assert storage_adapter.cleanup_called is True

    assert repository.updated_status == {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "upload_status": UploadStatus.ABORTED.value,
        "dataset_status": DatasetStatus.FAILED.value,
    }

    assert "aborted_at" in metadata
    assert metadata["abort_reason"] == "User requested upload abort."


@pytest.mark.asyncio
async def test_abort_upload_when_metadata_is_missing():
    workflow = UploadAbortWorkflow(
        repository=FakeUploadMetadataRepository(metadata=None),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload metadata not found.",
    ):
        await workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
        )


@pytest.mark.asyncio
async def test_abort_upload_returns_when_already_aborted():
    workflow = UploadAbortWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata(
                status=UploadStatus.ABORTED.value,
            )
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    result = await workflow.run(
        dataset_id="dataset-1",
        upload_id="upload-1",
    )

    assert result == {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "upload_status": UploadStatus.ABORTED.value,
        "dataset_status": DatasetStatus.FAILED.value,
    }


@pytest.mark.asyncio
async def test_abort_upload_rejects_completed_upload():
    workflow = UploadAbortWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata(
                status=UploadStatus.COMPLETED.value,
            )
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Completed uploads cannot be aborted.",
    ):
        await workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        UploadStatus.PREPARING.value,
        UploadStatus.PREPARED.value,
        UploadStatus.PROFILING.value,
        UploadStatus.PROFILED.value,
        UploadStatus.DELETED.value,
    ],
)
async def test_abort_upload_rejects_invalid_status(
    status,
):
    workflow = UploadAbortWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata(status=status),
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload status cannot be aborted.",
    ):
        await workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
        )


@pytest.mark.asyncio
async def test_abort_upload_rejects_missing_object_key():
    metadata = build_metadata()
    metadata["object_key"] = ""

    workflow = UploadAbortWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=metadata,
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload object key not found.",
    ):
        await workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
        )


@pytest.mark.asyncio
async def test_abort_upload_raises_runtime_error_when_storage_fails():
    workflow = UploadAbortWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata(),
        ),
        storage_adapter=FailingStorageAdapter(),
    )

    with pytest.raises(
        RuntimeError,
        match="Upload storage abort failed.",
    ):
        await workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
        )
