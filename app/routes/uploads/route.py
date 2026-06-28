from fastapi import APIRouter, Depends, status

from app.core.uploads.controller import UploadController
from app.core.uploads.dto import UploadInitRequestDTO, UploadInitResponseDTO
from app.routes.uploads.dependencies import get_upload_controller

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
    """
    Initialize a dataset multipart upload.
    """
    return controller.initialize_upload(request)
