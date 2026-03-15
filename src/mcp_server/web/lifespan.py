"""Application lifespan — startup and shutdown hooks."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import anyio
import httpx
from fastapi import FastAPI
from loguru import logger

from mcp_server.mcp.server import mcp_server
from mcp_server.mcp import transport as transport_mod
from mcp_server.settings import settings


@asynccontextmanager
async def lifespan_setup(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise shared resources on startup, tear down on shutdown."""

    # ── Startup ──────────────────────────────────────────────────
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.request_timeout, connect=5.0),
    )
    logger.info(
        "MCP SearXNG server starting on {}:{}  (env={})",
        settings.host,
        settings.port,
        settings.environment,
    )

    # ── MCP transport lifecycle ──────────────────────────────────
    transport = transport_mod.mcp_transport
    if transport is None:
        raise RuntimeError("mount_mcp_transport() must be called before lifespan")

    init_options = mcp_server.create_initialization_options()

    async with anyio.create_task_group() as tg:

        async def _run_mcp(*, task_status: anyio.abc.TaskStatus = anyio.TASK_STATUS_IGNORED) -> None:
            async with transport.connect() as (read_stream, write_stream):
                task_status.started()
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    init_options,
                    raise_exceptions=False,
                )

        await tg.start(_run_mcp)
        logger.info("MCP transport connected at /mcp (stateless mode)")

        yield

        # ── Shutdown ─────────────────────────────────────────────
        await transport.terminate()
        tg.cancel_scope.cancel()

    await app.state.http_client.aclose()
    logger.info("MCP SearXNG server stopped.")
