"""Abstract base class for tool providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from mcp.types import Tool


class ToolProvider(ABC):
    """Interface that every provider must implement.

    A provider contributes one or more MCP tools.  It is responsible for:
    - declaring tool schemas (``list_tools``)
    - executing tool calls and returning text results (``call_tool``)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Short identifier for the provider (e.g. ``"searxng"``)."""

    @abstractmethod
    def list_tools(self) -> list[Tool]:
        """Return MCP ``Tool`` definitions for all tools this provider offers."""

    @abstractmethod
    async def call_tool(self, name: str, arguments: dict) -> str:
        """Execute a tool call and return a plain-text result.

        Raise ``Exception`` for user-facing errors — the MCP layer will
        wrap them in an ``isError`` response.
        """
