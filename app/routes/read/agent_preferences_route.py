from fastapi import APIRouter, Depends, status
from typing import Any
from app.routes.read.controllers.agent_preferences_controller import AgentPreferencesController
from app.routes.read.dtos.agent_preferences_dto import AgentPreferencesResponse
from app.security.security import verify_signature

router = APIRouter(prefix="/agent", tags=["Agent Preferences"])

@router.get(
    "/{user_id}/preferences",
    response_model=AgentPreferencesResponse,
    status_code=status.HTTP_200_OK,
    summary="Recupera as preferências de persona e comportamento do agente de IA do usuário.",
    dependencies=[Depends(verify_signature)]
)
def get_agent_preferences(user_id: Any):
    """
    Endpoint protegido por assinatura de cabeçalho (X-Signature).
    Recupera as configurações do agente ou retorna o perfil padrão seguro caso não existam customizações.
    """
    controller = AgentPreferencesController()
    return controller.handle_get_preferences(user_id)