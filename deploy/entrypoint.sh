#!/bin/sh
# entrypoint.sh — start SearXNG + MCP server in a single container
# No supervisord needed — just background the SearXNG process and
# run the MCP server in the foreground.

set -e

# ── Trap signals for clean shutdown ──────────────────────────────
cleanup() {
    echo "[entrypoint] Shutting down…"
    kill "$SEARXNG_PID" 2>/dev/null || true
    wait "$SEARXNG_PID" 2>/dev/null || true
    exit 0
}
trap cleanup TERM INT QUIT

# ── Start SearXNG in background ──────────────────────────────────
# Activate the SearXNG venv so granian worker subprocesses inherit
# the correct sys.path (they fork via multiprocessing).
echo "[entrypoint] Starting SearXNG on :8080…"
(
    export VIRTUAL_ENV=/usr/local/searxng/.venv
    export PATH="/usr/local/searxng/.venv/bin:$PATH"
    export SEARXNG_SETTINGS_PATH="/etc/searxng/settings.yml"
    cd /usr/local/searxng
    exec python -m granian \
        --interface asgi \
        --host 0.0.0.0 \
        --port 8080 \
        --workers 1 \
        --log-level info \
        searx.webapp:app
) &
SEARXNG_PID=$!

# ── Wait for SearXNG to be ready ────────────────────────────────
echo "[entrypoint] Waiting for SearXNG…"
for i in $(seq 1 30); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080')" 2>/dev/null; then
        echo "[entrypoint] SearXNG is ready"
        break
    fi
    [ "$i" -eq 30 ] && echo "[entrypoint] WARNING: SearXNG not ready after 30s, starting MCP server anyway"
    sleep 1
done

# ── Start MCP server in foreground ───────────────────────────────
echo "[entrypoint] Starting MCP server on :8101…"
exec python3 -m mcp_server
