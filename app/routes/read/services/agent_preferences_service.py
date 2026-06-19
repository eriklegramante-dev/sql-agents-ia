from typing import Dict, Any, Optional
from app.core.read.agent_preferences_workflow import AgentPreferencesWorkflow


class AgentPreferencesService:
    """
    Camada de serviço orquestradora para o módulo de preferências do agente.
    Atua como um desacoplador entre o framework web (FastAPI) e as regras de negócio puras (Workflow).
    """

    def __init__(self, workflow: Optional[AgentPreferencesWorkflow] = None):
        self.workflow = workflow or AgentPreferencesWorkflow()

    def get_user_preferences(self, user_id_raw: Any) -> Dict[str, Any]:
        """
        Orquestra o fluxo de recuperação das preferências chamando o workflow responsável.
        """
        return self.workflow.execute(user_id_raw)