from fastapi import APIRouter, Depends, status
from app.routes.read.controllers.agent_preferences_controller import (
    AgentPreferencesController,
)
from app.routes.read.dtos.agent_preferences_dto import AgentPreferencesResponse
from app.security.security import verify_signature
from app.routes.read.dtos.agent_preferences_dto import AgentPreferencesRequest

router = APIRouter(prefix="/agent", tags=["Agent Preferences"])


@router.get(
    "/{user_id}/preferences",
    response_model=AgentPreferencesResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieves the user's AI agent persona and behavior preferences.",
    dependencies=[Depends(verify_signature)],
)
def get_agent_preferences(user_id: int, request: AgentPreferencesRequest = Depends()):
    """
    Endpoint protected by header signature (X-Signature) to retrieve agent preferences.

    Args:
        user_id (int): The unique integer identifier of the user.

    Returns:
        AgentPreferencesResponse: The standard enveloped response containing preference data.
    """
    controller = AgentPreferencesController()
    return controller.handle_get_preferences(user_id)
