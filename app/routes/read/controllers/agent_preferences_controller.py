from typing import Any, Optional
from fastapi import HTTPException, status
from app.routes.read.services.agent_preferences_service import AgentPreferencesService
from app.routes.read.dtos.agent_preferences_dto import (
    AgentPreferencesResponse,
    AgentPreferencesData,
)


class AgentPreferencesController:
    """
    Controller layer responsible for handling inbound agent preference read requests.

    Orchestrates the data flow by invoking the service layer, catching core business
    exceptions, and structuralizing the output into standard response DTOs.
    """

    def __init__(self, service: Optional[AgentPreferencesService] = None):
        """
        Initializes the controller with its required service dependency.

        Args:
            service (Optional[AgentPreferencesService]): The service layer component handling
                business operations. Defaults to a new instance of AgentPreferencesService.
        """
        self.service = service or AgentPreferencesService()

    def handle_get_preferences(self, user_id_raw: Any) -> AgentPreferencesResponse:
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
            raw_data = self.service.get_user_preferences(user_id_raw)

            # Pydantic V2 standard parsing method
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
