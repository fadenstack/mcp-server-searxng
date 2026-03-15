"""Settings REST API — schema, get, update provider settings at runtime."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import UJSONResponse
from pydantic import ValidationError

from mcp_server.settings import provider_settings_manager

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/schema")
async def get_settings_schema() -> UJSONResponse:
    """Return the JSON Schema for provider settings."""
    return UJSONResponse(provider_settings_manager.get_schema())


@router.get("")
async def get_settings() -> UJSONResponse:
    """Return current provider settings (sensitive fields masked)."""
    return UJSONResponse(provider_settings_manager.get_values())


@router.put("")
async def update_settings(body: dict[str, Any]) -> UJSONResponse:
    """Apply a partial update to provider settings."""
    try:
        provider_settings_manager.update(body)
    except ValidationError as exc:
        return UJSONResponse(
            {"error": "validation_error", "detail": exc.errors()},
            status_code=422,
        )
    return UJSONResponse(provider_settings_manager.get_values())
