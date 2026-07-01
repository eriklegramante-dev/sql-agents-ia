from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse

from app.routes.uploads.dto import (
    UploadInitRequestDTO,
    UploadInitResponseDataDTO,
    UploadInitResponseDTO,
)
from app.routes.uploads.service import UploadService
from app.logs.setup_logger import LOGGER


class UploadController:
    """Controller responsible for handling upload HTTP requests.

    Attributes:
        service: Upload service used to process requests.
    """

    def __init__(self, service: Optional[UploadService] = None) -> None:
        """Initialize the upload controller.

        Args:
            service: Upload service used to process requests.
        """
        self.service = service or UploadService()

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
            LOGGER.log_info(
                "[upload:init:controller] Received upload initialization request"
            )
            result = self.service.initialize_upload(request)
            response = UploadInitResponseDTO(
                success=True,
                message="Upload initialized successfully.",
                data=UploadInitResponseDataDTO(**result),
            )

            LOGGER.log_info(
                "[upload:init:controller] Upload initialization response created"
            )

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response.model_dump(mode="json"),
            )
        except ValueError as exc:
            LOGGER.log_warning(
                f"[upload:init:controller] Upload initialization validation failed: {exc}"
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": str(exc),
                    "data": None,
                },
            )
