from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)