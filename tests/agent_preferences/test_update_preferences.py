from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.core.agent_preferences.update.workflow import AgentPreferencesUpdateWorkflow


class TestAgentPreferencesUpdateWorkflow:
    @pytest.fixture
    def mock_repository(self):
        return MagicMock()

    @pytest.fixture
    def workflow(self, mock_repository):
        return AgentPreferencesUpdateWorkflow(repository=mock_repository)

    def test_update_success_creates_new_preferences_with_defaults(
        self, workflow, mock_repository
    ):
        mock_repository.get_by_user_id.return_value = None

        payload = {"persona_name": "Custom Assistant", "response_style": "technical"}

        result = workflow.execute(user_id=1, update_data=payload)

        assert result["user_id"] == 1
        assert result["persona_name"] == "Custom Assistant"
        assert result["response_style"] == "technical"
        assert result["language"] == "en"
        assert result["guardrails"]["allow_sql_generation"] is True
        mock_repository.upsert.assert_called_once()

    def test_update_success_preserves_omitted_fields(self, workflow, mock_repository):
        old_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_repository.get_by_user_id.return_value = {
            "user_id": 1,
            "persona_name": "Old Name",
            "response_style": "business",
            "language": "pt",
            "created_at": old_time,
            "updated_at": old_time,
        }

        payload = {"response_style": "detailed"}

        result = workflow.execute(user_id=1, update_data=payload)

        assert result["response_style"] == "detailed"
        assert result["persona_name"] == "Old Name"
        assert result["language"] == "pt"
        assert result["created_at"] == old_time
        assert result["updated_at"] > old_time
        mock_repository.upsert.assert_called_once()

    @pytest.mark.parametrize("invalid_id", [0, -1, -99])
    def test_validation_fails_with_invalid_user_id(self, workflow, invalid_id):
        payload = {"persona_name": "Valid Name"}

        with pytest.raises(HTTPException) as exc_info:
            workflow.execute(user_id=invalid_id, update_data=payload)

        assert exc_info.value.status_code == 400
        assert "Invalid user identifier" in exc_info.value.detail

    def test_validation_fails_with_empty_payload(self, workflow):
        with pytest.raises(HTTPException) as exc_info:
            workflow.execute(user_id=1, update_data={})

        assert exc_info.value.status_code == 400
        assert "Empty update payload" in exc_info.value.detail
