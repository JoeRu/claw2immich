from functools import lru_cache
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("claw2immich")

OPENAPI_SPEC_URL = (
    "https://raw.githubusercontent.com/immich-app/immich/main/open-api/immich-openapi-specs.json"
)
DEFAULT_BASE_URL = "http://localhost:2283"
DEFAULT_TIMEOUT = 10.0


def _get_config() -> dict[str, str]:
    base_url = os.getenv("IMMICH_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    api_key = os.getenv("IMMICH_API_KEY", "").strip()
    api_token = os.getenv("IMMICH_API_TOKEN", "").strip()
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        raise ValueError("IMMICH_BASE_URL must start with http:// or https://")
    return {"base_url": base_url, "api_key": api_key, "api_token": api_token}


def _build_headers(config: dict[str, str], require_auth: bool) -> dict[str, str]:
    headers = {"accept": "application/json"}
    if config["api_key"]:
        headers["x-api-key"] = config["api_key"]
    if config["api_token"]:
        headers["authorization"] = f"Bearer {config['api_token']}"
    if require_auth and not (config["api_key"] or config["api_token"]):
        raise ValueError("IMMICH_API_KEY or IMMICH_API_TOKEN must be set for this call")
    return headers


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any | None = None,
    require_auth: bool = False,
) -> Any:
    try:
        config = _get_config()
        url = f"{config['base_url']}{path}"
        headers = _build_headers(config, require_auth)
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.request(
                method, url, params=params, json=json_body, headers=headers
            )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text
    except httpx.HTTPStatusError as exc:
        return {
            "error": "Immich API error",
            "status_code": exc.response.status_code,
            "detail": exc.response.text,
        }
    except httpx.RequestError as exc:
        return {"error": "Network error", "detail": str(exc)}
    except ValueError as exc:
        return {"error": "Configuration error", "detail": str(exc)}


def _pagination_params(
    page: int | None = None,
    size: int | None = None,
    order: str | None = None,
) -> dict[str, Any] | None:
    params: dict[str, Any] = {}
    if page is not None:
        params["page"] = page
    if size is not None:
        params["size"] = size
    if order:
        params["order"] = order
    return params or None


@lru_cache
def _fetch_openapi_spec() -> dict[str, Any]:
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        response = client.get(OPENAPI_SPEC_URL)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def openapi_summary() -> dict[str, Any]:
    """Return OpenAPI title, version, and path count."""
    spec = _fetch_openapi_spec()
    info = spec.get("info", {})
    paths = spec.get("paths", {})
    return {
        "title": info.get("title"),
        "version": info.get("version"),
        "path_count": len(paths),
    }


@mcp.tool()
def list_openapi_paths(limit: int = 20) -> list[str]:
    """List OpenAPI method/path entries (limited)."""
    spec = _fetch_openapi_spec()
    paths = spec.get("paths", {})
    entries: list[str] = []
    for path, methods in paths.items():
        for method in methods.keys():
            entries.append(f"{method.upper()} {path}")
            if len(entries) >= limit:
                return entries
    return entries


@mcp.tool()
def ping_server() -> Any:
    """Check whether the Immich server is reachable."""
    return _request("GET", "/api/server/ping")


@mcp.tool()
def get_server_info() -> Any:
    """Fetch public server info."""
    return _request("GET", "/api/server-info")


@mcp.tool()
def get_server_version() -> Any:
    """Fetch Immich server version information."""
    return _request("GET", "/api/server/version")


@mcp.tool()
def get_current_user() -> Any:
    """Fetch the current user (requires API key or token)."""
    return _request("GET", "/api/users/me", require_auth=True)


@mcp.tool()
def list_assets(
    page: int | None = None,
    size: int | None = None,
    order: str | None = None,
) -> Any:
    """List assets with optional pagination (requires API key or token)."""
    params = _pagination_params(page=page, size=size, order=order)
    return _request("GET", "/api/assets", params=params, require_auth=True)


@mcp.tool()
def get_asset(asset_id: str) -> Any:
    """Fetch a single asset by ID (requires API key or token)."""
    return _request("GET", f"/api/assets/{asset_id}", require_auth=True)


@mcp.tool()
def list_albums(
    page: int | None = None,
    size: int | None = None,
    order: str | None = None,
) -> Any:
    """List albums with optional pagination (requires API key or token)."""
    params = _pagination_params(page=page, size=size, order=order)
    return _request("GET", "/api/albums", params=params, require_auth=True)


@mcp.tool()
def get_album(album_id: str) -> Any:
    """Fetch a single album by ID (requires API key or token)."""
    return _request("GET", f"/api/albums/{album_id}", require_auth=True)


@mcp.tool()
def list_libraries() -> Any:
    """List libraries (requires API key or token)."""
    return _request("GET", "/api/libraries", require_auth=True)


@mcp.tool()
def get_library(library_id: str) -> Any:
    """Fetch a single library by ID (requires API key or token)."""
    return _request("GET", f"/api/libraries/{library_id}", require_auth=True)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
