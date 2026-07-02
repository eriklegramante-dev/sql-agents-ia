from fastapi import APIRouter

from app.routes.datasets.router import router as datasets_router

router = APIRouter()

router.include_router(datasets_router, prefix="/api/v1")
