from typing import Optional

from fastapi import status
from fastapi.responses import JSONResponse

from app.core.uploads.exceptions import UploadCompletionError, UploadAccessDeniedError
from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.uploads.dtos.dto import (
    UploadAbortRequestDTO,
    UploadAbortResponseDTO,
    UploadAbortResponseDataDTO,
    UploadCompleteRequestDTO,
    UploadCompleteResponseDTO,
    UploadCompleteResponseDataDTO,
    UploadInitRequestDTO,
    UploadInitResponseDataDTO,
    UploadInitResponseDTO,
)
from app.routes.uploads.services.service import UploadService


class UploadController:
    """Controller responsible for handling upload HTTP requests.

    This controller receives validated DTOs from the FastAPI routes,
    delegates the business execution to the UploadService and transforms
    the returned data into standardized HTTP responses.
    """

    def __init__(
        self,
        service: UploadService,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        """Initialize the upload controller.

        Args:
            service: Fully configured upload service used to process requests.
            logger: Logger used to register controller execution events.
        """
        self.service = service
        self.logger = logger or LOGGER

    async def initialize_upload(
        self,
        request: UploadInitRequestDTO,
        *,
        user_id: int,
    ) -> JSONResponse:
        """Handle upload initialization for the trusted user.

        Args:
            request: Validated request received from the route.
            user_id: Trusted caller identity forwarded to the service.

        Returns:
            HTTP 201 with upload metadata and signed part URLs, or HTTP 400
            when request processing raises ValueError.

        Exceptions outside the handled failure types propagate to the caller.
        """
        try:
            self.logger.log_info(
                "[upload:init:controller] Received upload initialization request"
            )
            result = await self.service.initialize_upload(request=request, user_id=user_id)
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
                    "message": "The upload initialization request is invalid.",
                    "data": None,
                },
            )

    async def complete_upload(
        self,
        request: UploadCompleteRequestDTO,
        *,
        user_id: int,
    ) -> JSONResponse:
        """Handle completion of an upload for the trusted user.

        Args:
            request: Validated request received from the route.
            user_id: Trusted caller identity forwarded to the service.

        Returns:
            HTTP 200 with completed upload metadata, HTTP 403 for denied
            ownership, HTTP 400 for invalid upload data, or HTTP 502 for a
            storage completion failure.

        Exceptions outside the handled failure types propagate to the caller.
        """
        try:
            self.logger.log_info(
                "[upload:complete:controller] Received upload completion request"
            )

            result = await self.service.complete_upload(
                dataset_id=(request.dataset_id),
                upload_id=request.upload_id,
                parts=[part.model_dump() for part in request.parts],
                user_id=user_id,
            )
            response = UploadCompleteResponseDTO(
                success=True,
                message="Upload completed successfully.",
                data=UploadCompleteResponseDataDTO(**result),
            )

            self.logger.log_info(
                "[upload:complete:controller] Upload completion response created"
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response.model_dump(mode="json"),
            )
        except UploadAccessDeniedError:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "message": "You do not have access to this upload.",
                    "data": None,
                },
            )
        except ValueError as exc:
            self.logger.log_warning(
                "[upload:complete:controller] "
                f"Upload completion validation failed: {exc}"
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "The upload completion request is invalid.",
                    "data": None,
                },
            )
        except UploadCompletionError as exc:
            self.logger.log_error(
                "[upload:complete:controller] "
                f"Upload completion processing failed: {exc}"
            )
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content={
                    "success": False,
                    "message": "The upload could not be completed at this time.",
                    "data": None,
                },
            )

    async def abort_upload(
        self,
        request: UploadAbortRequestDTO,
        *,
        user_id: int,
    ) -> JSONResponse:
        """Handle cancellation of an upload for the trusted user.

        Args:
            request: Validated request received from the route.
            user_id: Trusted caller identity forwarded to the service.

        Returns:
            HTTP 200 with final upload and dataset statuses, HTTP 403 for
            denied ownership, HTTP 400 for invalid upload data, or HTTP 502
            for a runtime failure during abort processing.

        Exceptions outside the handled failure types propagate to the caller.
        """
        try:
            self.logger.log_info(
                "[upload:abort:controller] Received upload abort request"
            )

            result = await self.service.abort_upload(
                dataset_id=(request.dataset_id),
                upload_id=request.upload_id,
                user_id=user_id,
            )
            response = UploadAbortResponseDTO(
                success=True,
                message="Upload abort processed successfully.",
                data=UploadAbortResponseDataDTO(**result),
            )

            self.logger.log_info(
                "[upload:abort:controller] Upload abort response created"
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response.model_dump(mode="json"),
            )

        except UploadAccessDeniedError:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "success": False,
                    "message": "You do not have access to this upload.",
                    "data": None,
                },
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
                    "message": "The upload initialization request is invalid.",
                    "data": None,
                },
            )
