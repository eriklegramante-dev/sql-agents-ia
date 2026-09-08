import logging

from typing import Any, Optional
from fastapi import HTTPException, status
from app.routes.agent_preferences.services.service import AgentPreferencesService
from app.routes.agent_preferences.dtos.dto import (
    AgentPreferencesResponse,
    AgentPreferencesData,
    AISettingsResponse,     
    UpdateAISettingsDTO,    
)

logger = logging.getLogger(__name__)

class AgentPreferencesController:
    """
    Controller layer responsible for handling inbound agent preference operations.

    Orchestrates the data flow by invoking the service layer, catching core business
    exceptions, and structuralizing the output into standard response DTOs for both
    retrieval and update requests.
    """

    def __init__(self, service: Optional[AgentPreferencesService] = None):
        """
        Initializes the controller with its required service dependency.

        Args:
            service (Optional[AgentPreferencesService]): The service layer component handling
                business operations. Defaults to None, typically injected by the route handler.
        """
        self.service = service or AgentPreferencesService()

    async def handle_get_preferences(self, user_id_raw: Any) -> AgentPreferencesResponse:
        """
        Processes the request to retrieve agent preferences, handles exceptions, and envelopes the data.

        Args:
            user_id_raw (Any): The raw, unvalidated user identifier incoming from the route layer.

        Raises:
            HTTPException: 400 Bad Request if validation rules in the workflow fail.
            HTTPException: 500 Internal Server Error for any unhandled infrastructure or runtime exceptions.

        Returns:
            AgentPreferencesResponse: The standard enveloped API response containing validated data schemas.
        """
        try:
            raw_data = await self.service.get_user_preferences(user_id_raw)

            preferences_data = AgentPreferencesData.model_validate(raw_data)

            return AgentPreferencesResponse(
                success=True,
                message="Preferences retrieved successfully.",
                data=preferences_data,
            )

        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred while retrieving agent preferences.",
            )

    async def handle_get_ai_settings(self, user_id_raw: Any) -> AISettingsResponse:
        """
        Processes the request to retrieve AI settings specifically for the frontend interface.

        Args:
            user_id_raw (Any): The raw, unvalidated user identifier incoming from the route layer.

        Raises:
            HTTPException: 400 Bad Request if validation rules in the workflow fail.
            HTTPException: 500 Internal Server Error for any unhandled infrastructure or runtime exceptions.

        Returns:
            AISettingsResponse: The structured presentation data for AI settings.
        """
        try:
            return await self.service.get_ai_settings(user_id_raw)
            
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred while retrieving AI settings.",
            )

    async def handle_update_ai_settings(self, user_id_raw: Any, payload: UpdateAISettingsDTO) -> AISettingsResponse:
        """
        Processes the request to update AI settings and handles core validation exceptions.

        Args:
            user_id_raw (Any): The raw, unvalidated user identifier incoming from the route layer.
            payload (UpdateAISettingsDTO): The data transfer object containing the settings to update.

        Raises:
            HTTPException: 400 Bad Request if validation rules in the workflow fail.
            HTTPException: 500 Internal Server Error for any unhandled infrastructure or runtime exceptions.

        Returns:
            AISettingsResponse: The structured presentation data reflecting the updated AI settings.
        """
        try:
            return await self.service.update_ai_settings(user_id_raw, payload)
            
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
            )
        except Exception as e:
            logger.error(f"Failed to update AI settings for user {user_id_raw}: {repr(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred while updating AI settings."
            )