"""Health and readiness endpoints."""

from fastapi import APIRouter
from fastapi.responses import UJSONResponse

from mcp_server.settings import provider_settings_manager

router = APIRouter(tags=["monitoring"])


@router.get("/health")
async def health_check() -> UJSONResponse:
    return UJSONResponse({"status": "ok", "provider": "searxng"})


@router.get("/readiness")
async def readiness_check() -> UJSONResponse:
    """Check that the backing SearXNG instance is reachable."""
    import httpx

    base_url = provider_settings_manager.current.base_url
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/healthz")
            if resp.status_code == 200:
                return UJSONResponse({"status": "ok", "searxng": "reachable"})
            return UJSONResponse(
                {"status": "degraded", "searxng": f"HTTP {resp.status_code}"},
                status_code=503,
            )
    except Exception as exc:
        return UJSONResponse(
            {"status": "degraded", "searxng": str(exc)},
            status_code=503,
        )
