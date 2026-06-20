from fastapi import APIRouter

from app.adapters.storage.fake_blob_storage_adapter import FakeBlobStorageAdapter
from app.core.uploads.controller import UploadController
from app.core.uploads.dto import UploadInitRequestDTO
from app.core.uploads.init_workflow import UploadInitializationWorkflow
from app.core.uploads.service import UploadService
from app.repositories.in_memory_upload_metadata_repository import (
    InMemoryUploadMetadataRepository,
)
from app.settings.app_config import app_config

router = APIRouter(prefix="/uploads", tags=["Uploads"])

repository = InMemoryUploadMetadataRepository()
storage_adapter = FakeBlobStorageAdapter()


def get_upload_controller() -> UploadController:
    """Create an upload controller with its dependencies.

    Returns:
        Configured upload controller instance.
    """
    workflow = UploadInitializationWorkflow(
        repository=repository,
        storage_adapter=storage_adapter,
        config=app_config,
    )
    service = UploadService(init_workflow=workflow)
    return UploadController(service=service)


@router.post("/init")
def initialize_upload(request: UploadInitRequestDTO):
    """Initialize a dataset multipart upload.

    Args:
        request: Upload initialization payload.

    Returns:
        Standardized upload initialization response.
    """
    controller = get_upload_controller()
    return controller.initialize_upload(request)