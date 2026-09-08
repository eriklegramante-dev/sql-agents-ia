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
        Updates the user's AI settings and formats the updated record for the frontend.

        This method validates the incoming user identifier, delegates the persistence 
        of the new AI settings to the repository layer, and standardizes the output. 
        It explicitly handles the deserialization of PostgreSQL JSONB strings into 
        Python dictionaries to ensure strict compatibility with the response model.

        Args:
            user_id_raw (Any): The raw user identifier to be validated and converted to an integer.
            payload (UpdateAISettingsDTO): The data transfer object containing the 
                new settings (persona, model, temperature, response styles, etc.) to apply.

        Returns:
            AISettingsResponse: A validated Pydantic model representing the updated 
                AI settings state, ready to be serialized and consumed by the frontend.

        Raises:
            ValueError: If the provided `user_id_raw` fails validation (e.g., non-integer or <= 0).
        """
        print(f"\n🚨 [RAIO-X 1] INICIANDO SALVAMENTO PARA USER_ID: {user_id}")
        print(f"🚨 [RAIO-X 2] DADOS RECEBIDOS (PAYLOAD): {payload.dict(exclude_unset=True)}")

        current = await self.find_by_user_id(user_id)
        print(f"🚨 [RAIO-X 3] DADOS ATUAIS NO BANCO ANTES DO UPDATE: {current}")
        
        p_api_key = getattr(payload, 'api_key', getattr(payload, 'apiKey', None))
        p_persona = getattr(payload, 'persona', None)
        p_model = getattr(payload, 'model', None)
        p_temperature = getattr(payload, 'temperature', None)
        p_response_styles = getattr(payload, 'response_styles', getattr(payload, 'responseStyles', None))

        api_key = current.get("api_key") if current else None
        if p_api_key and p_api_key != "••••••••":
            api_key = p_api_key

        persona = p_persona if p_persona is not None else (current.get("persona") if current else "executive")
        model = p_model if p_model is not None else (current.get("model") if current else "gpt-5")
        temperature = p_temperature if p_temperature is not None else (current.get("temperature") if current else 0.5)
        
        current_styles = current.get("response_styles") if current else {}
        if isinstance(current_styles, str):
            try:
                current_styles = json.loads(current_styles)
            except Exception:
                current_styles = {}
                
        response_styles = p_response_styles if p_response_styles is not None else current_styles

        print(f"🚨 [RAIO-X 4] VARIÁVEIS PRONTAS PARA O SQL -> Model: {model}, Persona: {persona}")

        query = """
            INSERT INTO agent_preferences (user_id, api_key, persona, model, temperature, response_styles)
            VALUES ($1, $2, $3, $4, $5, CAST($6 AS jsonb))
            ON CONFLICT (user_id) DO UPDATE SET
                api_key = EXCLUDED.api_key,
                persona = EXCLUDED.persona,
                model = EXCLUDED.model,
                temperature = EXCLUDED.temperature,
                response_styles = EXCLUDED.response_styles,
                updated_at = CURRENT_TIMESTAMP
            RETURNING *;
        """

        try:
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
                print(f"🚨 [RAIO-X 5] SUCESSO! GRAVOU NO BANCO: {dict(record) if record else 'FALHOU/VAZIO'}")
                return dict(record) if record else {}
        except Exception as e:
            print(f"🚨 [RAIO-X 6] ERRO FATAL AO GRAVAR NO BANCO: {str(e)}")
            raise e