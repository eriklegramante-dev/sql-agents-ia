from fastapi import APIRouter, Depends, status
from typing import Any
from app.routes.read.controllers.agent_preferences_controller import AgentPreferencesController
from app.routes.read.dtos.agent_preferences_dto import AgentPreferencesResponse
from app.security.security import verify_signature

router = APIRouter(prefix="/agent", tags=["Agent Preferences"])

@router.get(
    "/{user_id}/preferences",
    response_model=AgentPreferencesResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieves the user's AI agent persona and behavior preferences.",
    dependencies=[Depends(verify_signature)]
)
def get_agent_preferences(user_id: Any):
    """
    Endpoint protected by header signature (X-Signature). Retrieve agent settings or revert
    to the secure default profile if no customizations exist.
    """
    controller = AgentPreferencesController()
    return controller.handle_get_preferences(user_id)