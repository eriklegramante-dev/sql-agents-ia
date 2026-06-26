from fastapi import APIRouter

from app.routes.agent_preferences.route import router as agent_preferences_router
from app.routes.uploads.route import router as uploads_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(uploads_router)
api_router.include_router(
    agent_preferences_router,
    tags=["Agent Preferences"],
)