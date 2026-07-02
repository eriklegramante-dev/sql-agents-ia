from fastapi import APIRouter, Path, Depends
from app.routes.update.dependencies.dependence import get_agent_preferences_update_controller
from app.routes.update.dtos.dto import (
    AgentPreferencesUpdateRequest,
    AgentPreferencesUpdateResponse,
)
from app.routes.update.controllers.controller import AgentPreferencesUpdateController

router = APIRouter(prefix="/api/v1", tags=["Agent Preferences"])


@router.put(
    "/{user_id}/preferences",
    response_model=AgentPreferencesUpdateResponse,
    summary="Create or update agent/persona preferences",
    description="Upserts user configuration profile for the AI agent behavior.",
)
def update_agent_preferences(
    payload: AgentPreferencesUpdateRequest,
    user_id: int = Path(..., description="The identifier of the user", gt=0),
    controller: AgentPreferencesUpdateController = Depends(
        get_agent_preferences_update_controller
    ),
) -> AgentPreferencesUpdateResponse:
    """
    Route handler for the update/upsert operation.
    Receives user_id path parameter and delegates processing downwards.

    Args:
        payload (AgentPreferencesUpdateRequest): The validated body payload parameters.
        user_id (int): The unique identifier extracted from the path. Must be > 0.
        controller (AgentPreferencesUpdateController): Injected controller instance handling coordination.

    Returns:
        AgentPreferencesUpdateResponse: Standard API response container with updated profile structure.
    """
    return controller.update_preferences(user_id=user_id, payload=payload)
