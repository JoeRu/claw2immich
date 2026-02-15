# claw2immich

claw2immich is a Python MCP (Model Context Protocol) server that exposes selected Immich REST API endpoints. It uses the Immich OpenAPI spec for API metadata and surfaces a small, permission-aware tool set for common read-only checks.

## Status
- Core MCP server and capability filtering are implemented.
- Tool exposure is gated by Immich API permissions.
- Integration tests cover tool listing and permission probes.

## Available tools
- `openapi_summary` (OpenAPI title/version/path count)
- `list_openapi_paths` (limited list of method/path entries)
- `ping_server`
- `get_server_info`
- `get_server_version`
- `tool_access_report`
- `write_capability_report`
- `get_current_user` (only when permitted by API key/token)

## Configuration
Environment variables:
- `IMMICH_BASE_URL` (default `http://localhost:2283`)
- `IMMICH_API_KEY`
- `IMMICH_API_TOKEN`
- `IMMICH_WRITE_PROBE_PATH` (optional write capability probe)
- `IMMICH_WRITE_PROBE_METHOD` (default `POST`)

OpenAPI spec source:
https://github.com/immich-app/immich/blob/main/open-api/immich-openapi-specs.json

## Run
```
python main.py
```

## Tests
Integration tests use the standard library `unittest` runner (pytest can also discover them).

Integration test setup:
1. Ensure an Immich server is running and reachable.
2. Create `.env_test` with read-only credentials.
3. Create `.env` with full-access credentials, or set `IMMICH_ENV_FULL` to another file.

Run:
```
python -m unittest discover -s tests -v
```

Optional with pytest:
```
pytest tests/
```

You can override env file locations:
- `IMMICH_ENV_TEST` for the restricted credentials file (default `.env_test`)
- `IMMICH_ENV_FULL` for the full-access credentials file (default `.env`)

## Docker

Build and run with Docker Compose:
```
docker compose build
docker compose up
```

Environment variables are passed through from your shell or `.env` file:
- `IMMICH_BASE_URL` (default `http://host.docker.internal:2283`)
- `IMMICH_API_KEY`
- `IMMICH_API_TOKEN`
- `IMMICH_WRITE_PROBE_PATH`
- `IMMICH_WRITE_PROBE_METHOD`