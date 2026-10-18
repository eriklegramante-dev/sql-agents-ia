from fastapi import HTTPException

from app.logs.setup_logger import LoggerManager
from app.prepare.exceptions import AppException
from app.routes.chat.dtos.dto import (
    ChatMessageRequestDTO,
    ChatMessageResponseDTO,
)
from app.routes.chat.services.service import ChatMessageService


class ChatMessageController:
    """
    Coordinates HTTP-level chat message request processing.

    This controller acts as the entry point between the FastAPI route and the
    chat application service. It delegates validated requests to the service,
    wraps successful results in the standard response structure, and converts
    predictable application exceptions into HTTP responses.

    Unexpected failures propagate to the ASGI error handler. Only application
    exceptions are translated into a standardized response by this controller.

    The controller contains no business rules, intent classification,
    persistence logic, assistant integration, analytical query execution, or
    chart-generation behavior.

    Dependencies are received through constructor injection, preventing the
    controller from instantiating its own service or logging implementation.

    Args:
        service:
            Application service responsible for coordinating the chat message
            execution flow.

        logger:
            Logger manager used to record controller execution events
            and unexpected failures.

    Attributes:
        service:
            Application service responsible for coordinating the chat message
            execution flow.

        logger:
            Logger manager used to record controller execution events and
            unexpected failures.
    """

    def __init__(
        self,
        service: ChatMessageService,
        logger: LoggerManager,
    ) -> None:
        self._service = service
        self._logger = logger

    async def execute(
        self,
        request: ChatMessageRequestDTO,
        *,
        user_id: int,
    ) -> ChatMessageResponseDTO:
        """
        Execute HTTP-level chat message processing.

        Args:
            request:
                Validated chat message request received from the route.
            user_id:
                Trusted caller identity supplied by the route dependency.

        Returns:
            Standardized response envelope containing the processed chat
            message result.

        Raises:
            HTTPException: With the original status for application failures.

        Unexpected exceptions propagate to the ASGI error handler.
        """
        try:
            self._logger.log_info(
                f"Starting chat message controller for user " f"{user_id}."
            )

            response_data = await self._service.execute(request, user_id=user_id)

            self._logger.log_info(
                f"Chat message controller completed for user " f"{user_id}."
            )

            return ChatMessageResponseDTO(
                success=True,
                message="Chat message processed successfully.",
                data=response_data,
                errors=None,
            )

        except AppException as error:
            self._logger.log_warning(f"Chat message processing failed: {error.message}")

            raise HTTPException(
                status_code=error.status_code,
                detail={
                    "success": False,
                    "message": error.message,
                    "data": None,
                    "errors": error.details,
                },
            ) from error
