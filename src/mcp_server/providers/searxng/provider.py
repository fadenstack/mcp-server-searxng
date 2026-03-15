"""SearXNG provider — exposes web_search, news_search, and images_search tools."""

from __future__ import annotations

from mcp.types import Tool

from mcp_server.providers.base import ToolProvider
from mcp_server.providers.searxng.client import SearXNGClient

_WEB_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The search query.",
        },
        "count": {
            "type": "integer",
            "description": "Number of results to return (1-50).",
            "default": 10,
        },
        "language": {
            "type": "string",
            "description": "Language code for results (e.g. en, de, fr). Empty for default.",
            "default": "",
        },
        "time_range": {
            "type": "string",
            "enum": ["", "day", "week", "month", "year"],
            "description": "Time range filter: day, week, month, or year. Empty for all time.",
            "default": "",
        },
        "engines": {
            "type": "string",
            "description": "Comma-separated search engines to use (e.g. google,duckduckgo). Empty for all.",
            "default": "",
        },
    },
    "required": ["query"],
}

_NEWS_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The news search query.",
        },
        "count": {
            "type": "integer",
            "description": "Number of results to return (1-50).",
            "default": 10,
        },
        "language": {
            "type": "string",
            "description": "Language code for results (e.g. en, de, fr). Empty for default.",
            "default": "",
        },
        "time_range": {
            "type": "string",
            "enum": ["", "day", "week", "month", "year"],
            "description": "Time range filter: day, week, month, or year. Empty for all time.",
            "default": "",
        },
    },
    "required": ["query"],
}

_IMAGES_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The image search query.",
        },
        "count": {
            "type": "integer",
            "description": "Number of results to return (1-50).",
            "default": 10,
        },
        "engines": {
            "type": "string",
            "description": "Comma-separated image engines (e.g. google_images,bing_images). Empty for all.",
            "default": "",
        },
    },
    "required": ["query"],
}


class SearXNGProvider(ToolProvider):
    """SearXNG as an MCP tool provider."""

    def __init__(self) -> None:
        self._client = SearXNGClient()

    @property
    def provider_name(self) -> str:
        return "searxng"

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name="web_search",
                description=(
                    "Search the web using SearXNG (a privacy-respecting metasearch engine). "
                    "Returns results aggregated from multiple search engines with titles, URLs, and snippets."
                ),
                inputSchema=_WEB_SEARCH_SCHEMA,
            ),
            Tool(
                name="news_search",
                description=(
                    "Search for recent news articles using SearXNG. "
                    "Returns news results with titles, URLs, publication dates, and snippets."
                ),
                inputSchema=_NEWS_SEARCH_SCHEMA,
            ),
            Tool(
                name="images_search",
                description=(
                    "Search for images using SearXNG. "
                    "Returns image results with titles, image URLs, and source pages."
                ),
                inputSchema=_IMAGES_SEARCH_SCHEMA,
            ),
        ]

    async def call_tool(self, name: str, arguments: dict) -> str:
        if name == "web_search":
            return await self._client.web_search(
                query=arguments["query"],
                count=arguments.get("count", 10),
                language=arguments.get("language", ""),
                time_range=arguments.get("time_range", ""),
                engines=arguments.get("engines", ""),
            )
        if name == "news_search":
            return await self._client.news_search(
                query=arguments["query"],
                count=arguments.get("count", 10),
                language=arguments.get("language", ""),
                time_range=arguments.get("time_range", ""),
            )
        if name == "images_search":
            return await self._client.images_search(
                query=arguments["query"],
                count=arguments.get("count", 10),
                engines=arguments.get("engines", ""),
            )
        raise ValueError(f"Unknown tool: {name}")
