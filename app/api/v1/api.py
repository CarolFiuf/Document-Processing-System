from fastapi import APIRouter

from app.api.v1.endpoints import documents, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(health.router, tags=["health"])