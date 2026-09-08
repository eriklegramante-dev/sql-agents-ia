from typing import Dict, Any, Optional
from app.core.agent_preferences.workflow import AgentPreferencesWorkflow
from ..dtos.dto import UpdateAISettingsDTO, AISettingsResponse

class AgentPreferencesService:
    """
    Service orchestration layer for the agent preferences module.

    Acts as a decoupling boundary layer between the web framework (FastAPI)
    and the pure core domain business rules (Workflow), propagating asynchronous execution.
    """

    def __init__(self, workflow: Optional[AgentPreferencesWorkflow] = None):
        """
        Initializes the service with its required workflow logic dependency.

        Args:
            workflow (Optional[AgentPreferencesWorkflow]): The core business workflow component.
        """
        self.workflow = workflow

    async def get_user_preferences(self, user_id_raw: Any) -> Dict[str, Any]:
        """
        Orchestrates the retrieval data flow by executing the core business workflow.

        Args:
            user_id_raw (Any): The incoming raw user identifier.

        Returns:
            Dict[str, Any]: Raw core preference attributes or fallback parameters.
        """
        return await self.workflow.execute(user_id_raw)

    async def get_ai_settings(self, user_id_raw: Any) -> AISettingsResponse:
        """
        Delegates the AI settings retrieval process for frontend integration.

        Args:
            user_id_raw (Any): The incoming raw user identifier.

        Returns:
            AISettingsResponse: The structured presentation data for AI settings.
        """
        return await self.workflow.get_ai_settings(user_id_raw)

    async def update_ai_settings(self, user_id_raw: Any, payload: UpdateAISettingsDTO) -> AISettingsResponse:
        """
        Delegates the AI settings update execution flow to the core workflow.

        Args:
            user_id_raw (Any): The incoming raw user identifier.
            payload (UpdateAISettingsDTO): The structured payload containing update intent.

        Returns:
            AISettingsResponse: The resulting structured data after the update completes.
        """
        return await self.workflow.update_ai_settings(user_id_raw, payload)