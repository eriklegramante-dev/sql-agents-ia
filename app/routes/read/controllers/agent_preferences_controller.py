from typing import Any, Optional
from fastapi import HTTPException, status
from app.routes.read.services.agent_preferences_service import AgentPreferencesService
from app.routes.read.dtos.agent_preferences_dto import AgentPreferencesResponse, AgentPreferencesData

class AgentPreferencesController:
    """
    The controller layer is responsible for receiving read requests,
    triggering the service layer, and formatting the data output according to the standard DTO.
    """

    def __init__(self, service: Optional[AgentPreferencesService] = None):
        self.service = service or AgentPreferencesService()

    def handle_get_preferences(self, user_id_raw: Any) -> AgentPreferencesResponse:
        """
        It handles the preference search request, catches validation errors,
        and builds the enveloped success response.
        """
        try:
            raw_data = self.service.get_user_preferences(user_id_raw)
            
            preferences_data = AgentPreferencesData.from_orm(raw_data) if hasattr(AgentPreferencesData, "from_orm") else AgentPreferencesData(**raw_data)
            
            return AgentPreferencesResponse(
                success=True,
                message="Preferences retrieved successfully.",
                data=preferences_data
            )
            
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err)
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred while retrieving agent preferences."
            )