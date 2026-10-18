import pytest
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from fastapi import status
from fastapi.responses import JSONResponse

from app.core.uploads.exceptions import UploadAccessDeniedError
from app.core.uploads.exceptions import UploadCompletionError
from app.routes.uploads.controllers.controller import UploadController
from app.routes.uploads.dtos.dto import (
    UploadCompleteRequestDTO,
    UploadInitRequestDTO,
)


class FakeUploadService:

    def __init__(
        self,
        should_fail: bool = False,
    ) -> None:
        self.should_fail = should_fail
        self.complete_error = None
        self.completed_upload = None

    async def initialize_upload(
        self,
        request: UploadInitRequestDTO,
        *,
        user_id: int,
    ) -> dict:

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

    async def complete_upload(
        self,
        dataset_id: str,
        upload_id: str,
        parts: list[dict],
        *,
        user_id: int,
    ) -> dict:

        if self.complete_error:
            raise self.complete_error

        self.completed_upload = {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "parts": parts,
            "user_id": user_id,
        }

        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "status": "COMPLETED",
            "object_key": f"datasets/{dataset_id}/raw/file.csv",
            "completed_parts_count": len(parts),
        }


def make_request() -> UploadInitRequestDTO:

    return UploadInitRequestDTO(
        filename="customers.csv",
        content_type="text/csv",
        file_size_bytes=1000,
        dataset_name="Customers",
        description=None,
    )


def make_complete_request() -> UploadCompleteRequestDTO:

    return UploadCompleteRequestDTO(
        dataset_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        upload_id="upload-1",
        parts=[
            {
                "part_number": 1,
                "etag": "etag-1",
            },
        ],
    )


@pytest.mark.asyncio
async def test_initialize_upload_returns_success_response() -> None:

    controller = UploadController(service=FakeUploadService())

    request = make_request()

    response = await controller.initialize_upload(request, user_id=17)

    assert isinstance(
        response,
        JSONResponse,
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_initialize_upload_returns_bad_request_on_value_error() -> None:

    controller = UploadController(service=FakeUploadService(should_fail=True))

    request = make_request()

    response = await controller.initialize_upload(request, user_id=17)

    assert isinstance(
        response,
        JSONResponse,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


class FakeAbortService:

    async def abort_upload(
        self,
        dataset_id: str,
        upload_id: str,
        *,
        user_id: int,
    ) -> dict:

        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "upload_status": "ABORTED",
            "dataset_status": "ABORTED",
        }


class FakeFailAbortService:

    async def abort_upload(
        self,
        dataset_id: str,
        upload_id: str,
        *,
        user_id: int,
    ) -> dict:

        raise ValueError("Upload cannot be aborted")


def make_abort_request():

    return type(
        "AbortRequest",
        (),
        {
            "dataset_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "upload_id": "upload-1",
        },
    )()


@pytest.mark.asyncio
async def test_abort_upload_controller_success() -> None:

    controller = UploadController(service=FakeAbortService())

    request = make_abort_request()

    response = await controller.abort_upload(request, user_id=17)

    assert isinstance(
        response,
        JSONResponse,
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_abort_upload_controller_failure() -> None:

    controller = UploadController(service=FakeFailAbortService())

    request = make_abort_request()

    response = await controller.abort_upload(request, user_id=17)

    assert isinstance(
        response,
        JSONResponse,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_complete_upload_returns_success_response() -> None:

    service = FakeUploadService()

    controller = UploadController(service=service)

    request = make_complete_request()

    response = await controller.complete_upload(request, user_id=17)

    assert service.completed_upload["user_id"] == 17

    assert response.status_code == status.HTTP_200_OK

    assert str(service.completed_upload["dataset_id"]) == (
        "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    )

    assert service.completed_upload["upload_id"] == "upload-1"

    assert service.completed_upload["parts"] == [
        {
            "part_number": 1,
            "etag": "etag-1",
        }
    ]


@pytest.mark.asyncio
async def test_complete_upload_returns_bad_request_when_service_raises_value_error() -> (
    None
):

    service = FakeUploadService()

    service.complete_error = ValueError("Invalid completion request.")

    controller = UploadController(service=service)

    request = make_complete_request()

    response = await controller.complete_upload(request, user_id=17)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_complete_upload_returns_bad_gateway_when_service_raises_completion_error() -> (
    None
):

    service = FakeUploadService()

    service.complete_error = UploadCompletionError(
        "Upload completion failed in object storage."
    )

    controller = UploadController(service=service)

    request = make_complete_request()

    response = await controller.complete_upload(request, user_id=17)

    assert isinstance(
        response,
        JSONResponse,
    )

    assert response.status_code == status.HTTP_502_BAD_GATEWAY

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("operation", "request_factory"),
    [
        ("complete_upload", make_complete_request),
        ("abort_upload", make_abort_request),
    ],
)
async def test_upload_returns_forbidden_when_access_is_denied(
    operation,
    request_factory,
):
    service_method = AsyncMock(
        side_effect=UploadAccessDeniedError(
            "You do not have access to this upload."
        )
    )
    service = SimpleNamespace(**{operation: service_method})
    controller = UploadController(service=service)

    response = await getattr(controller, operation)(
        request_factory(),
        user_id=17,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert json.loads(response.body) == {
        "success": False,
        "message": "You do not have access to this upload.",
        "data": None,
    }
    service_method.assert_awaited_once()
    assert service_method.await_args.kwargs["user_id"] == 17