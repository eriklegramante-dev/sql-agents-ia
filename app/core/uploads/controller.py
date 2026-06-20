from fastapi import status
from fastapi.responses import JSONResponse

from app.core.uploads.dto import (
    UploadInitRequestDTO,
    UploadInitResponseDataDTO,
    UploadInitResponseDTO,
)
from app.core.uploads.service import UploadService


class UploadController:
    """Controller responsible for handling upload HTTP requests.

    Attributes:
        service: Upload service used to process requests.
    """

    def __init__(self, service: UploadService) -> None:
        """Initialize the upload controller.

        Args:
            service: Upload service used to process requests.
        """
        self.service = service

    def initialize_upload(
        self,
        request: UploadInitRequestDTO,
    ) -> JSONResponse:
        """Handle the upload initialization request.

        Args:
            request: Validated upload initialization request.

        Returns:
            Standardized JSON response.
        """
        try:
            result = self.service.initialize_upload(request)
            response = UploadInitResponseDTO(
                success=True,
                message="Upload initialized successfully.",
                data=UploadInitResponseDataDTO(**result),
            )

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response.model_dump(mode="json"),
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": str(exc),
                    "data": None,
                },
            )