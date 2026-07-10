from app.routes.uploads.dtos.dto import UploadInitRequestDTO
from app.routes.uploads.services.service import UploadService


class FakeInitWorkflow:
    def __init__(self) -> None:
        self.received_request = None

    def run(self, request: UploadInitRequestDTO) -> dict:
        self.received_request = request
        return {"status": "UPLOADING"}


class FakeCompleteWorkflow:
    def __init__(self) -> None:
        self.received_dataset_id = None
        self.received_upload_id = None
        self.received_parts = None

    def run(self, dataset_id: str, upload_id: str, parts: list[dict]) -> dict:
        self.received_dataset_id = dataset_id
        self.received_upload_id = upload_id
        self.received_parts = parts
        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "status": "COMPLETED",
            "object_key": "datasets/dataset-1/raw/file.csv",
            "completed_parts_count": len(parts),
        }


class FakeAbortWorkflow:
    def __init__(self) -> None:
        self.received_dataset_id = None
        self.received_upload_id = None

    def run(self, dataset_id: str, upload_id: str) -> dict:
        self.received_dataset_id = dataset_id
        self.received_upload_id = upload_id
        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "upload_status": "ABORTED",
            "dataset_status": "ABORTED",
        }


def test_initialize_upload_delegates_to_workflow() -> None:
    workflow = FakeInitWorkflow()
    service = UploadService(workflow=workflow)
    request = UploadInitRequestDTO(
        filename="customers.csv",
        content_type="text/csv",
        file_size_bytes=1000,
        dataset_name="Customers",
        description=None,
    )

    result = service.initialize_upload(request)

    assert result == {"status": "UPLOADING"}
    assert workflow.received_request == request


def test_complete_upload_delegates_to_workflow() -> None:
    complete_workflow = FakeCompleteWorkflow()
    service = UploadService(
        complete_workflow=complete_workflow,
    )
    parts = [{"part_number": 1, "etag": "etag-1"}]

    result = service.complete_upload(
        dataset_id="dataset-1",
        upload_id="upload-1",
        parts=parts,
    )

    assert result == {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "status": "COMPLETED",
        "object_key": "datasets/dataset-1/raw/file.csv",
        "completed_parts_count": 1,
    }
    assert complete_workflow.received_dataset_id == "dataset-1"
    assert complete_workflow.received_upload_id == "upload-1"
    assert complete_workflow.received_parts == parts


def test_abort_upload_delegates_to_workflow() -> None:
    abort_workflow = FakeAbortWorkflow()
    service = UploadService(
        workflow=FakeInitWorkflow(),
        abort_workflow=abort_workflow,
    )

    result = service.abort_upload(
        dataset_id="dataset-1",
        upload_id="upload-1",
    )

    assert result == {
        "dataset_id": "dataset-1",
        "upload_id": "upload-1",
        "upload_status": "ABORTED",
        "dataset_status": "ABORTED",
    }
    assert abort_workflow.received_dataset_id == "dataset-1"
    assert abort_workflow.received_upload_id == "upload-1"
