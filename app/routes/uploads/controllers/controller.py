from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse

from app.logs.setup_logger import LOGGER, LoggerManager, LoggerManager
from app.routes.uploads.dtos.dto import (
    UploadAbortRequestDTO,
    UploadAbortResponseDTO,
    UploadAbortResponseDataDTO,
    UploadInitRequestDTO,
    UploadInitResponseDataDTO,
    UploadInitResponseDTO,
)
from app.routes.uploads.services.service import UploadService


class UploadController:
    """Controller responsible for handling upload HTTP requests.

    Attributes:
        service: Upload service used to process upload use cases.
    """

    def __init__(
        self,
        service: Optional[UploadService] = None,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        """Initialize the upload controller.

        Args:
            service: Upload service used to process requests.
        """
        self.service = service or UploadService()
        self.logger = logger or LOGGER

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
            self.logger.log_info(
                "[upload:init:controller] Received upload initialization request"
            )
            result = self.service.initialize_upload(request)
            response = UploadInitResponseDTO(
                success=True,
                message="Upload initialized successfully.",
                data=UploadInitResponseDataDTO(**result),
            )

            self.logger.log_info(
                "[upload:init:controller] Upload initialization response created"
            )

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response.model_dump(mode="json"),
            )
        except ValueError as exc:
            self.logger.log_warning(
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

    def abort_upload(
        self,
        request: UploadAbortRequestDTO,
    ) -> JSONResponse:
        """Handle the upload abort request.

        Args:
            request: Validated upload abort request.

        Returns:
            Standardized JSON response containing final upload statuses.
        """
        try:
            self.logger.log_info("[upload:abort:controller] Received upload abort request")

            result = self.service.abort_upload(
                dataset_id=str(request.dataset_id),
                upload_id=request.upload_id,
            )
            response = UploadAbortResponseDTO(
                success=True,
                message="Upload abort processed successfully.",
                data=UploadAbortResponseDataDTO(**result),
            )

            self.logger.log_info("[upload:abort:controller] Upload abort response created")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response.model_dump(mode="json"),
            )
        except ValueError as exc:
            self.logger.log_warning(
                f"[upload:abort:controller] Upload abort validation failed: {exc}"
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": str(exc),
                    "data": None,
                },
            )
        except RuntimeError as exc:
            self.logger.log_error(
                f"[upload:abort:controller] Upload abort processing failed: {exc}"
            )
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content={
                    "success": False,
                    "message": str(exc),
                    "data": None,
                },
            )
