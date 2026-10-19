from fastapi import APIRouter, Depends, status

from app.security.security import get_trusted_user_id
from app.chat.dependencies import get_chat_message_controller
from app.routes.chat.controllers.controller import ChatMessageController
from app.routes.chat.dtos.dto import (
    ChatMessageRequestDTO,
    ChatMessageResponseDTO,
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/message",
    response_model=ChatMessageResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Process a chat message.",
    description=(
        "Receives a user chat message, processes the request through the "
        "chat workflow, and returns the generated response together with "
        "any optional artifacts produced during execution."
    ),
)
async def send_chat_message(
    payload: ChatMessageRequestDTO,
    user_id: int = Depends(get_trusted_user_id),
    controller: ChatMessageController = Depends(
        get_chat_message_controller,
    ),
) -> ChatMessageResponseDTO:
    """
    Process a chat message using the trusted user identity.

    Receives the validated message payload and the user identifier
    provided by get_trusted_user_id, which requires the internal
    signature and a positive X-User-Id header. Delegates processing
    to the controller and returns the standardized chat response.

    The user identifier is not accepted in the request body.

    Args:
        payload (ChatMessageRequestDTO):
            Validated user message and optional dataset, session,
            and contextual metadata.

        user_id (int):
            User identifier forwarded by the trusted calling service
            after authenticating the user.

        controller (ChatMessageController):
            Injected controller responsible for coordinating
            chat message processing.

    Returns:
        ChatMessageResponseDTO:
            Standardized response containing the generated answer,
            detected intent, tool information, and optional artifact.
    """
    return await controller.execute(payload, user_id=user_id)
