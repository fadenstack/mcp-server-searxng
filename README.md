# MCP Server — SearXNG

Standalone MCP server backed by a self-hosted [SearXNG](https://docs.searxng.org/) instance.
Integrates with LLM.port as a tool provider via the **Streamable HTTP** transport.

## Architecture

This project runs **both SearXNG and the MCP server in a single container** using
`supervisord` as the process manager:

```
┌─────────────────────────────────────────┐
│  Container: mcp-searxng                 │
│                                         │
│  ┌─────────────┐   ┌─────────────────┐  │
│  │  SearXNG     │   │  MCP Server     │  │
│  │  (Granian)   │◄──│  (Uvicorn)      │  │
│  │  :8080       │   │  :8101          │  │
│  └─────────────┘   └────────┬────────┘  │
│                              │           │
│  supervisord manages both    │           │
└──────────────────────────────┼───────────┘
                               │
                    Streamable HTTP /mcp/
                               │
                        ┌──────┴──────┐
                        │  LLM.port   │
                        │  MCP Hub    │
                        └─────────────┘
```

## Tools

| Tool | Description |
|------|-------------|
| `web_search` | General web search across multiple engines |
| `news_search` | News article search with date filtering |
| `images_search` | Image search with source page links |

## Quick Start

### Docker (recommended)

```bash
# Build and run
docker compose up -d --build

# Verify
curl http://localhost:8101/api/health
```

### Local Development

```bash
# Install dependencies
uv sync

# Start (requires a running SearXNG instance)
MCP_SEARXNG_BASE_URL=http://localhost:8080 uv run python -m mcp_server
```

## Configuration

All settings use the `MCP_SEARXNG_` environment variable prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SEARXNG_BASE_URL` | `http://127.0.0.1:8080` | SearXNG instance URL |
| `MCP_SEARXNG_HOST` | `0.0.0.0` | MCP server bind host |
| `MCP_SEARXNG_PORT` | `8101` | MCP server bind port |
| `MCP_SEARXNG_AUTH_TOKEN` | *(empty)* | Bearer token for incoming MCP requests |
| `MCP_SEARXNG_REQUEST_TIMEOUT` | `15` | HTTP timeout for SearXNG calls (seconds) |
| `MCP_SEARXNG_LOG_LEVEL` | `info` | Log level |

## LLM.port Registration

Register this server in the MCP Admin UI:

| Field | Value |
|-------|-------|
| **Name** | `searxng` |
| **Transport** | `Streamable HTTP` |
| **URL** | `http://<host>:8101/mcp/` |
| **Tool Prefix** | `searxng` |

### Registration curl

```bash
curl -X POST http://localhost:8000/api/admin/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "searxng",
    "transport": "streamable_http",
    "url": "http://<host>:8101/mcp/",
    "tool_prefix": "searxng"
  }'
```

## Testing MCP Protocol

```bash
# Initialize
curl -X POST http://localhost:8101/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# List tools
curl -X POST http://localhost:8101/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id-from-init>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

# Call web_search
curl -X POST http://localhost:8101/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id-from-init>" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"web_search","arguments":{"query":"hello world"}}}'
```

## SearXNG Configuration

The container includes a default `settings.yml` at [`deploy/searxng-settings.yml`](deploy/searxng-settings.yml).
Override it by volume-mounting your own:

```yaml
volumes:
  - ./my-settings.yml:/etc/searxng/settings.yml
```

Key settings for MCP integration:
- `search.formats` must include `json` (enabled by default)
- `server.limiter` should be `false` unless you also run Redis/Valkey
- `server.secret_key` should be changed in production

## License

Apache-2.0
