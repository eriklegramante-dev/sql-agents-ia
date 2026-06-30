from app.routes.update.dtos.dto import (
    AgentPreferencesUpdateRequest,
    AgentPreferencesUpdateResponse,
    UpdatedAgentPreferencesData,
)
from app.routes.update.services.service import AgentPreferencesUpdateService


class AgentPreferencesUpdateController:
    """
    Controller layer responsible for handling the execution flow of agent preference updates.

    Acts as an intermediary that orchestrates the data flow by passing transport-layer
    inputs to the business service layer and shaping the returned raw domain structures
    into strict API response contracts (DTOs).

    Attributes:
        service (AgentPreferencesUpdateService): The business service layer instance.
    """

    def __init__(self, service: AgentPreferencesUpdateService = None) -> None:
        """
        Initializes the controller with optional service layer injection.

        Args:
            service (AgentPreferencesUpdateService, optional): Service handling preferences execution. Defaults to None.
        """
        self.service = service or AgentPreferencesUpdateService()

    def update_preferences(
        self, user_id: int, payload: AgentPreferencesUpdateRequest
    ) -> AgentPreferencesUpdateResponse:
        """
        Receives the sanitized payload, directs it to the business service layer,
        and shapes the repository output into a structured response contract.

        Args:
            user_id (int): The unique identifier of the user to update.
            payload (AgentPreferencesUpdateRequest): The validated data package from the request body.

        Returns:
            AgentPreferencesUpdateResponse: The structured API JSON response payload wrapper.
        """
        persisted_data = self.service.execute_update(user_id=user_id, payload=payload)

        data_response = UpdatedAgentPreferencesData(
            user_id=persisted_data["user_id"],
            persona_name=persisted_data["persona_name"],
            persona_description=persisted_data.get("persona_description"),
            response_style=persisted_data["response_style"],
            language=persisted_data["language"],
            default_dataset_scope=persisted_data.get("default_dataset_scope"),
            tool_preferences=persisted_data.get("tool_preferences", {}),
            guardrails=persisted_data.get("guardrails", {}),
            created_at=persisted_data["created_at"],
            updated_at=persisted_data["updated_at"],
        )

        return AgentPreferencesUpdateResponse(
            success=True,
            message="Agent preferences successfully updated.",
            data=data_response,
        )
