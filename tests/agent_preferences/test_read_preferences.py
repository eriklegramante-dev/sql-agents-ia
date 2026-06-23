import pytest
from app.core.read.agent_preferences_workflow import AgentPreferencesWorkflow

class TestAgentPreferencesRead:
    """
    Unit test suite to validate the reading flow of agent preferences through Workflow.
    """

    def test_retrieval_success_with_existing_preferences(self, mock_repository):
        """
        Scenario: The user has custom preferences saved in the database.
        Expected: The system should return the exact data from the database.
        """
        workflow = AgentPreferencesWorkflow(repository=mock_repository)
        
        result = workflow.execute(1)
        
        assert result is not None
        assert result["user_id"] == 1
        assert result["persona_name"] == "Sênior"
        assert result["response_style"] == "direct and technical"

    def test_fallback_to_default_profile_when_preferences_missing(self, mock_repository):
            """
            Scenario: The user exists, but has no saved custom preferences.
            Expected: The system should activate the Golden Rule and revert to the default profile from the settings.
            """
            from app.settings.setting import get_settings
            settings = get_settings()
            
            workflow = AgentPreferencesWorkflow(repository=mock_repository)
            
            result = workflow.execute(99)
            
            assert result is not None
            assert result["user_id"] == 99
            assert result["persona_name"] == settings.agent.default_persona_name  
            assert result["language"] == settings.agent.default_language     
            assert "execute_sql" in result["tool_preferences"]

    @pytest.mark.parametrize("invalid_id", ["abc", -5, 0, None])
    def test_validation_fails_with_invalid_user_id(self, mock_repository, invalid_id):
        """
        Scenario: The provided user_id format is invalid (letters, negative, zero, or null).
        Expected: The Workflow should throw a ValueError preventing the flow from progressing.
        """
        workflow = AgentPreferencesWorkflow(repository=mock_repository)
        
        with pytest.raises(ValueError) as exc_info:
            workflow.execute(invalid_id)
            
        assert "The user identifier (user_id) provided is invalid." in str(exc_info.value)