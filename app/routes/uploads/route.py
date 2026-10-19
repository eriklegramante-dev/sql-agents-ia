from fastapi import APIRouter, Depends, status

from app.routes.uploads.controllers.controller import UploadController
from app.routes.uploads.dependencies.dependence import get_upload_controller
from app.security.security import get_trusted_user_id
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
    user_id: int = Depends(get_trusted_user_id),
    controller: UploadController = Depends(get_upload_controller),
):
    """Create a new multipart upload session for a dataset.

    Args:
        request:
            Validated upload initialization request.
        user_id:
            Trusted user identity forwarded by the route security dependency.
        controller:
            Controller responsible for the upload flow.

    Returns:
        JSON response containing the upload metadata and signed URLs.
    """
    return await controller.initialize_upload(request=request, user_id=user_id)


@router.post(
    "/complete",
    status_code=status.HTTP_200_OK,
    response_model=UploadCompleteResponseDTO,
)
async def complete_upload(
    request: UploadCompleteRequestDTO,
    user_id: int = Depends(get_trusted_user_id),
    controller: UploadController = Depends(get_upload_controller),
) -> UploadCompleteResponseDTO:
    """Delegate multipart upload completion using the trusted user identity.

    The controller forwards the request to the completion workflow, which
    checks ownership, validates parts, completes storage, and updates metadata.

    Args:
        request: Validated upload completion payload.
        user_id: Trusted identity supplied by the route security dependency.
        controller: Injected controller responsible for the completion flow.

    Returns:
        JSON response containing completion metadata or a handled upload error.
    """
    return await controller.complete_upload(request=request, user_id=user_id)


@router.post(
    "/abort",
    status_code=status.HTTP_200_OK,
    response_model=UploadAbortResponseDTO,
)
async def abort_upload(
    request: UploadAbortRequestDTO,
    user_id: int = Depends(get_trusted_user_id),
    controller: UploadController = Depends(get_upload_controller),
) -> UploadAbortResponseDTO:
    """Delegate multipart upload cancellation using the trusted user identity.

    The workflow checks ownership before processing the upload status and
    performing any required storage abort and temporary-part cleanup.

    Args:
        request: Validated upload abort payload.
        user_id: Trusted identity supplied by the route security dependency.
        controller: Injected controller responsible for the abort flow.

    Returns:
        JSON response containing final upload statuses or a handled upload error.
    """
    return await controller.abort_upload(request=request, user_id=user_id)
