from typing import Optional, Dict, Any, Union
from datetime import datetime, timezone
from app.agents.repository import AgentPreferencesRepository
from app.settings.setting import get_settings
from app.routes.agent_preferences.dtos.dto import UpdateAISettingsDTO, AISettingsResponse

class AgentPreferencesWorkflow:
    def __init__(self, repository: Optional[AgentPreferencesRepository] = None):
        self.repository = repository
        self.settings = get_settings()

    def _validate_user_id(self, user_id_raw: Any) -> int:
        try:
            user_id = int(user_id_raw)
            if user_id <= 0:
                raise ValueError()
            return user_id
        except (ValueError, TypeError):
            raise ValueError("The user identifier (user_id) provided is invalid.")

    async def execute(self, user_id_raw: Any) -> Dict[str, Any]:
        user_id = self._validate_user_id(user_id_raw)
        preferences = await self.repository.find_by_user_id(user_id)

        if not preferences:
            preferences = self._get_default_preferences_profile(user_id)
        return preferences

    def _get_default_preferences_profile(self, user_id: int) -> Dict[str, Any]:
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

        return AISettingsResponse(
            hasApiKey=bool(getattr(preferences, 'api_key', None)),
            persona=getattr(preferences, 'persona', 'executive'),
            model=getattr(preferences, 'model', 'gpt-5'),
            temperature=getattr(preferences, 'temperature', 0.5),
            responseStyles=getattr(preferences, 'response_styles', {}) or {}
        )

    async def update_ai_settings(self, user_id_raw: Any, payload: UpdateAISettingsDTO) -> AISettingsResponse:
        user_id = self._validate_user_id(user_id_raw)
        updated_preferences = await self.repository.update_ai_settings(user_id, payload)

        return AISettingsResponse(
            hasApiKey=bool(getattr(updated_preferences, 'api_key', None)),
            persona=getattr(updated_preferences, 'persona', 'executive'),
            model=getattr(updated_preferences, 'model', 'gpt-5'),
            temperature=getattr(updated_preferences, 'temperature', 0.5),
            responseStyles=getattr(updated_preferences, 'response_styles', {}) or {}
        )