import pytest
from app.core.agent_preferences.workflow import AgentPreferencesWorkflow
from app.settings.setting import get_settings


class TestAgentPreferencesRead:
    async def test_retrieval_success_with_existing_preferences(self, mock_repository):
        workflow = AgentPreferencesWorkflow(repository=mock_repository)

        result = await workflow.execute(1)

        assert result is not None
        assert result["user_id"] == 1
        assert result["persona_name"] == "Sênior"
        assert result["response_style"] == "direct and technical"

    async def test_fallback_to_default_profile_when_preferences_missing(
        self, mock_repository
    ):
        settings = get_settings()
        workflow = AgentPreferencesWorkflow(repository=mock_repository)

        result = await workflow.execute(99)

        assert result is not None
        assert result["user_id"] == 99
        assert result["persona_name"] == settings.agent.default_persona_name
        assert result["language"] == settings.agent.default_language
        assert "execute_sql" in result["tool_preferences"]

    @pytest.mark.parametrize("invalid_id", ["abc", -5, 0, None, "1 OR 1=1"])
    async def test_validation_fails_with_invalid_user_id(self, mock_repository, invalid_id):
        workflow = AgentPreferencesWorkflow(repository=mock_repository)

        with pytest.raises(ValueError) as exc_info:
            await workflow.execute(invalid_id)

        assert "The user identifier (user_id) provided is invalid." in str(
            exc_info.value
        )
