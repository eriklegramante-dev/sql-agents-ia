from typing import Optional, Dict, Any, Union
from datetime import datetime, timezone
import json
from app.agents.repository import AgentPreferencesRepository
from app.settings.setting import get_settings
from app.routes.agent_preferences.dtos.dto import UpdateAISettingsDTO, AISettingsResponse

class AgentPreferencesWorkflow:
    """
    Core business logic layer for managing agent and AI settings preferences.

    This workflow orchestrates the retrieval, validation, and updating of user 
    preferences, acting as the bridge between the service layer and the database repository.
    """

    def __init__(self, repository: Optional[AgentPreferencesRepository] = None):
        """
        Initializes the workflow with required dependencies.

        Args:
            repository (Optional[AgentPreferencesRepository]): The database repository 
                handling raw asynchronous SQL operations.
        """
        self.repository = repository
        self.settings = get_settings()

    def _validate_user_id(self, user_id_raw: Any) -> int:
        """
        Validates and converts a raw user identifier into a positive integer.

        Args:
            user_id_raw (Any): The incoming user identifier to be validated.

        Returns:
            int: The validated positive integer representing the user ID.

        Raises:
            ValueError: If the identifier cannot be cast to an integer or is <= 0.
        """
        try:
            user_id = int(user_id_raw)
            if user_id <= 0:
                raise ValueError()
            return user_id
        except (ValueError, TypeError):
            raise ValueError("The user identifier (user_id) provided is invalid.")

    async def execute(self, user_id_raw: Any) -> Dict[str, Any]:
        """
        Retrieves the complete agent preference profile for a given user.

        If no profile exists in the database, a default profile is generated 
        and returned based on the application's core settings.

        Args:
            user_id_raw (Any): The raw user identifier.

        Returns:
            Dict[str, Any]: A dictionary containing the user's full agent preferences.
        """
        user_id = self._validate_user_id(user_id_raw)
        preferences = await self.repository.find_by_user_id(user_id)

        if not preferences:
            preferences = self._get_default_preferences_profile(user_id)
        return preferences

    def _get_default_preferences_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Constructs a default agent preference profile using system baseline settings.

        Args:
            user_id (int): The validated user identifier.

        Returns:
            Dict[str, Any]: A dictionary populated with default agent behaviors, 
                guardrails, and tool preferences.
        """
        now = datetime.now(timezone.utc)
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

    async def get_ai_settings(self, user_id_raw: Any) -> AISettingsResponse:
        """
        Retrieves and formats the user's AI settings for the frontend interface.

        Fetches raw data from the repository, handles the deserialization of 
        JSONB fields (like response_styles), and structures the data into the 
        expected Pydantic response model.

        Args:
            user_id_raw (Any): The raw user identifier.

        Returns:
            AISettingsResponse: A validated model containing the AI settings state.
        """
        user_id = self._validate_user_id(user_id_raw)
        preferences = await self.repository.find_by_user_id(user_id)

        if not preferences:
            return AISettingsResponse(
                hasApiKey=False,
                persona=self.settings.agent.default_persona_name or "executive",
                model="gpt-5",
                temperature=0.5,
                responseStyles={}
            )

        raw_styles = preferences.get('response_styles', {})
        if isinstance(raw_styles, str):
            try:
                raw_styles = json.loads(raw_styles)
            except Exception:
                raw_styles = {}

        return AISettingsResponse(
            hasApiKey=bool(preferences.get('api_key')),
            persona=preferences.get('persona', 'executive'),
            model=preferences.get('model', 'gpt-5'),
            temperature=preferences.get('temperature', 0.5),
            responseStyles=raw_styles
        )

    async def update_ai_settings(self, user_id_raw: Any, payload: UpdateAISettingsDTO) -> AISettingsResponse:
        """
        Updates the user's AI settings and formats the updated record for the frontend.

        This method validates the incoming user identifier, delegates the persistence 
        of the new AI settings to the repository layer, and standardizes the output. 
        It explicitly handles the deserialization of PostgreSQL JSONB strings into 
        Python dictionaries to ensure strict compatibility with the response model.

        Args:
            user_id_raw (Any): The raw user identifier.
            payload (UpdateAISettingsDTO): The data transfer object containing the 
                new settings (persona, model, temperature, response styles, etc.) to apply.

        Returns:
            AISettingsResponse: A validated Pydantic model representing the updated 
                AI settings state, ready to be serialized and consumed by the frontend.
        """
        user_id = self._validate_user_id(user_id_raw)
        updated_preferences = await self.repository.update_ai_settings(user_id, payload)

        raw_styles = updated_preferences.get('response_styles', {})
        if isinstance(raw_styles, str):
            try:
                raw_styles = json.loads(raw_styles)
            except Exception:
                raw_styles = {}

        return AISettingsResponse(
            hasApiKey=bool(updated_preferences.get('api_key')),
            persona=updated_preferences.get('persona', 'executive'),
            model=updated_preferences.get('model', 'gpt-5'),
            temperature=updated_preferences.get('temperature', 0.5),
            responseStyles=raw_styles
        )