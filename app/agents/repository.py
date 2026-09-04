import json
import asyncpg
from typing import Optional, Dict, Any
from app.routes.agent_preferences.dtos.dto import UpdateAISettingsDTO

class AgentPreferencesRepository:
    """
    Repository class responsible for accessing the persisted agent preferences data.

    This layer isolates infrastructure and raw asynchronous SQL query logic from the 
    core business domain, utilizing asyncpg for high-performance database operations.
    """

    def __init__(self, pool: asyncpg.Pool):
        """
        Initializes the repository with a database connection pool.

        Args:
            pool (asyncpg.Pool): The shared asynchronous PostgreSQL connection pool.
        """
        self.pool = pool

    async def find_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Searches for an agent's preferences profile in the database by user ID.

        Args:
            user_id (int): The validated unique integer identifier of the user.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing raw preference records 
                if found, otherwise None.
        """
        query = "SELECT * FROM agent_preferences WHERE user_id = $1"
        
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, user_id)
            if record:
                return dict(record)
            return None

    async def update_ai_settings(self, user_id: int, payload: UpdateAISettingsDTO) -> Dict[str, Any]:
        """
        Persists the AI settings updates to the database using an UPSERT strategy.

        Applies security constraints to ensure API keys are not overwritten by 
        masked values originating from the frontend interface.

        Args:
            user_id (int): The validated unique integer identifier of the user.
            payload (UpdateAISettingsDTO): The data transfer object containing the settings to update.

        Returns:
            Dict[str, Any]: A dictionary representing the updated database record.
        """
        current = await self.find_by_user_id(user_id)
        
        api_key = current.get("api_key") if current else None
        if payload.apiKey and payload.apiKey != "••••••••":
            api_key = payload.apiKey

        persona = payload.persona if payload.persona is not None else (current.get("persona") if current else "executive")
        model = payload.model if payload.model is not None else (current.get("model") if current else "gpt-5")
        temperature = payload.temperature if payload.temperature is not None else (current.get("temperature") if current else 0.5)
        
        response_styles = payload.responseStyles if payload.responseStyles is not None else (
            json.loads(current.get("response_styles", "{}")) if current and current.get("response_styles") else {}
        )

        query = """
            INSERT INTO agent_preferences (user_id, api_key, persona, model, temperature, response_styles)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE SET
                api_key = EXCLUDED.api_key,
                persona = EXCLUDED.persona,
                model = EXCLUDED.model,
                temperature = EXCLUDED.temperature,
                response_styles = EXCLUDED.response_styles,
                updated_at = CURRENT_TIMESTAMP
            RETURNING *;
        """

        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                query, 
                user_id, 
                api_key, 
                persona, 
                model, 
                temperature, 
                json.dumps(response_styles)
            )
            return dict(record)