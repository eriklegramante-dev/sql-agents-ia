from typing import Optional, Dict, Any
from datetime import datetime, UTC
from app.agents.agent_preferences_repository import AgentPreferencesRepository
from app.settings.setting import get_settings


class AgentPreferencesWorkflow:
    """
    The core of the business domain logic for agent preferences.

    Responsible for validating incoming identifiers, orchestrating database lookups,
    and applying fallback defaults from application settings when profile data is missing.
    """

    def __init__(self, repository: Optional[AgentPreferencesRepository] = None):
        """
        Initializes the workflow with required dependencies.

        Args:
            repository (Optional[AgentPreferencesRepository]): The data persistence layer component.
                Defaults to a new instance of AgentPreferencesRepository.
        """
        self.repository = repository or AgentPreferencesRepository()
        self.settings = get_settings()

    def execute(self, user_id_raw: Any) -> Dict[str, Any]:
        """
        Executes the business logic orchestration to retrieve agent preferences.

        Args:
            user_id_raw (Any): The unvalidated raw user identifier incoming from the application layer.

        Raises:
            ValueError: If the user_id cannot be converted to an integer or is less than or equal to zero.

        Returns:
            Dict[str, Any]: A dictionary containing the user's custom agent preferences,
                or a dynamic default profile fallback.
        """
        try:
            user_id = int(user_id_raw)
            if user_id <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("The user identifier (user_id) provided is invalid.")

        preferences = self.repository.find_by_user_id(user_id)

        if not preferences:
            preferences = self._get_default_preferences_profile(user_id)

        return preferences

    def _get_default_preferences_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Generates a secure default preference profile dynamically loaded from system settings.

        Args:
            user_id (int): The validated unique integer identifier of the user.

        Returns:
            Dict[str, Any]: A dictionary containing standard persona configurations, fallback parameters,
                and precise timezone-aware creation timestamps.
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
            "updated_at": now,
        }
