from fastapi import APIRouter, Depends, status

from app.routes.uploads.controllers.controller import UploadController
from app.routes.uploads.dependencies.dependence import get_upload_controller
from app.routes.uploads.dtos.dto import (
    UploadAbortRequestDTO,
    UploadAbortResponseDTO,
    UploadCompleteRequestDTO,
    UploadCompleteResponseDTO,
    UploadInitRequestDTO,
    UploadInitResponseDTO,
)

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post(
    "/init",
    status_code=status.HTTP_201_CREATED,
    response_model=UploadInitResponseDTO,
)
async def initialize_upload(
    request: UploadInitRequestDTO,
    controller: UploadController = Depends(get_upload_controller),
):
    """Create a new multipart upload session for a dataset.

    Args:
        request:
            Validated upload initialization request.
        controller:
            Controller responsible for the upload flow.

    Returns:
        JSON response containing the upload metadata and signed URLs.
    """
    return await controller.initialize_upload(request)


@router.post(
    "/complete",
    status_code=status.HTTP_200_OK,
    response_model=UploadCompleteResponseDTO,
)
async def complete_upload(
    request: UploadCompleteRequestDTO,
    controller: UploadController = Depends(get_upload_controller),
) -> UploadCompleteResponseDTO:
    """Finalize a multipart dataset upload.

    This endpoint validates the uploaded parts, completes the multipart
    upload in object storage and updates the persisted dataset metadata.

    Args:
        request: Validated upload completion payload.
        controller: Configured upload controller.

    Returns:
        Standardized response containing the finalized upload metadata.
    """
    return await controller.complete_upload(request)


@router.post(
    "/abort",
    status_code=status.HTTP_200_OK,
    response_model=UploadAbortResponseDTO,
)
async def abort_upload(
    request: UploadAbortRequestDTO,
    controller: UploadController = Depends(get_upload_controller),
) -> UploadAbortResponseDTO:
    """Abort an active multipart upload.

    This endpoint cancels an unfinished multipart upload, removes any
    temporary objects created during the upload process and updates the
    dataset status accordingly.

    Args:
        request: Validated upload abort payload.
        controller: Configured upload controller.

    Returns:
        Standardized response containing the final upload and dataset
        statuses.
    """
    return await controller.abort_upload(request)
