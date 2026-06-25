from fastapi import FastAPI
from app.routes.router import api_router
from app.settings.app_config import AppConfig


config = AppConfig()

app = FastAPI(
    title="User Management API",
    description="REST API for secure identity management, operational data access, and reliable service integration.",
    openapi_url=f"{config.get_root_path()}/openapi.json",
    version="1.0.0",
    root_path=config.get_root_path(),
)

app.include_router(api_router)
