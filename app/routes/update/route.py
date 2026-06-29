from fastapi import APIRouter, status, Path
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
):
    """
    Route handler for the update/upsert operation.
    Receives user_id path parameter and delegates processing downwards.
    """
    controller = AgentPreferencesUpdateController()
    return controller.update_preferences(user_id=user_id, payload=payload)
