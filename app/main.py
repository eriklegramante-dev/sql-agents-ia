from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings.setting import get_settings
from app.routes.router import api_router
from app.settings.app_config import app_config
from app.settings.setting import get_settings

settings = get_settings()

settings = get_settings()

app = FastAPI(
    title="SQL Agents IA",
    version="1.0.0",
    root_path=app_config.get_root_path(),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
