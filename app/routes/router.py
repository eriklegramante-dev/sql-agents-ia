from fastapi import APIRouter

from app.routes.agent_preferences.route import (
    router as agent_preferences_router,
)
from app.routes.prepare.route import router as prepare_router
from app.routes.analysis.route import router as analysis_router
from app.routes.schema.route import router as schema_router
from app.routes.update.route import router as update_router
from app.routes.uploads.route import router as uploads_router
from app.routes.profiling.route import router as profiling_router
from app.routes.preview.route import router as preview_router
from app.routes.chat.route import router as chat_router
from app.routes.datasets.route import router as datasets_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(
    uploads_router,
    tags=["Uploads"],
)

api_router.include_router(
    agent_preferences_router,
    tags=["Agent Preferences"],
)

api_router.include_router(update_router)

api_router.include_router(
    prepare_router,
    tags=["Datasets"],
)

api_router.include_router(
    schema_router,
    tags=["Schema"],
)

api_router.include_router(profiling_router, tags=["Profiling"])

api_router.include_router(
    datasets_router,
    tags=["Datasets"],
)

api_router.include_router(
    preview_router,
    tags=["Preview"],
)

api_router.include_router(
    analysis_router,
    tags=["Analysis"],
)

api_router.include_router(chat_router)
