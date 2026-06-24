from fastapi import APIRouter

from app.routes.agent_preferences.route import router as agent_preferences_router


api_router = APIRouter()


api_router.include_router(
    agent_preferences_router, 
    prefix="/api/v1", 
    tags=["Agent Preferences"]
)