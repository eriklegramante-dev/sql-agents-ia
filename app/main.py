from fastapi import FastAPI

from app.routes.router import api_router
from app.settings.app_config import app_config

app = FastAPI(
    title="SQL Agents IA",
    version="1.0.0",
    root_path=app_config.get_root_path(),
)

app.include_router(api_router)