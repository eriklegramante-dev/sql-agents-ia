from app.routes.update.dtos.dto import AgentPreferencesUpdateRequest
from app.core.agent_preferences.update.workflow import AgentPreferencesUpdateWorkflow


class AgentPreferencesUpdateService:
    """
    Service layer responsible for architectural isolation.
    
    Acts as a boundary between the HTTP transport layer (FastAPI) and the core 
    business logic (Workflow), ensuring that data payloads are mapped into pure 
    Python structures before deep execution.
    """
    
    def __init__(self, workflow: AgentPreferencesUpdateWorkflow = None):
        self.workflow = workflow or AgentPreferencesUpdateWorkflow()

    def execute_update(self, user_id: int, payload: AgentPreferencesUpdateRequest):
        """
        Acts as an architectural isolation layer. Dispatches input data into
        the core engine workflow, completely abstracted from HTTP constraints.
        """
        update_data = payload.model_dump(exclude_unset=True)

        return self.workflow.execute(user_id=user_id, update_data=update_data)
