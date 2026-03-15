"""FastAPI application factory."""

from __future__ import annotations

from importlib import metadata

from fastapi import FastAPI

from mcp_server.log import configure_logging
from mcp_server.mcp.transport import mount_mcp_transport
from mcp_server.settings import settings
from mcp_server.web.api.router import api_router
from mcp_server.web.lifespan import lifespan_setup


def get_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()

    app = FastAPI(
        title="MCP Server — SearXNG",
        version=metadata.version("mcp-server-searxng"),
        lifespan=lifespan_setup,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    # REST endpoints (health, etc.)
    app.include_router(api_router, prefix="/api")

    # MCP Streamable-HTTP transport at /mcp
    mount_mcp_transport(app)

    return app
