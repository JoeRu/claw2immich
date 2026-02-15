# claw2immich

Fresh project. The goal is to build an MCP server that exposes the Immich REST API.

## Goals
- Provide an MCP server interface for Immich endpoints.
- Keep the OpenAPI spec as the source of truth for API shape.

## Scope
### In scope
- MCP server scaffolding and tool definitions for Immich endpoints.
- Configuration for Immich base URL and API key/token.

### Out of scope
- Full Immich client UI.
- Production deployment or hosting.

## OpenAPI spec
Source: https://github.com/immich-app/immich/blob/main/open-api/immich-openapi-specs.json

Workflow (manual for now):
1. Download the latest spec when Immich updates.
2. Reconcile endpoint/tool mappings against the new spec.
3. Update any generated or hand-written mappings.

## Run (placeholder)
```
python main.py
```

## Configuration
Set these environment variables before running the server:
- `IMMICH_BASE_URL` (default: `http://localhost:2283`)
- `IMMICH_API_KEY` or `IMMICH_API_TOKEN` (required for authenticated tools)

## MCP tools (current)
Public:
- `openapi_summary`
- `list_openapi_paths`
- `ping_server`
- `get_server_info`
- `get_server_version`

Authenticated:
- `get_current_user`
- `list_assets`
- `get_asset`
- `list_albums`
- `get_album`
- `list_libraries`
- `get_library`

Example (authenticated):
```bash
export IMMICH_BASE_URL="http://localhost:2283"
export IMMICH_API_KEY="your-api-key"
python main.py
```

## Docker
Build and run with Docker Compose:
```bash
docker compose up --build
```

Environment variables (optional):
- `IMMICH_BASE_URL`
- `IMMICH_API_KEY`
- `IMMICH_API_TOKEN`
- `MCP_PORT` (default: 8765)

Note: The MCP server uses stdio transport, so the exposed port is reserved for future network transports.

## Test (placeholder)
Install dependencies and run:
```bash
pytest
```