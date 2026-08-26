from fastapi import APIRouter, Path, Depends

from app.routes.update.controllers.controller import AgentPreferencesUpdateController
from app.routes.update.dependencies.dependence import (
    get_agent_preferences_update_controller,
)
from app.routes.update.dtos.dto import (
    AgentPreferencesUpdateRequest,
    AgentPreferencesUpdateResponse,
)

router = APIRouter(tags=["Agent Preferences"])


@router.put(
    "/{user_id}/preferences",
    response_model=AgentPreferencesUpdateResponse,
    summary="Create or update agent preferences.",
    description=(
        "Creates a new agent preference profile when one does not exist "
        "or updates the existing configuration for the specified user."
    ),
)
def update_agent_preferences(
    payload: AgentPreferencesUpdateRequest,
    user_id: int = Path(..., description="The identifier of the user", gt=0),
    controller: AgentPreferencesUpdateController = Depends(
        get_agent_preferences_update_controller
    ),
) -> AgentPreferencesUpdateResponse:
    """
    Create or update an agent preferences profile.

    This route receives the validated request payload together with the
    target user identifier, delegates the business execution to the
    controller layer, and returns a standardized response describing the
    persisted agent preferences.

    Args:
        payload (AgentPreferencesUpdateRequest):
            Validated request containing the agent preference configuration.
        user_id (int):
            Unique identifier of the user whose preferences will be created
            or updated.

    Returns:
        AgentPreferencesUpdateResponse:
            Standardized response containing the persisted agent
            preferences after the operation completes successfully.
    """
    controller = AgentPreferencesUpdateController()

    return controller.update_preferences(
        user_id=user_id,
        payload=payload,
    )
