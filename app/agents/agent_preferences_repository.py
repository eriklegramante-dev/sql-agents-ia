from typing import Optional, Dict, Any
from datetime import datetime

class AgentPreferencesRepository:
    """
    Responsável direta pelo acesso aos dados persistidos das preferências do agente.
    Isola a lógica de queries SQL do restante da aplicação.
    """

    def __init__(self):
        self._mock_db: Dict[int, Dict[str, Any]] = {
            1: {
                "user_id": 1,
                "persona_name": "Default",
                "persona_description": "Agente focado em análise de segurança, criptografia e infraestrutura Linux.",
                "response_style": "direto e técnico",
                "language": "pt-BR",
                "default_dataset_scope": "production_logs",
                "tool_preferences": ["execute_sql", "network_recon"],
                "guardrails": ["block_sensitive_data", "restrict_pii"],
                "created_at": datetime.fromisoformat("2026-04-10T10:00:00"),
                "updated_at": datetime.fromisoformat("2026-06-18T15:00:00")
            }
        }

    def find_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca as preferências de um agente no banco de dados pelo ID do usuário.
        Retorna um dicionário com os dados brutos ou None se não encontrar.
        """
        return self._mock_db.get(user_id)