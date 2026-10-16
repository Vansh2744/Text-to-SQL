from fastapi import APIRouter

from app.api.routes import conversations, datasets, queries, saved_queries, system

api = APIRouter(prefix="/api/v1")
for r in (system, datasets, queries, conversations, saved_queries):
    api.include_router(r.router)
