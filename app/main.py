from fastapi import FastAPI

from app.routes.router import api_router
from app.settings.app_config import app_config

app = FastAPI(title=app_config.app_name)
app.include_router(api_router)