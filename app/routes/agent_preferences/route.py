from fastapi import APIRouter, Depends, status, Body
import asyncpg

from app.database.connection import get_db_pool 

from app.routes.agent_preferences.controllers.controller import AgentPreferencesController
from app.routes.agent_preferences.services.service import AgentPreferencesService
from app.core.agent_preferences.workflow import AgentPreferencesWorkflow
from app.agents.repository import AgentPreferencesRepository
from app.security.security import verify_signature

from app.routes.agent_preferences.dtos.dto import (
    AgentPreferencesRequest,
    AgentPreferencesResponse,
    AISettingsResponse,
    UpdateAISettingsDTO
)

router = APIRouter()

async def get_controller(pool: asyncpg.Pool = Depends(get_db_pool)) -> AgentPreferencesController:
    """
    Dependency injection factory.
    Instantiates the full architectural chain passing the asyncpg pool down to the repository.
    """
    repository = AgentPreferencesRepository(pool)
    workflow = AgentPreferencesWorkflow(repository)
    service = AgentPreferencesService(workflow)
    return AgentPreferencesController(service)

@router.get(
    "/{user_id}/preferences",
    response_model=AgentPreferencesResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieves the user's AI agent persona and behavior preferences.",
    dependencies=[Depends(verify_signature)],
)
async def get_agent_preferences(
    user_id: int, 
    request: AgentPreferencesRequest = Depends(),
    controller: AgentPreferencesController = Depends(get_controller)
):
    """
    Endpoint protected by header signature (X-Signature) to retrieve agent preferences.
    """
    return await controller.handle_get_preferences(request.user_id)


@router.get(
    "/{user_id}/ai-settings",
    response_model=AISettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieves the AI settings configured for the frontend UI.",
    dependencies=[Depends(verify_signature)],
)
async def get_ai_settings(
    user_id: int,
    controller: AgentPreferencesController = Depends(get_controller)
):
    """
    Retrieves specific AI preferences structured for the frontend settings page.
    Automatically masks the API Key in the response.
    """
    return await controller.handle_get_ai_settings(user_id)


@router.put(
    "/{user_id}/ai-settings",
    response_model=AISettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Updates the user's AI settings from the frontend UI.",
    dependencies=[Depends(verify_signature)],
)
async def update_ai_settings(
    user_id: int,
    payload: UpdateAISettingsDTO = Body(...),
    controller: AgentPreferencesController = Depends(get_controller)
):
    print("🚨 PAYLOAD RECEBIDO DO FRONTEND:", payload.dict(exclude_unset=True))
    """
    Updates specific AI settings. Includes security constraints to prevent 
    overwriting valid API keys with visual frontend mask strings.
    """
    return await controller.handle_update_ai_settings(user_id, payload)