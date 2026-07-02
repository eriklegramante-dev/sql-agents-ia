from fastapi import APIRouter

from app.routes.agent_preferences.route import router as agent_preferences_router
from app.routes.update.route import router as update_router
from app.routes.prepare.route import router as prepare_router
from app.routes.schema.route import router as schema_router


api_router = APIRouter()

api_router.include_router(
    agent_preferences_router,
    prefix="/api/v1",
    tags=["Agent Preferences"],
)

api_router.include_router(update_router)

api_router.include_router(
    prepare_router,
    prefix="/api/v1",
    tags=["Datasets"],
)

api_router.include_router(
    schema_router,
    prefix="/api/v1",
    tags=["Schema"],
)