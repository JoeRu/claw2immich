from functools import lru_cache
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
MCP_PORT_RAW = os.getenv("MCP_PORT", "8000").strip()
MCP_LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO").strip().upper() or "INFO"
try:
    MCP_PORT = int(MCP_PORT_RAW)
except ValueError as exc:
    raise ValueError("MCP_PORT must be an integer") from exc

mcp = FastMCP("claw2immich", host=MCP_HOST, port=MCP_PORT, log_level=MCP_LOG_LEVEL)

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


def _probe(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any | None = None,
    require_auth: bool = False,
) -> dict[str, Any]:
    try:
        config = _get_config()
        url = f"{config['base_url']}{path}"
        headers = _build_headers(config, require_auth)
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.request(
                method, url, params=params, json=json_body, headers=headers
            )
        return {
            "ok": response.status_code < 400,
            "status_code": response.status_code,
            "detail": response.text,
        }
    except httpx.RequestError as exc:
        return {"ok": False, "error": "Network error", "detail": str(exc)}
    except ValueError as exc:
        return {"ok": False, "error": "Configuration error", "detail": str(exc)}


@lru_cache
def _fetch_openapi_spec() -> dict[str, Any]:
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        response = client.get(OPENAPI_SPEC_URL)
    response.raise_for_status()
    return response.json()


@lru_cache
def _discover_capabilities() -> dict[str, dict[str, str | bool]]:
    capabilities: dict[str, dict[str, str | bool]] = {
        "get_current_user": {"allowed": False, "reason": "Not checked"}
    }
    config = _get_config()
    if not (config["api_key"] or config["api_token"]):
        capabilities["get_current_user"]["reason"] = (
            "Missing IMMICH_API_KEY or IMMICH_API_TOKEN"
        )
        return capabilities

    probe = _probe("GET", "/api/users/me", require_auth=True)
    if probe.get("ok"):
        capabilities["get_current_user"]["allowed"] = True
        capabilities["get_current_user"]["reason"] = "Allowed"
        return capabilities

    status_code = probe.get("status_code")
    if status_code in (401, 403):
        capabilities["get_current_user"]["reason"] = (
            "API key/token lacks permission for /api/users/me"
        )
        return capabilities

    error = probe.get("error")
    if error:
        capabilities["get_current_user"]["reason"] = (
            f"Capability check failed: {error}"
        )
        return capabilities

    capabilities["get_current_user"]["reason"] = (
        "Immich server error during capability check"
    )
    return capabilities


@lru_cache
def _discover_write_capability() -> dict[str, str | bool]:
    method = os.getenv("IMMICH_WRITE_PROBE_METHOD", "POST").strip().upper()
    path = os.getenv("IMMICH_WRITE_PROBE_PATH", "").strip()
    if not path:
        return {
            "configured": False,
            "allowed": False,
            "reason": "IMMICH_WRITE_PROBE_PATH not set",
        }

    probe = _probe(method, path, require_auth=True)
    if probe.get("ok"):
        return {"configured": True, "allowed": True, "reason": "Allowed"}

    status_code = probe.get("status_code")
    if status_code in (401, 403):
        return {
            "configured": True,
            "allowed": False,
            "reason": f"API key/token lacks permission for {method} {path}",
        }

    error = probe.get("error")
    if error:
        return {
            "configured": True,
            "allowed": False,
            "reason": f"Capability check failed: {error}",
        }

    return {
        "configured": True,
        "allowed": False,
        "reason": "Immich server error during capability check",
    }


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


def ping_server() -> Any:
    """Check whether the Immich server is reachable."""
    return _request("GET", "/api/server/ping")


def get_server_info() -> Any:
    """Fetch public server info."""
    return _request("GET", "/api/server-info")


def get_server_version() -> Any:
    """Fetch Immich server version information."""
    return _request("GET", "/api/server/version")


def get_current_user() -> Any:
    """Fetch the current user (requires API key or token)."""
    return _request("GET", "/api/users/me", require_auth=True)


def tool_access_report() -> dict[str, Any]:
    """Describe which tools are available based on API key permissions."""
    capabilities = _discover_capabilities()
    allowed_tools = [
        "openapi_summary",
        "list_openapi_paths",
        "ping_server",
        "get_server_info",
        "get_server_version",
        "tool_access_report",
        "write_capability_report",
    ]
    blocked_tools: list[dict[str, str]] = []
    for tool_name, info in capabilities.items():
        if info.get("allowed"):
            allowed_tools.append(tool_name)
        else:
            blocked_tools.append(
                {"tool": tool_name, "reason": str(info.get("reason"))}
            )
    return {"allowed_tools": allowed_tools, "blocked_tools": blocked_tools}


def write_capability_report() -> dict[str, str | bool]:
    """Report optional write capability probe results."""
    return _discover_write_capability()


def _register_tools(capabilities: dict[str, dict[str, str | bool]]) -> None:
    for tool_func in (
        openapi_summary,
        list_openapi_paths,
        ping_server,
        get_server_info,
        get_server_version,
        tool_access_report,
        write_capability_report,
    ):
        mcp.tool()(tool_func)

    if capabilities.get("get_current_user", {}).get("allowed"):
        mcp.tool()(get_current_user)


def main() -> None:
    capabilities = _discover_capabilities()
    _register_tools(capabilities)
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
    mount_path = os.getenv("MCP_MOUNT_PATH", "").strip() or None
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT must be stdio, sse, or streamable-http")
    mcp.run(transport=transport, mount_path=mount_path)


if __name__ == "__main__":
    main()
