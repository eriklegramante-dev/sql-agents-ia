import pytest

from app.core.uploads.abort_workflow import UploadAbortWorkflow
from app.core.uploads.enums import DatasetStatus, UploadStatus


class FakeRepository:
    def __init__(self, metadata=None) -> None:
        self.metadata = metadata
        self.updated_status = None

    def find_by_dataset_and_upload(self, dataset_id: str, upload_id: str):
        return self.metadata

    def update_status(
        self,
        dataset_id: str,
        upload_id: str,
        upload_status: str,
        dataset_status: str,
    ) -> None:
        self.updated_status = {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "upload_status": upload_status,
            "dataset_status": dataset_status,
        }


class FakeStorageAdapter:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.abort_called = False
        self.cleanup_called = False

    def abort_multipart_upload(self, object_key: str, upload_id: str) -> None:
        self.abort_called = True
        if self.should_fail:
            raise RuntimeError("storage unavailable")

    def cleanup_temporary_parts(self, object_key: str, upload_id: str) -> None:
        self.cleanup_called = True


def make_metadata(status: str = UploadStatus.UPLOADING.value):
    return {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "upload_status": status,
        "dataset_status": DatasetStatus.UPLOADING.value,
        "object_key": "datasets/dataset-1/raw/customers.csv",
    }


def test_abort_upload_successfully_when_status_is_uploading() -> None:
    repository = FakeRepository(metadata=make_metadata())
    storage_adapter = FakeStorageAdapter()
    workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )

    result = workflow.run(dataset_id="dataset-1", upload_id="upload-1")

    assert result["dataset_id"] == "dataset-1"
    assert result["upload_id"] == "upload-1"
    assert result["upload_status"] == UploadStatus.ABORTED.value
    assert result["dataset_status"] == DatasetStatus.ABORTED.value
    assert storage_adapter.abort_called is True
    assert storage_adapter.cleanup_called is True
    assert repository.updated_status["upload_status"] == UploadStatus.ABORTED.value
    assert repository.updated_status["dataset_status"] == DatasetStatus.ABORTED.value
    assert repository.metadata["aborted_at"] is not None
    assert repository.metadata["abort_reason"] == "User requested upload abort."


def test_abort_upload_successfully_when_status_is_failed() -> None:
    repository = FakeRepository(metadata=make_metadata(UploadStatus.FAILED.value))
    storage_adapter = FakeStorageAdapter()
    workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )

    result = workflow.run(dataset_id="dataset-1", upload_id="upload-1")

    assert result["upload_status"] == UploadStatus.ABORTED.value
    assert result["dataset_status"] == DatasetStatus.ABORTED.value
    assert storage_adapter.abort_called is True
    assert storage_adapter.cleanup_called is True


def test_abort_upload_raises_value_error_when_metadata_is_missing() -> None:
    repository = FakeRepository(metadata=None)
    storage_adapter = FakeStorageAdapter()
    workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )

    with pytest.raises(ValueError, match="Upload metadata not found"):
        workflow.run(dataset_id="dataset-1", upload_id="upload-1")

    assert storage_adapter.abort_called is False
    assert storage_adapter.cleanup_called is False


def test_abort_upload_raises_value_error_when_upload_is_completed() -> None:
    repository = FakeRepository(metadata=make_metadata(UploadStatus.COMPLETED.value))
    storage_adapter = FakeStorageAdapter()
    workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )

    with pytest.raises(ValueError, match="Completed uploads cannot be aborted"):
        workflow.run(dataset_id="dataset-1", upload_id="upload-1")

    assert storage_adapter.abort_called is False
    assert storage_adapter.cleanup_called is False


def test_abort_upload_returns_no_op_when_upload_is_already_aborted() -> None:
    repository = FakeRepository(metadata=make_metadata(UploadStatus.ABORTED.value))
    storage_adapter = FakeStorageAdapter()
    workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )

    result = workflow.run(dataset_id="dataset-1", upload_id="upload-1")

    assert result["upload_status"] == UploadStatus.ABORTED.value
    assert result["dataset_status"] == DatasetStatus.ABORTED.value
    assert storage_adapter.abort_called is False
    assert storage_adapter.cleanup_called is False
    assert repository.updated_status is None


def test_abort_upload_raises_value_error_when_status_is_not_cancelable() -> None:
    repository = FakeRepository(metadata=make_metadata("UNKNOWN"))
    storage_adapter = FakeStorageAdapter()
    workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )

    with pytest.raises(ValueError, match="Upload status cannot be aborted"):
        workflow.run(dataset_id="dataset-1", upload_id="upload-1")

    assert storage_adapter.abort_called is False
    assert storage_adapter.cleanup_called is False


def test_abort_upload_raises_value_error_when_object_key_is_missing() -> None:
    metadata = make_metadata()
    metadata.pop("object_key")
    repository = FakeRepository(metadata=metadata)
    storage_adapter = FakeStorageAdapter()
    workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )

    with pytest.raises(ValueError, match="Upload object key not found"):
        workflow.run(dataset_id="dataset-1", upload_id="upload-1")

    assert storage_adapter.abort_called is False
    assert storage_adapter.cleanup_called is False


def test_abort_upload_raises_runtime_error_when_storage_fails() -> None:
    repository = FakeRepository(metadata=make_metadata())
    storage_adapter = FakeStorageAdapter(should_fail=True)
    workflow = UploadAbortWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )

    with pytest.raises(RuntimeError, match="Upload storage abort failed"):
        workflow.run(dataset_id="dataset-1", upload_id="upload-1")

    assert storage_adapter.abort_called is True
    assert storage_adapter.cleanup_called is False
