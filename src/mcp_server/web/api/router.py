"""API router composition."""

from fastapi import APIRouter

from mcp_server.web.api.monitoring import views as monitoring
from mcp_server.web.api.settings import views as settings_views

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(settings_views.router)
