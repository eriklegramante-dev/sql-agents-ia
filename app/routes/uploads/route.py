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
def initialize_upload(
    request: UploadInitRequestDTO,
    controller: UploadController = Depends(get_upload_controller),
):
    """Initialize a dataset multipart upload.

    Args:
        request: Validated upload initialization request.
        controller: Injected upload controller.

    Returns:
        Standardized upload initialization response.
    """
    return controller.initialize_upload(request)


@router.post(
    "/complete",
    status_code=status.HTTP_200_OK,
    response_model=UploadCompleteResponseDTO,
)
def complete_upload(
    request: UploadCompleteRequestDTO,
    controller: UploadController = Depends(get_upload_controller),
):
    """Complete a dataset multipart upload.

    Args:
        request: Validated upload completion request.
        controller: Injected upload controller.

    Returns:
        Standardized upload completion response containing final metadata.
    """
    return controller.complete_upload(request)


@router.post(
    "/abort",
    status_code=status.HTTP_200_OK,
    response_model=UploadAbortResponseDTO,
)
def abort_upload(
    request: UploadAbortRequestDTO,
    controller: UploadController = Depends(get_upload_controller),
):
    """Abort an unfinished dataset multipart upload.

    Args:
        request: Validated upload abort request.
        controller: Injected upload controller.

    Returns:
        Standardized upload abort response containing final statuses.
    """
    return controller.abort_upload(request)
