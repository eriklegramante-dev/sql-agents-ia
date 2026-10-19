import pytest
from datetime import datetime
from typing import Optional, Dict, Any
from app.agents.repository import AgentPreferencesRepository


class MockAgentPreferencesRepository(AgentPreferencesRepository):
    def __init__(self):
        self._mock_db = {
            1: {
                "user_id": 1,
                "persona_name": "Sênior",
                "persona_description": "Agent focused on security and infrastructure analysis.",
                "response_style": "direct and technical",
                "language": "pt-BR",
                "default_dataset_scope": "production_logs",
                "tool_preferences": ["execute_sql"],
                "guardrails": ["block_sensitive_data"],
                "created_at": datetime.fromisoformat("2026-04-10T10:00:00"),
                "updated_at": datetime.fromisoformat("2026-06-18T15:00:00"),
            }
        }

    async def find_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self._mock_db.get(user_id)


@pytest.fixture
def mock_repository():
    """Fixture provides the simulated repository for testing."""
    return MockAgentPreferencesRepository()
