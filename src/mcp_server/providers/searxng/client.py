"""HTTP client for a self-hosted SearXNG instance."""

from __future__ import annotations

import httpx
from loguru import logger

from mcp_server.settings import provider_settings_manager


class SearXNGClient:
    """Async wrapper around the SearXNG ``/search`` JSON API."""

    def _base_url(self) -> str:
        return provider_settings_manager.current.base_url.rstrip("/")

    async def _search(self, params: dict[str, str | int]) -> dict:
        """Execute a search request against SearXNG and return the JSON payload."""
        url = f"{self._base_url()}/search"
        params["format"] = "json"
        ps = provider_settings_manager.current

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(ps.request_timeout, connect=5.0),
        ) as client:
            resp = await client.get(url, params=params)

        if resp.status_code >= 500:
            raise RuntimeError(f"SearXNG error (HTTP {resp.status_code}).")
        resp.raise_for_status()
        return resp.json()

    # ── Public methods ───────────────────────────────────────────

    async def web_search(
        self,
        query: str,
        count: int = 10,
        language: str = "",
        time_range: str = "",
        engines: str = "",
    ) -> str:
        """Perform a general web search and return markdown-formatted results."""
        params: dict[str, str | int] = {
            "q": query,
            "categories": "general",
            "pageno": 1,
        }
        if language:
            params["language"] = language
        if time_range:
            params["time_range"] = time_range
        if engines:
            params["engines"] = engines

        data = await self._search(params)
        results = data.get("results", [])[:count]
        return self._format_web_results(results, query, data)

    async def news_search(
        self,
        query: str,
        count: int = 10,
        language: str = "",
        time_range: str = "",
    ) -> str:
        """Perform a news search and return markdown-formatted results."""
        params: dict[str, str | int] = {
            "q": query,
            "categories": "news",
            "pageno": 1,
        }
        if language:
            params["language"] = language
        if time_range:
            params["time_range"] = time_range

        data = await self._search(params)
        results = data.get("results", [])[:count]
        return self._format_news_results(results, query)

    async def images_search(
        self,
        query: str,
        count: int = 10,
        engines: str = "",
    ) -> str:
        """Perform an image search and return markdown-formatted results."""
        params: dict[str, str | int] = {
            "q": query,
            "categories": "images",
            "pageno": 1,
        }
        if engines:
            params["engines"] = engines

        data = await self._search(params)
        results = data.get("results", [])[:count]
        return self._format_image_results(results, query)

    # ── Formatting ───────────────────────────────────────────────

    @staticmethod
    def _format_web_results(results: list[dict], query: str, data: dict) -> str:
        if not results:
            return f"No web results found for: {query}"

        lines = [f"## Web results for: {query}\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            snippet = r.get("content", "")
            engine = ", ".join(r.get("engines", []))
            lines.append(f"### {i}. {title}")
            lines.append(f"**URL:** {url}")
            if snippet:
                lines.append(f"{snippet}")
            if engine:
                lines.append(f"*Source: {engine}*")
            lines.append("")

        # Include infobox if present
        infoboxes = data.get("infoboxes", [])
        if infoboxes:
            info = infoboxes[0]
            lines.append(f"---\n**Infobox:** {info.get('infobox', '')}")
            if info.get("content"):
                lines.append(info["content"])
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_news_results(results: list[dict], query: str) -> str:
        if not results:
            return f"No news results found for: {query}"

        lines = [f"## News results for: {query}\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            snippet = r.get("content", "")
            published = r.get("publishedDate", "")
            engine = ", ".join(r.get("engines", []))
            lines.append(f"### {i}. {title}")
            lines.append(f"**URL:** {url}")
            if published:
                lines.append(f"**Published:** {published}")
            if snippet:
                lines.append(f"{snippet}")
            if engine:
                lines.append(f"*Source: {engine}*")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_image_results(results: list[dict], query: str) -> str:
        if not results:
            return f"No image results found for: {query}"

        lines = [f"## Image results for: {query}\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "Untitled")
            img_src = r.get("img_src", "")
            url = r.get("url", "")
            source = r.get("source", "")
            lines.append(f"### {i}. {title}")
            if img_src:
                lines.append(f"**Image:** {img_src}")
            if url:
                lines.append(f"**Page:** {url}")
            if source:
                lines.append(f"*Source: {source}*")
            lines.append("")

        return "\n".join(lines)
