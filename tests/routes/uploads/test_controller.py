from fastapi import status
from fastapi.responses import JSONResponse

from app.routes.uploads.controllers.controller import UploadController
from app.routes.uploads.dtos.dto import UploadInitRequestDTO


class FakeUploadService:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def initialize_upload(self, request: UploadInitRequestDTO) -> dict:
        if self.should_fail:
            raise ValueError("Invalid upload request.")

        return {
            "dataset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "upload_id": "fake-upload-id",
            "object_key": "datasets/id/raw/customers.csv",
            "status": "UPLOADING",
            "chunk_size_bytes": 5242880,
            "chunks_count": 1,
            "parts": [
                {
                    "part_number": 1,
                    "upload_url": "https://fake-storage.local/upload",
                }
            ],
        }


def make_request() -> UploadInitRequestDTO:
    return UploadInitRequestDTO(
        filename="customers.csv",
        content_type="text/csv",
        file_size_bytes=1000,
        dataset_name="Customers",
        description=None,
    )


def test_initialize_upload_returns_success_response() -> None:
    controller = UploadController(service=FakeUploadService())
    request = make_request()

    response = controller.initialize_upload(request)

    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_201_CREATED


def test_initialize_upload_returns_bad_request_on_value_error() -> None:
    controller = UploadController(service=FakeUploadService(should_fail=True))
    request = make_request()

    response = controller.initialize_upload(request)

    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    

class FakeAbortService:
    def abort_upload(self, dataset_id: str, upload_id: str) -> dict:
        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "upload_status": "ABORTED",
            "dataset_status": "ABORTED",
        }


class FakeFailAbortService:
    def abort_upload(self, dataset_id: str, upload_id: str) -> dict:
        raise ValueError("Upload cannot be aborted")


def make_abort_request():
    return type(
        "AbortRequest",
        (),
        {
            "dataset_id": "dataset-1",
            "upload_id": "upload-1",
        },
    )()


def test_abort_upload_controller_success() -> None:
    controller = UploadController(service=FakeAbortService())
    request = make_abort_request()

    response = controller.abort_upload(request)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200


def test_abort_upload_controller_failure() -> None:
    controller = UploadController(service=FakeFailAbortService())
    request = make_abort_request()

    response = controller.abort_upload(request)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400