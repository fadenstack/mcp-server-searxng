"""Dedicated CLI for the SearXNG MCP server."""

from __future__ import annotations

import json
import subprocess
import sys

import click

from mcp_server.settings import settings


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
@click.version_option(package_name="mcp-server-searxng")
@click.pass_context
def cli(ctx: click.Context, *, verbose: bool) -> None:
    """mcp-searxng — Standalone MCP server backed by a self-hosted SearXNG instance."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("--host", default=None, help="Bind host (overrides MCP_SEARXNG_HOST).")
@click.option("--port", default=None, type=int, help="Bind port (overrides MCP_SEARXNG_PORT).")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development.")
def run(host: str | None, port: int | None, *, reload: bool) -> None:
    """Start the MCP server."""
    import uvicorn

    uvicorn.run(
        "mcp_server.web.application:get_app",
        host=host or settings.host,
        port=port or settings.port,
        workers=settings.workers_count,
        reload=reload or settings.reload,
        factory=True,
    )


@cli.command()
def doctor() -> None:
    """Validate configuration and test SearXNG connectivity."""
    errors: list[str] = []
    warnings: list[str] = []

    click.echo("Checking configuration...\n")

    # SearXNG base URL
    click.echo(f"  SearXNG URL: {settings.base_url}")

    # Auth token
    if settings.auth_enabled:
        click.echo("  [OK] Auth token set (incoming requests will be validated)")
    else:
        warnings.append("No MCP_SEARXNG_AUTH_TOKEN set — server accepts unauthenticated requests.")

    # Test SearXNG connectivity
    click.echo("\nTesting SearXNG connectivity...")
    import httpx

    try:
        resp = httpx.get(
            f"{settings.base_url}/search",
            params={"q": "test", "format": "json", "categories": "general"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            n = len(data.get("results", []))
            click.echo(f"  [OK] SearXNG reachable — returned {n} results")
        else:
            errors.append(f"SearXNG returned HTTP {resp.status_code}.")
    except httpx.ConnectError:
        errors.append(f"Cannot reach SearXNG at {settings.base_url} — check that it is running.")
    except httpx.TimeoutException:
        errors.append("SearXNG request timed out.")

    # Summary
    click.echo("")
    for w in warnings:
        click.echo(click.style(f"  [WARN] {w}", fg="yellow"))
    for e in errors:
        click.echo(click.style(f"  [FAIL] {e}", fg="red"))

    if errors:
        click.echo(click.style("\nDoctor found issues. Fix them before starting.", fg="red"))
        raise SystemExit(1)

    click.echo(click.style("\nAll checks passed.", fg="green"))


@cli.command()
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
def manifest(*, pretty: bool) -> None:
    """Print the MCP tool manifest as JSON (for registration/debugging)."""
    from mcp_server.providers.searxng.provider import SearXNGProvider

    provider = SearXNGProvider()
    tools = [
        {
            "name": t.name,
            "description": t.description,
            "inputSchema": t.inputSchema,
        }
        for t in provider.list_tools()
    ]

    output = {
        "server_name": "searxng-search",
        "provider": provider.provider_name,
        "transport": "streamable-http",
        "endpoint": f"http://{settings.host}:{settings.port}/mcp",
        "tools": tools,
    }
    indent = 2 if pretty else None
    click.echo(json.dumps(output, indent=indent))


@cli.command("docker-up")
@click.option("--build", is_flag=True, help="Rebuild the image before starting.")
@click.option("--dev", is_flag=True, help="Use dev compose overrides.")
def docker_up(*, build: bool, dev: bool) -> None:
    """Build and start the Docker container."""
    cmd = ["docker", "compose"]
    if dev:
        cmd.extend(["-f", "docker-compose.yml", "-f", "deploy/docker-compose.dev.yml"])
    cmd.append("up")
    if build:
        cmd.append("--build")
    cmd.append("-d")
    click.echo(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


@cli.command("docker-down")
def docker_down() -> None:
    """Stop and remove the Docker container."""
    cmd = ["docker", "compose", "down"]
    click.echo(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    cli()
