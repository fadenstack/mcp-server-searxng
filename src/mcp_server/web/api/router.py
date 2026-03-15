"""API router composition."""

from fastapi import APIRouter

from mcp_server.web.api.monitoring import views as monitoring

api_router = APIRouter()
api_router.include_router(monitoring.router)
