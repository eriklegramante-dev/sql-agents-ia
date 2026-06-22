from typing import Optional, Dict, Any
from datetime import datetime, UTC
from app.agents.agent_preferences_repository import AgentPreferencesRepository
from app.settings.setting import get_settings  

class AgentPreferencesWorkflow:
    """
    O coração da regra de negócio. Responsável por validar regras de acesso,
    identificadores e aplicar a lógica de perfil padrão (fallback).
    """

    def __init__(self, repository: Optional[AgentPreferencesRepository] = None):
        self.repository = repository or AgentPreferencesRepository()
        self.settings = get_settings()

    def execute(self, user_id_raw: Any) -> Dict[str, Any]:
        """
        Executa a lógica de negócio para recuperação das preferências do agente.
        """
        try:
            user_id = int(user_id_raw)
            if user_id <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("O identificador do usuário (user_id) fornecido é inválido.")

        preferences = self.repository.find_by_user_id(user_id)

        if not preferences:
            preferences = self._get_default_preferences_profile(user_id)

        return preferences

    def _get_default_preferences_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Retorna um perfil de preferências padrão seguro puxado diretamente
        das configurações do sistema (settings).
        """
        now = datetime.now(UTC)
        
        return {
            "user_id": user_id,
            "persona_name": self.settings.agent.default_persona_name,
            "persona_description": self.settings.agent.default_persona_description,
            "response_style": self.settings.agent.default_response_style,
            "language": self.settings.agent.default_language,
            "default_dataset_scope": "public",
            "tool_preferences": ["execute_sql"],
            "guardrails": ["block_sensitive_data"],
            "created_at": now,
            "updated_at": now
        }