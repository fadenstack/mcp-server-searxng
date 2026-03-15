# ── SearXNG + MCP Server unified image ───────────────────────────
# Runs both SearXNG (port 8080 internal) and the MCP server (port 8101)
# inside a single container using supervisord as process manager.
#
# Build:  docker build -t llmport/mcp-searxng:latest .
# Run:    docker compose up -d

FROM searxng/searxng:latest

# ── Install Python build tooling ─────────────────────────────────
# SearXNG base has Python 3.14 but no pip on PATH.
# Install uv via ensurepip, then use uv for everything else.
RUN python3 -m ensurepip 2>/dev/null || true && \
    python3 -m pip install --no-cache-dir uv supervisor

# ── Install MCP server dependencies ─────────────────────────────
WORKDIR /app/mcp

COPY pyproject.toml README.md ./
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
# Override SearXNG's built-in ENTRYPOINT so we control the process tree.
# supervisord runs both SearXNG and MCP server, handles signal propagation.
ENTRYPOINT []
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
