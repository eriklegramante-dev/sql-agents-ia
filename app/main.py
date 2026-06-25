from fastapi import FastAPI

from app.routes.router import api_router

app = FastAPI(
    title="SQL Agents IA",
    version="1.0.0",
)

app.include_router(api_router)