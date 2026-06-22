import pytest
from datetime import datetime
from typing import Optional, Dict, Any
from app.agents.agent_preferences_repository import AgentPreferencesRepository

class MockAgentPreferencesRepository(AgentPreferencesRepository):
    def __init__(self):
        self._mock_db = {
            1: {
                "user_id": 1,
                "persona_name": "Sênior",
                "persona_description": "Agente focado em análise de segurança e infraestrutura.",
                "response_style": "direto e técnico",
                "language": "pt-BR",
                "default_dataset_scope": "production_logs",
                "tool_preferences": ["execute_sql"],
                "guardrails": ["block_sensitive_data"],
                "created_at": datetime.fromisoformat("2026-04-10T10:00:00"),
                "updated_at": datetime.fromisoformat("2026-06-18T15:00:00")
            }
        }

    def find_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self._mock_db.get(user_id)

@pytest.fixture
def mock_repository():
    """Fixture que fornece o repositório simulado para os testes."""
    return MockAgentPreferencesRepository()