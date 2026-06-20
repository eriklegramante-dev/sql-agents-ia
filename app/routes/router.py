from fastapi import APIRouter

from app.routes.uploads.route import router as uploads_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(uploads_router)