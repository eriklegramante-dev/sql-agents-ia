from app.routes.update.controllers.controller import AgentPreferencesUpdateController
from app.routes.update.services.service import AgentPreferencesUpdateService


def get_agent_preferences_update_controller() -> AgentPreferencesUpdateController:
    """Builds the agent preferences update controller dependency.

    Creates the controller with its service dependency already configured,
    keeping the route layer focused only on request handling and response
    delegation.
    """

    service = AgentPreferencesUpdateService()
    return AgentPreferencesUpdateController(service)