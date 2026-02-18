# claw2immich

[![Docker](https://github.com/JoeRu/claw2immich/actions/workflows/build-docker.yml/badge.svg)](https://github.com/JoeRu/claw2immich/actions/workflows/build-docker.yml)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/JoeRu/claw2immich/ci.yml?branch=main)

claw2immich is a Python MCP (Model Context Protocol) server that exposes selected Immich REST API endpoints. It uses the Immich OpenAPI spec for API metadata and surfaces a small, permission-aware tool set for common read-only checks.

## Status
- Core MCP server and capability filtering are implemented.
- Tool exposure is gated by Immich API permissions.
- Integration tests cover tool listing and permission probes.

## Available tools
- `ping_server`
- `get_server_version`
- `tool_access_report`
- `write_capability_report`
- `get_current_user` (only when permitted by API key/token)

All OpenAPI endpoints are exposed as tools named `immich_<operation>` or `immich_<method>_<path>`.
Tools are filtered based on auth presence, admin-only markers, and write capability probes (default `POST /api/assets`).

OpenAPI tool descriptions include:
- `params:` summary of required path/query/body fields
- `example:` short call sketch for required inputs
- `returns:` response schema title and key fields when available

OpenAPI tool responses for assets, albums, people, and places include a `web_url` field with a direct link to the item in the Immich web UI (when `IMMICH_EXTERNAL_DOMAIN` is configured or discovered from server settings).

OpenAPI tool parameters use explicit, prefixed fields so MCP clients can discover what to set:
- `path_<name>` for path parameters
- `query_<name>` for query parameters
- `header_<name>` for header parameters
- `cookie_<name>` for cookie parameters
- `body` for JSON request bodies

Legacy fields `path_params`, `query_params`, `headers`, and `json_body` are still accepted for compatibility.

## MCP documentation surfaces
- Server instructions are sent during initialize. Use them as the short on-ramp and point to the usage guide resource.
- Initialize instructions now call out externalDomain discovery, workflow groups, do/don't guidance, and an example instruction string.
- Resource: `docs://usage-guide` contains a detailed workflow guide with examples.
- Prompts: workflow templates are available under titles like "Immich: Get image", "Immich: Find person", and "Immich: Share album".

## Configuration
Environment variables:
- `IMMICH_BASE_URL` (default `http://localhost:2283`)
- `IMMICH_API_KEY`
- `IMMICH_API_TOKEN`
- `IMMICH_EXTERNAL_DOMAIN` (optional: domain for web UI links like `https://immich.example.com`; if not set, discovered from `/api/server-config`)
- `IMMICH_PROFILE` (optional: `read_only`, `read_write`, or `full_scope`)
- `IMMICH_WRITE_PROBE_PATH` (default `/api/assets`)
- `IMMICH_WRITE_PROBE_METHOD` (default `POST`)

MCP server environment variables:
- `MCP_TRANSPORT` (`stdio`, `sse`, or `streamable-http`; default `stdio`)
- `MCP_HOST` (default `127.0.0.1`)
- `MCP_PORT` (default `8000`)
- `MCP_MOUNT_PATH` (optional mount path for SSE transport)
- `MCP_LOG_LEVEL` (default `INFO`)

OpenAPI spec source:
Version-matched spec (after `/api/health` and `/api/server/version`):
https://raw.githubusercontent.com/immich-app/immich/v{VERSION}/open-api/immich-openapi-specs.json

## Access Profiles

Access profiles provide predefined permission levels to simplify API key management and reduce misconfiguration risk. Set `IMMICH_PROFILE` to one of the following values:

### `read_only`
**Use case:** Safe browsing, search, and reporting without modification risk.

**Permissions required:**
- `asset.read` - View photos and videos
- `album.read` - View albums
- `library.read` - Browse libraries
- `timeline.read` - Access timeline and memories

**Typical tools exposed:**
- `immich_getAllAssets`, `immich_getAssetById`, `immich_searchAssets`
- `immich_getAllAlbums`, `immich_getAlbumInfo`
- `immich_getMyUserInfo`, `immich_getServerVersion`
- All GET endpoints for reading data

**Blocked tools:**
- Asset upload, update, delete
- Album creation, modification
- User management
- Server configuration

**Example Claude Desktop config (`mcporter.json` snippet):**
```json
{
  "mcpServers": {
    "claw2immich-readonly": {
      "command": "python",
      "args": ["c:\\path\\to\\claw2immich\\main.py"],
      "env": {
        "IMMICH_BASE_URL": "https://immich.example.com",
        "IMMICH_API_KEY": "your-read-only-key",
        "IMMICH_PROFILE": "read_only"
      }
    }
  }
}
```

### `read_write`
**Use case:** Full asset and album management without admin privileges.

**Permissions required:**
- All `read_only` permissions plus:
- `asset.create` - Upload photos/videos
- `asset.update` - Edit metadata, favorites
- `asset.delete` - Remove assets
- `album.create` - Create albums
- `album.update` - Modify albums
- `album.delete` - Remove albums

**Typical tools exposed:**
- All read-only tools plus:
- `immich_uploadAsset`, `immich_updateAsset`, `immich_deleteAssets`
- `immich_createAlbum`, `immich_addAssetsToAlbum`, `immich_removeAssetFromAlbum`
- `immich_updateUser` (own user only)
- All POST, PUT, PATCH, DELETE endpoints except admin-only

**Blocked tools:**
- User administration (`getAllUsers`, `createUser`, `deleteUser`)
- Server configuration (`setServerConfig`, `updateServerConfig`)
- System maintenance (`runJobs`, `validateStorage`)
- API key management

**Example Claude Desktop config:**
```json
{
  "mcpServers": {
    "claw2immich-readwrite": {
      "command": "python",
      "args": ["c:\\path\\to\\claw2immich\\main.py"],
      "env": {
        "IMMICH_BASE_URL": "https://immich.example.com",
        "IMMICH_API_KEY": "your-readwrite-key",
        "IMMICH_PROFILE": "read_write"
      }
    }
  }
}
```

### `full_scope`
**Use case:** Administrative tasks, user management, server configuration.

**Permissions required:**
- All `read_write` permissions plus:
- `admin.user` - User administration
- `admin.config` - Server configuration
- `admin.jobs` - Job management
- `admin.apiKey` - API key management

**Typical tools exposed:**
- All read_write tools plus:
- `immich_getAllUsers`, `immich_createUser`, `immich_updateUser`, `immich_deleteUser`
- `immich_getServerConfig`, `immich_updateServerConfig`
- `immich_getAllJobs`, `immich_runJob`
- `immich_createApiKey`, `immich_updateApiKey`, `immich_deleteApiKey`

**Example Claude Desktop config:**
```json
{
  "mcpServers": {
    "claw2immich-admin": {
      "command": "python",
      "args": ["c:\\path\\to\\claw2immich\\main.py"],
      "env": {
        "IMMICH_BASE_URL": "https://immich.example.com",
        "IMMICH_API_KEY": "your-admin-key",
        "IMMICH_PROFILE": "full_scope"
      }
    }
  }
}
```

### No profile (default)
When `IMMICH_PROFILE` is not set, tool filtering relies solely on capability probes and the API key's actual permissions. This is backward-compatible with existing configurations.

**Profile selection guidelines:**
- Use `read_only` for AI assistants performing search and analysis without modification needs
- Use `read_write` for general asset and album management workflows
- Use `full_scope` only when administrative access is required
- Always create a dedicated Immich API key with minimal permissions for each profile

## Run
```
python main.py
```

## Tests
Integration tests use the standard library `unittest` runner (pytest can also discover them).

Blocked tool reasons now include HTTP status or network error details to help troubleshoot capability checks.

Integration test setup:
1. Ensure an Immich server is running and reachable.
2. Create `.env_test` with read-only credentials.
3. Create `.env` with full-access credentials, or set `IMMICH_ENV_FULL` to another file.

MCP client tests start a background server using SSE. You can override defaults:
- `MCP_TEST_HOST` (default `127.0.0.1`)
- `MCP_TEST_PORT` (default `0` for auto-assign)
- `MCP_TEST_TIMEOUT` (default `20` seconds)
- `MCP_LOG_LEVEL` (default `DEBUG` for test server logs)

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

### Build and run locally

Build and run with Docker Compose:
```
docker compose build
docker compose up
```

Note: the container runs `main.py`, which imports the `claw2immich` package.
If you change the package layout, rebuild the image so the updated package is
copied into the container.

Environment variables are passed through from your shell or `.env` file:
- `IMMICH_BASE_URL` (default `http://host.docker.internal:2283`)
- `IMMICH_API_KEY`
- `IMMICH_API_TOKEN`
- `IMMICH_WRITE_PROBE_PATH` (default `/api/assets`)
- `IMMICH_WRITE_PROBE_METHOD` (default `POST`)

MCP server settings for Docker Compose:
- `MCP_TRANSPORT` (default `sse` in compose; use `streamable-http` for HTTP)
- `MCP_HOST` (default `0.0.0.0` in compose)
- `MCP_PORT` (default `8000`; published as the host port)

### Use pre-built images from GitHub Container Registry

Pre-built Docker images are automatically published to GitHub Container Registry (GHCR) for every push to `main` and `develop` branches, as well as for releases.

**Pull the image:**
```bash
# Latest build from main branch
docker pull ghcr.io/joeru/claw2immich:latest

# Latest build from develop branch
docker pull ghcr.io/joeru/claw2immich:develop

# Specific version (e.g., 0.1.0)
docker pull ghcr.io/joeru/claw2immich:0.1.0
```

**Run the image:**
```bash
docker run -e IMMICH_BASE_URL=https://immich.example.com \
           -e IMMICH_API_KEY=your-api-key \
           -p 8000:8000 \
           ghcr.io/joeru/claw2immich:latest
```

**Run with SSE transport (HTTP):**
```bash
docker run -e IMMICH_BASE_URL=https://immich.example.com \
           -e IMMICH_API_KEY=your-api-key \
           -e MCP_TRANSPORT=sse \
           -e MCP_HOST=0.0.0.0 \
           -p 8000:8000 \
           ghcr.io/joeru/claw2immich:latest
```

**Run with read-only profile:**
```bash
docker run -e IMMICH_BASE_URL=https://immich.example.com \
           -e IMMICH_API_KEY=your-readonly-api-key \
           -e IMMICH_PROFILE=read_only \
           -p 8000:8000 \
           ghcr.io/joeru/claw2immich:latest
```

Images support multiple architectures (amd64, arm64) and are automatically selected based on your platform.
