from fastapi import APIRouter, status

from app.routes.uploads.controller import UploadController
from app.routes.uploads.dto import UploadInitRequestDTO, UploadInitResponseDTO

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post(
    "/init",
    status_code=status.HTTP_201_CREATED,
    response_model=UploadInitResponseDTO,
)
def initialize_upload(request: UploadInitRequestDTO):
    """
    Initialize a dataset multipart upload.
    """
    controller = UploadController()
    return controller.initialize_upload(request)
