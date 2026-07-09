from app.routes.uploads.dtos.dto import UploadInitRequestDTO
from app.routes.uploads.services.service import UploadService


class FakeInitWorkflow:
    def __init__(self) -> None:
        self.received_request = None

    def run(self, request: UploadInitRequestDTO) -> dict:
        self.received_request = request
        return {"status": "UPLOADING"}


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
