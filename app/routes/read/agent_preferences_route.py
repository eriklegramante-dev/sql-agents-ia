from fastapi import APIRouter, Depends, status
from typing import Any
from app.routes.read.controllers.agent_preferences_controller import AgentPreferencesController
from app.routes.read.dtos.agent_preferences_dto import AgentPreferencesResponse


router = APIRouter(prefix="/agent", tags=["Agent Preferences"])


@router.get(
    "/{user_id}/preferences",
    response_model=AgentPreferencesResponse,
    status_code=status.HTTP_200_OK,
    summary="Recupera as preferências de persona e comportamento do agente de IA do usuário."
)
def get_agent_preferences(
    user_id: Any, 
):
    """
    Endpoint público/autenticado para carregar as configurações de comportamento da inteligência artificial.
    Se o usuário não possuir preferências customizadas, um perfil padrão (default) seguro será retornado.
    """
    controller = AgentPreferencesController()
    return controller.handle_get_preferences(user_id)