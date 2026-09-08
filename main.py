from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.router import api_router
from app.settings.setting import get_settings

settings = get_settings()

app = FastAPI(
    title="User Management API",
    description="REST API for secure identity management, operational data access, and reliable service integration.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins_list,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
