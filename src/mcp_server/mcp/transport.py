"""Mount the MCP SDK's Streamable-HTTP transport onto a FastAPI app.

The ``mcp`` SDK (>=1.9) provides ``StreamableHTTPServerTransport`` which
implements the ASGI interface.  We mount it at ``/mcp`` and wire it to
the ``mcp.server.Server`` instance created in ``server.py``.

Lifecycle (connect / run / terminate) is handled by the lifespan in
``lifespan.py`` so that streams are ready before the first request.
"""

from __future__ import annotations

from fastapi import FastAPI
from loguru import logger
from mcp.server.streamable_http import StreamableHTTPServerTransport
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from mcp_server.mcp.server import mcp_server, register_provider
from mcp_server.providers.searxng.provider import SearXNGProvider
from mcp_server.settings import settings

# Module-level transport — created by mount_mcp_transport(),
# lifecycle managed by lifespan_setup().
mcp_transport: StreamableHTTPServerTransport | None = None


class _MCPAsgiApp:
    """Thin ASGI wrapper: auth guard + delegate to the SDK transport."""

    def __init__(self, transport: StreamableHTTPServerTransport) -> None:
        self._transport = transport

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return
        request = Request(scope, receive)
        if not _check_auth(request):
            response = Response(content="Unauthorized", status_code=401)
            await response(scope, receive, send)
            return
        try:
            await self._transport.handle_request(scope, receive, send)
        except Exception:
            logger.exception("MCP transport error")
            raise


def _check_auth(request: Request) -> bool:
    """Validate bearer token if auth is enabled."""
    if not settings.auth_enabled:
        return True
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:] == settings.auth_token
    return False


def mount_mcp_transport(app: FastAPI) -> None:
    """Register providers and mount the MCP ASGI handler at ``/mcp``.

    Does **not** start the transport — that is done by the lifespan.
    """
    global mcp_transport

    # Register providers
    searxng_provider = SearXNGProvider()
    register_provider(searxng_provider)
    logger.info(
        "Registered provider '{}' with {} tool(s)",
        searxng_provider.provider_name,
        len(searxng_provider.list_tools()),
    )

    # Create the transport (mcp_session_id=None → stateless mode)
    mcp_transport = StreamableHTTPServerTransport(mcp_session_id=None)

    # Mount the ASGI sub-app at /mcp — this gives the transport
    # raw (scope, receive, send) instead of going through FastAPI routing.
    app.mount("/mcp", _MCPAsgiApp(mcp_transport))
