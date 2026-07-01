from app.routes.uploads.dto import UploadInitRequestDTO
from app.routes.uploads.service import UploadService


class FakeInitWorkflow:
    def __init__(self) -> None:
        self.received_request = None

    def run(self, request: UploadInitRequestDTO) -> dict:
        self.received_request = request
        return {"status": "UPLOADING"}


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