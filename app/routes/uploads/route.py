from fastapi import APIRouter, status

from app.routes.uploads.controllers.controller import UploadController
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
def initialize_upload(request: UploadInitRequestDTO):
    """Initialize a dataset multipart upload.

    Args:
        request: Validated upload initialization request.

    Returns:
        Standardized upload initialization response.
    """
    controller = UploadController()
    return controller.initialize_upload(request)


@router.post(
    "/complete",
    status_code=status.HTTP_200_OK,
    response_model=UploadCompleteResponseDTO,
)
def complete_upload(request: UploadCompleteRequestDTO):
    """Complete a dataset multipart upload.

    Args:
        request: Validated upload completion request.

    Returns:
        Standardized upload completion response containing final metadata.
    """
    controller = UploadController()
    return controller.complete_upload(request)


@router.post(
    "/abort",
    status_code=status.HTTP_200_OK,
    response_model=UploadAbortResponseDTO,
)
def abort_upload(request: UploadAbortRequestDTO):
    """Abort an unfinished dataset multipart upload.

    Args:
        request: Validated upload abort request.

    Returns:
        Standardized upload abort response containing final statuses.
    """
    controller = UploadController()
    return controller.abort_upload(request)
