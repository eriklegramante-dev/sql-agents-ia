import pytest

from app.adapters.storage.exceptions import StorageOperationError
from app.core.uploads.complete_workflow import UploadCompletionWorkflow
from app.core.uploads.enums import DatasetStatus, UploadStatus
from app.core.uploads.exceptions import UploadCompletionError


class FakeUploadMetadataRepository:
    def __init__(self, metadata=None) -> None:
        self.metadata = metadata
        self.updated_status = None
        self.completed_parts = None

    def find_by_dataset_and_upload(
        self,
        dataset_id: str,
        upload_id: str,
    ):
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

    def store_completed_parts(
        self,
        dataset_id: str,
        upload_id: str,
        parts: list,
    ) -> None:
        self.completed_parts = {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "parts": parts,
        }


class FakeStorageAdapter:
    def __init__(self) -> None:
        self.completed_upload = None

    def complete_multipart_upload(
        self,
        object_key: str,
        upload_id: str,
        parts: list,
    ) -> None:
        self.completed_upload = {
            "object_key": object_key,
            "upload_id": upload_id,
            "parts": parts,
        }


class FailingStorageAdapter(FakeStorageAdapter):
    def complete_multipart_upload(
        self,
        object_key: str,
        upload_id: str,
        parts: list,
    ) -> None:
        raise StorageOperationError(
            operation="complete multipart upload"
        )


def build_metadata(
    status: str = UploadStatus.UPLOADING.value,
):
    return {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "upload_status": status,
        "dataset_status": DatasetStatus.UPLOADING.value,
        "object_key": "datasets/dataset-1/raw/file.csv",
        "chunks_count": 2,
    }


def test_complete_upload_successfully() -> None:
    metadata = build_metadata()
    repository = FakeUploadMetadataRepository(metadata=metadata)
    storage_adapter = FakeStorageAdapter()
    workflow = UploadCompletionWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
    )
    parts = [
        {"part_number": 2, "etag": "etag-2"},
        {"part_number": 1, "etag": "etag-1"},
    ]

    result = workflow.run(
        dataset_id="dataset-1",
        upload_id="upload-1",
        parts=parts,
    )

    sorted_parts = [
        {"part_number": 1, "etag": "etag-1"},
        {"part_number": 2, "etag": "etag-2"},
    ]

    assert result == {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "status": UploadStatus.COMPLETED.value,
        "object_key": "datasets/dataset-1/raw/file.csv",
        "completed_parts_count": 2,
    }
    assert storage_adapter.completed_upload == {
        "object_key": "datasets/dataset-1/raw/file.csv",
        "upload_id": "upload-1",
        "parts": sorted_parts,
    }
    assert repository.completed_parts == {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "parts": sorted_parts,
    }
    assert repository.updated_status == {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "upload_status": UploadStatus.COMPLETED.value,
        "dataset_status": DatasetStatus.COMPLETED.value,
    }
    assert "completed_at" in metadata


def test_complete_upload_raises_value_error_when_metadata_is_missing() -> None:
    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(metadata=None),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload metadata not found.",
    ):
        workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
            parts=[
                {
                    "part_number": 1,
                    "etag": "etag-1",
                },
            ],
        )


@pytest.mark.parametrize(
    "status",
    [
        UploadStatus.COMPLETED.value,
        UploadStatus.ABORTED.value,
        UploadStatus.FAILED.value,
    ],
)
def test_complete_upload_raises_value_error_when_status_is_invalid(
    status: str,
) -> None:
    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata(status=status)
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload status cannot be completed.",
    ):
        workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
            parts=[
                {
                    "part_number": 1,
                    "etag": "etag-1",
                },
            ],
        )


def test_complete_upload_raises_value_error_when_object_key_is_missing() -> None:
    metadata = build_metadata()
    metadata["object_key"] = ""

    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(metadata=metadata),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload object key not found.",
    ):
        workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
            parts=[
                {
                    "part_number": 1,
                    "etag": "etag-1",
                },
            ],
        )


def test_complete_upload_raises_value_error_when_parts_are_empty() -> None:
    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata()
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Upload parts must not be empty.",
    ):
        workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
            parts=[],
        )


@pytest.mark.parametrize(
    "part_number",
    [0, -1, "1", None],
)
def test_complete_upload_raises_value_error_when_part_number_is_invalid(
    part_number,
) -> None:
    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata()
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Part numbers must be positive integers.",
    ):
        workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
            parts=[
                {
                    "part_number": part_number,
                    "etag": "etag-1",
                },
                {
                    "part_number": 2,
                    "etag": "etag-2",
                },
            ],
        )


@pytest.mark.parametrize(
    "etag",
    ["", "   ", None, 123],
)
def test_complete_upload_raises_value_error_when_etag_is_invalid(
    etag,
) -> None:
    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata()
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Each upload part must contain a valid ETag.",
    ):
        workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
            parts=[
                {
                    "part_number": 1,
                    "etag": etag,
                },
                {
                    "part_number": 2,
                    "etag": "etag-2",
                },
            ],
        )


def test_complete_upload_raises_value_error_when_parts_are_duplicated() -> None:
    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata()
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match="Duplicated part numbers are not allowed.",
    ):
        workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
            parts=[
                {
                    "part_number": 1,
                    "etag": "etag-1",
                },
                {
                    "part_number": 1,
                    "etag": "etag-2",
                },
            ],
        )


def test_complete_upload_raises_value_error_when_parts_count_does_not_match() -> None:
    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata()
        ),
        storage_adapter=FakeStorageAdapter(),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Uploaded parts count does not match expected chunks count."
        ),
    ):
        workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
            parts=[
                {
                    "part_number": 1,
                    "etag": "etag-1",
                },
            ],
        )


def test_complete_upload_accepts_parts_when_expected_chunks_count_is_missing() -> None:
    metadata = build_metadata()
    metadata["chunks_count"] = None

    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(metadata=metadata),
        storage_adapter=FakeStorageAdapter(),
    )

    result = workflow.run(
        dataset_id="dataset-1",
        upload_id="upload-1",
        parts=[
            {
                "part_number": 1,
                "etag": "etag-1",
            },
        ],
    )

    assert result["completed_parts_count"] == 1


def test_complete_upload_raises_upload_completion_error_when_storage_fails() -> None:
    workflow = UploadCompletionWorkflow(
        repository=FakeUploadMetadataRepository(
            metadata=build_metadata()
        ),
        storage_adapter=FailingStorageAdapter(),
    )

    with pytest.raises(
        UploadCompletionError,
        match="Upload completion failed in object storage.",
    ):
        workflow.run(
            dataset_id="dataset-1",
            upload_id="upload-1",
            parts=[
                {
                    "part_number": 1,
                    "etag": "etag-1",
                },
                {
                    "part_number": 2,
                    "etag": "etag-2",
                },
            ],
        )
