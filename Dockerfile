# ── SearXNG + MCP Server unified image ───────────────────────────
# Runs both SearXNG (port 8080 internal) and the MCP server (port 8101)
# inside a single container using supervisord as process manager.
#
# Build:  docker build -t llmport/mcp-searxng:latest .
# Run:    docker compose up -d

FROM searxng/searxng:latest

# ── Install Python build tooling ─────────────────────────────────
# SearXNG base already has Python 3.12+ and pip.
# We add uv for fast dependency resolution and supervisord for process mgmt.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apk add --no-cache supervisor

# ── Install MCP server dependencies ─────────────────────────────
WORKDIR /app/mcp

COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

COPY src/ ./src/

RUN uv pip install --system --no-cache -e .

# ── Supervisord configuration ───────────────────────────────────
COPY deploy/supervisord.conf /etc/supervisord.conf

# ── SearXNG default settings (can be overridden by volume mount) ─
COPY deploy/searxng-settings.yml /etc/searxng/settings.yml

# ── Expose ports ─────────────────────────────────────────────────
# 8080 = SearXNG web UI/API (keep private in production)
# 8101 = MCP Streamable HTTP endpoint
EXPOSE 8080 8101

# ── Entrypoint ───────────────────────────────────────────────────
# supervisord runs both processes and handles signal propagation
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
