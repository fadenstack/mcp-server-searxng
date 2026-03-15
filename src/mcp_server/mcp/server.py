"""MCP Server instance — registers tools from providers."""

from __future__ import annotations

from mcp.server import Server
from mcp.types import CallToolResult, TextContent, Tool

from mcp_server.providers.base import ToolProvider

# Module-level server instance — created once, shared with transport.
mcp_server = Server("searxng-search")

# Provider registry — populated by register_provider().
_providers: dict[str, ToolProvider] = {}


def register_provider(provider: ToolProvider) -> None:
    """Register a provider's tools with the MCP server."""
    for tool in provider.list_tools():
        _providers[tool.name] = provider


@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return all registered tool definitions."""
    tools: list[Tool] = []
    for provider in dict.fromkeys(_providers.values()):
        tools.extend(provider.list_tools())
    return tools


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> CallToolResult:
    """Dispatch a tool call to the appropriate provider."""
    provider = _providers.get(name)
    if provider is None:
        return CallToolResult(
            isError=True,
            content=[TextContent(type="text", text=f"Unknown tool: {name}")],
        )
    try:
        result = await provider.call_tool(name, arguments or {})
        return CallToolResult(
            content=[TextContent(type="text", text=result)],
        )
    except Exception as exc:
        return CallToolResult(
            isError=True,
            content=[TextContent(type="text", text=str(exc))],
        )
