import pytest

from app.routes.uploads.dtos.dto import UploadInitRequestDTO
from app.routes.uploads.services.service import UploadService


class FakeInitWorkflow:
    def __init__(self) -> None:
        self.received_request = None

    async def run(
        self,
        request: UploadInitRequestDTO,
    ) -> dict:
        self.received_request = request

        return {
            "status": "UPLOADING"
        }


class FakeCompleteWorkflow:
    def __init__(self) -> None:
        self.received_dataset_id = None
        self.received_upload_id = None
        self.received_parts = None

    async def run(
        self,
        dataset_id: str,
        upload_id: str,
        parts: list[dict],
    ) -> dict:

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

    async def run(
        self,
        dataset_id: str,
        upload_id: str,
    ) -> dict:

        self.received_dataset_id = dataset_id
        self.received_upload_id = upload_id

        return {
            "dataset_id": dataset_id,
            "upload_id": upload_id,
            "upload_status": "ABORTED",
            "dataset_status": "ABORTED",
        }


def build_service() -> tuple[
    UploadService,
    FakeInitWorkflow,
    FakeCompleteWorkflow,
    FakeAbortWorkflow,
]:

    init_workflow = FakeInitWorkflow()
    complete_workflow = FakeCompleteWorkflow()
    abort_workflow = FakeAbortWorkflow()

    service = UploadService(
        init_workflow=init_workflow,
        complete_workflow=complete_workflow,
        abort_workflow=abort_workflow,
    )

    return (
        service,
        init_workflow,
        complete_workflow,
        abort_workflow,
    )


@pytest.mark.asyncio
async def test_initialize_upload_delegates_to_workflow() -> None:

    service, init_workflow, _, _ = build_service()

    request = UploadInitRequestDTO(
        filename="customers.csv",
        content_type="text/csv",
        file_size_bytes=1000,
        dataset_name="Customers",
        description=None,
    )

    result = await service.initialize_upload(request)

    assert result == {
        "status": "UPLOADING"
    }

    assert init_workflow.received_request == request


@pytest.mark.asyncio
async def test_complete_upload_delegates_to_workflow() -> None:

    service, _, complete_workflow, _ = build_service()

    parts = [
        {
            "part_number": 1,
            "etag": "etag-1",
        }
    ]

    result = await service.complete_upload(
        dataset_id="dataset-1",
        upload_id="upload-1",
        parts=parts,
    )

    assert result["status"] == "COMPLETED"

    assert (
        complete_workflow.received_dataset_id
        == "dataset-1"
    )

    assert (
        complete_workflow.received_upload_id
        == "upload-1"
    )

    assert complete_workflow.received_parts == parts


@pytest.mark.asyncio
async def test_abort_upload_delegates_to_workflow() -> None:

    service, _, _, abort_workflow = build_service()

    result = await service.abort_upload(
        dataset_id="dataset-1",
        upload_id="upload-1",
    )

    assert result["upload_status"] == "ABORTED"

    assert (
        abort_workflow.received_dataset_id
        == "dataset-1"
    )

    assert (
        abort_workflow.received_upload_id
        == "upload-1"
    )