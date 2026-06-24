from typing import Dict, Any, Optional
from app.core.read.agent_preferences_workflow import AgentPreferencesWorkflow


class AgentPreferencesService:
    """
    Service orchestration layer for the agent preferences module.

    Acts as a decoupling boundary layer between the web framework (FastAPI)
    and the pure core domain business rules (Workflow).
    """

    def __init__(self, workflow: Optional[AgentPreferencesWorkflow] = None):
        """
        Initializes the service with its required workflow logic dependency.

        Args:
            workflow (Optional[AgentPreferencesWorkflow]): The core business workflow component.
                Defaults to a new instance of AgentPreferencesWorkflow.
        """
        self.workflow = workflow or AgentPreferencesWorkflow()

    def get_user_preferences(self, user_id_raw: Any) -> Dict[str, Any]:
        """
        Orchestrates the retrieval data flow by executing the responsible core business workflow.

        Args:
            user_id_raw (Any): The unvalidated raw user identifier incoming from the application layer.

        Returns:
            Dict[str, Any]: A dictionary containing raw core preference attributes or fallback parameters.
        """
        return self.workflow.execute(user_id_raw)
