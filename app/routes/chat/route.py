from fastapi import APIRouter, Depends, status

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
    controller: ChatMessageController = Depends(
        get_chat_message_controller,
    ),
) -> ChatMessageResponseDTO:
    """
    Process a chat message.

    This route receives the validated chat request, delegates the business
    execution to the controller layer, and returns a standardized response
    containing the generated answer, detected intent, executed tool
    information, and any optional artifact produced during processing.

    Args:
        payload (ChatMessageRequestDTO):
            Validated request containing the user message and optional
            contextual information used during processing.

    Returns:
        ChatMessageResponseDTO:
            Standardized response containing the generated assistant
            response and execution metadata.
    """
    return await controller.execute(payload)
