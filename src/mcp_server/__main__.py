"""Uvicorn entry point: python -m mcp_server"""

import uvicorn

from mcp_server.settings import settings


def main() -> None:
    uvicorn.run(
        "mcp_server.web.application:get_app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers_count,
        reload=settings.reload,
        factory=True,
    )


if __name__ == "__main__":
    main()
