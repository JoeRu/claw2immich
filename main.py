from functools import lru_cache
import inspect
import os
import re
from typing import Any
from urllib.parse import quote

import httpx
from mcp.server.fastmcp import FastMCP

MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
MCP_PORT_RAW = os.getenv("MCP_PORT", "8000").strip()
MCP_LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO").strip().upper() or "INFO"
try:
    MCP_PORT = int(MCP_PORT_RAW)
except ValueError as exc:
    raise ValueError("MCP_PORT must be an integer") from exc

SERVER_INSTRUCTIONS = (
    "claw2immich MCP server for Immich. "
    "Use tool descriptions (method/path) to choose OpenAPI tools. "
    "Read docs://usage-guide for workflow examples and parameter naming."
)
USAGE_GUIDE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "docs", "usage-guide.md"
)

mcp = FastMCP(
    "claw2immich",
    host=MCP_HOST,
    port=MCP_PORT,
    log_level=MCP_LOG_LEVEL,
    instructions=SERVER_INSTRUCTIONS,
)

OPENAPI_SPEC_URL = (
    "https://raw.githubusercontent.com/immich-app/immich/main/open-api/immich-openapi-specs.json"
)
DEFAULT_BASE_URL = "http://localhost:2283"
DEFAULT_TIMEOUT = 10.0


@lru_cache
def _load_usage_guide() -> str:
    try:
        with open(USAGE_GUIDE_PATH, "r", encoding="utf-8") as guide_file:
            return guide_file.read()
    except OSError as exc:
        return f"Usage guide not available: {exc}"


@mcp.resource("docs://usage-guide")
def usage_guide() -> str:
    """Return the MCP usage guide markdown."""
    return _load_usage_guide()


@mcp.prompt(title="Immich: Get image")
def prompt_get_image(asset_id: str) -> str:
    return (
        "Find the tool whose description starts with 'GET /api/assets/{id}'. "
        "Call it with path_id set to the asset id. "
        f"Asset id: {asset_id}."
    )


@mcp.prompt(title="Immich: Find person")
def prompt_find_person(person_name: str) -> str:
    return (
        "Locate a tool with 'people' or 'person' in the description (often a search endpoint). "
        "Check inputSchema to decide whether to pass query_ fields or a body payload. "
        f"Target name: {person_name}."
    )


@mcp.prompt(title="Immich: Find location")
def prompt_find_location(location_name: str) -> str:
    return (
        "Locate a tool with 'locations' or 'map' in the description. "
        "Provide query_ or body fields based on inputSchema. "
        f"Target location: {location_name}."
    )


@mcp.prompt(title="Immich: Newest photo")
def prompt_newest_photo(limit: int = 1) -> str:
    return (
        "Locate a tool that lists assets (description includes '/api/assets' or '/api/search'). "
        "Use query parameters for sorting by time desc and limit. "
        f"Limit: {limit}."
    )


@mcp.prompt(title="Immich: Upload photo")
def prompt_upload_photo(filename: str) -> str:
    return (
        "Locate a tool with description starting 'POST /api/assets' or 'POST /api/assets/upload'. "
        "Inspect inputSchema and send required metadata in body. "
        f"Filename: {filename}."
    )


@mcp.prompt(title="Immich: Share album")
def prompt_share_album(album_id: str) -> str:
    return (
        "Locate a tool with description 'POST /api/albums/{id}/share' or similar. "
        "Call with path_id and body fields for sharing options. "
        f"Album id: {album_id}."
    )


def _get_config() -> dict[str, str]:
    base_url = os.getenv("IMMICH_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    api_key = os.getenv("IMMICH_API_KEY", "").strip()
    api_token = os.getenv("IMMICH_API_TOKEN", "").strip()
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        raise ValueError("IMMICH_BASE_URL must start with http:// or https://")
    return {"base_url": base_url, "api_key": api_key, "api_token": api_token}


def _build_headers(
    config: dict[str, str],
    require_auth: bool,
    extra_headers: dict[str, Any] | None = None,
) -> dict[str, str]:
    headers = {"accept": "application/json"}
    if config["api_key"]:
        headers["x-api-key"] = config["api_key"]
    if config["api_token"]:
        headers["authorization"] = f"Bearer {config['api_token']}"
    if require_auth and not (config["api_key"] or config["api_token"]):
        raise ValueError("IMMICH_API_KEY or IMMICH_API_TOKEN must be set for this call")
    if extra_headers:
        headers.update({str(k): str(v) for k, v in extra_headers.items()})
    return headers


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any | None = None,
    require_auth: bool = False,
    extra_headers: dict[str, Any] | None = None,
) -> Any:
    try:
        config = _get_config()
        url = f"{config['base_url']}{path}"
        headers = _build_headers(config, require_auth, extra_headers)
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


def _openapi_base_path(spec: dict[str, Any]) -> str:
    servers = spec.get("servers", [])
    if servers:
        url = servers[0].get("url", "")
        if isinstance(url, str):
            return url.rstrip("/")
    return ""


def _list_openapi_operations(spec: dict[str, Any]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for path, methods in spec.get("paths", {}).items():
        if not isinstance(methods, dict):
            continue
        path_parameters = methods.get("parameters", [])
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                continue
            method_upper = method.upper()
            if method_upper not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
                continue
            operations.append(
                {
                    "method": method_upper,
                    "path": path,
                    "operation": operation,
                    "path_parameters": path_parameters,
                }
            )
    return operations


def _merge_parameters(
    path_parameters: list[dict[str, Any]] | None,
    operation_parameters: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    combined: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for param in (path_parameters or []) + (operation_parameters or []):
        if not isinstance(param, dict):
            continue
        name = param.get("name")
        location = param.get("in")
        if not name or not location:
            continue
        key = (str(name), str(location))
        if key in seen:
            continue
        seen.add(key)
        combined.append(param)
    return combined


def _sanitize_param_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        return "param"
    if value[0].isdigit():
        return f"param_{value}"
    return value


def _param_arg_name(location: str, name: str) -> str:
    prefix = {
        "path": "path",
        "query": "query",
        "header": "header",
        "cookie": "cookie",
    }.get(location, location)
    return _sanitize_param_name(f"{prefix}_{name}")


def _schema_to_python_type(schema: dict[str, Any] | None) -> Any:
    if not isinstance(schema, dict):
        return Any
    if "$ref" in schema:
        return Any
    schema_type = schema.get("type")
    if schema_type == "integer":
        return int
    if schema_type == "number":
        return float
    if schema_type == "boolean":
        return bool
    if schema_type == "string":
        return str
    if schema_type == "array":
        return list[Any]
    if schema_type == "object":
        return dict[str, Any]
    return Any


def _operation_param_specs(entry: dict[str, Any]) -> list[dict[str, Any]]:
    operation = entry.get("operation") or {}
    params = _merge_parameters(
        entry.get("path_parameters"),
        operation.get("parameters"),
    )
    specs: list[dict[str, Any]] = []
    for param in params:
        name = str(param.get("name", ""))
        location = str(param.get("in", ""))
        if not name or not location:
            continue
        schema = param.get("schema") if isinstance(param.get("schema"), dict) else None
        specs.append(
            {
                "name": name,
                "location": location,
                "arg_name": _param_arg_name(location, name),
                "required": bool(param.get("required")),
                "py_type": _schema_to_python_type(schema),
            }
        )
    return specs


def _operation_request_body_spec(operation: dict[str, Any]) -> dict[str, Any] | None:
    request_body = operation.get("requestBody")
    if not isinstance(request_body, dict):
        return None
    content = request_body.get("content")
    if not isinstance(content, dict) or not content:
        return None
    schema = None
    for content_type in ("application/json", "application/*+json"):
        if content_type in content:
            schema = content.get(content_type, {}).get("schema")
            break
    if schema is None:
        first = next(iter(content.values()), {})
        if isinstance(first, dict):
            schema = first.get("schema")
    return {
        "arg_name": "body",
        "required": bool(request_body.get("required")),
        "py_type": _schema_to_python_type(schema if isinstance(schema, dict) else None),
        "schema": schema if isinstance(schema, dict) else None,
    }


def _schema_ref_name(schema: dict[str, Any] | None) -> str | None:
    if not isinstance(schema, dict):
        return None
    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return None
    match = re.match(r"^#/components/schemas/(?P<name>[^/]+)$", ref)
    if not match:
        return None
    return match.group("name")


def _resolve_schema(schema: dict[str, Any] | None, spec: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(schema, dict):
        return None
    ref_name = _schema_ref_name(schema)
    if not ref_name:
        return schema
    components = spec.get("components", {})
    schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
    resolved = schemas.get(ref_name)
    return resolved if isinstance(resolved, dict) else None


def _schema_title(schema: dict[str, Any] | None, spec: dict[str, Any]) -> str | None:
    if not isinstance(schema, dict):
        return None
    if "oneOf" in schema or "anyOf" in schema:
        return None
    schema_type = schema.get("type")
    if schema_type == "array":
        items = schema.get("items")
        item_title = _schema_title(items if isinstance(items, dict) else None, spec)
        if item_title:
            return f"list[{item_title}]"
        return "list"
    if "title" in schema and isinstance(schema.get("title"), str):
        return str(schema.get("title"))
    ref_name = _schema_ref_name(schema)
    if ref_name:
        return ref_name
    if schema_type:
        return str(schema_type)
    return None


def _schema_keys(schema: dict[str, Any] | None, spec: dict[str, Any]) -> list[str]:
    resolved = _resolve_schema(schema, spec) or schema
    if not isinstance(resolved, dict):
        return []
    schema_type = resolved.get("type")
    if schema_type == "array":
        items = resolved.get("items")
        return _schema_keys(items if isinstance(items, dict) else None, spec)
    properties = resolved.get("properties")
    if not isinstance(properties, dict):
        return []
    keys = list(properties.keys())
    return keys[:3]


def _response_schema_info(operation: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    responses = operation.get("responses")
    if not isinstance(responses, dict):
        return {"title": None, "keys": []}
    preferred = ["200", "201", "202", "203", "204", "default"]
    ordered = preferred + [key for key in responses.keys() if key not in preferred]
    for status in ordered:
        response = responses.get(status)
        if not isinstance(response, dict):
            continue
        content = response.get("content")
        if not isinstance(content, dict) or not content:
            if status == "204":
                return {"title": "empty", "keys": []}
            continue
        schema = None
        for content_type in ("application/json", "application/*+json", "*/*"):
            if content_type in content:
                schema = content.get(content_type, {}).get("schema")
                break
        if schema is None:
            first = next(iter(content.values()), {})
            if isinstance(first, dict):
                schema = first.get("schema")
        title = _schema_title(schema if isinstance(schema, dict) else None, spec)
        keys = _schema_keys(schema if isinstance(schema, dict) else None, spec)
        return {"title": title, "keys": keys}
    return {"title": None, "keys": []}


def _format_param_summary(
    param_specs: list[dict[str, Any]],
    body_spec: dict[str, Any] | None,
    spec: dict[str, Any],
) -> str:
    required: dict[str, list[str]] = {"path": [], "query": [], "header": [], "cookie": []}
    for param in param_specs:
        if not param.get("required"):
            continue
        location = str(param.get("location"))
        if location in required:
            required[location].append(str(param.get("name")))
    parts: list[str] = []
    for location in ("path", "query", "header", "cookie"):
        items = required[location]
        if items:
            parts.append(f"{location}({', '.join(items)})")
    if body_spec and body_spec.get("required"):
        schema = body_spec.get("schema") if isinstance(body_spec.get("schema"), dict) else None
        body_title = _schema_title(schema, spec) or "body"
        parts.append(f"body({body_title})")
    if not parts:
        return "params: none"
    return "params: " + "; ".join(parts)


def _example_value(name: str) -> str:
    lowered = name.lower()
    if "id" in lowered:
        return "<id>"
    if "take" in lowered or "limit" in lowered:
        return "1"
    if "page" in lowered:
        return "1"
    if "sort" in lowered:
        return "desc"
    return "<value>"


def _format_example(
    param_specs: list[dict[str, Any]],
    body_spec: dict[str, Any] | None,
) -> str | None:
    example_parts: list[str] = []
    for param in param_specs:
        if not param.get("required"):
            continue
        arg_name = str(param.get("arg_name"))
        example_parts.append(f"{arg_name}={_example_value(arg_name)}")
    if body_spec and body_spec.get("required"):
        example_parts.append("body={...}")
    if not example_parts:
        return None
    return "example: " + ", ".join(example_parts)


def _format_response_hint(info: dict[str, Any], include_keys: bool = True) -> str:
    title = info.get("title") or "response"
    keys = info.get("keys") if include_keys else []
    if keys:
        return f"returns: {title} (keys: {', '.join(keys)})"
    return f"returns: {title}"


def _truncate_description(text: str, max_len: int = 360) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def _sanitize_tool_name(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def _tool_name_for_operation(method: str, path: str, operation: dict[str, Any]) -> str:
    operation_id = operation.get("operationId")
    base = operation_id or f"{method}_{path}"
    base = _sanitize_tool_name(base)
    if not base.startswith("immich_"):
        base = f"immich_{base}"
    return base


def _apply_path_params(path_template: str, path_params: dict[str, Any] | None) -> str:
    params = path_params or {}

    def replacer(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in params:
            raise ValueError(f"Missing path parameter: {name}")
        return quote(str(params[name]), safe="")

    return re.sub(r"{([^}]+)}", replacer, path_template)


def _operation_requires_auth(operation: dict[str, Any], spec: dict[str, Any]) -> bool:
    if "security" in operation:
        return bool(operation.get("security"))
    security = spec.get("security")
    if security is None:
        return False
    return bool(security)


def _operation_admin_only(operation: dict[str, Any]) -> bool:
    return bool(operation.get("x-immich-admin-only"))


def _operation_permission(operation: dict[str, Any]) -> str | None:
    permission = operation.get("x-immich-permission")
    return str(permission) if permission else None


@lru_cache
def _discover_user_profile() -> dict[str, Any]:
    profile = _request("GET", "/api/users/me", require_auth=True)
    if isinstance(profile, dict) and not profile.get("error"):
        return profile
    return {}


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


def _openapi_tool_access() -> dict[str, Any]:
    spec = _fetch_openapi_spec()
    operations = _list_openapi_operations(spec)
    base_path = _openapi_base_path(spec)
    config = _get_config()
    has_auth = bool(config["api_key"] or config["api_token"])
    write_capability = _discover_write_capability()
    profile = _discover_user_profile() if has_auth else {}
    is_admin = bool(profile.get("isAdmin"))

    allowed_tools: list[str] = []
    blocked_tools: list[dict[str, str]] = []
    seen_names: set[str] = set()

    for entry in operations:
        method = entry["method"]
        path = entry["path"]
        operation = entry["operation"]
        tool_name = _tool_name_for_operation(method, path, operation)
        if tool_name in seen_names:
            suffix = 2
            while f"{tool_name}_{suffix}" in seen_names:
                suffix += 1
            tool_name = f"{tool_name}_{suffix}"
        seen_names.add(tool_name)

        requires_auth = _operation_requires_auth(operation, spec)
        if requires_auth and not has_auth:
            blocked_tools.append(
                {
                    "tool": tool_name,
                    "reason": "Missing IMMICH_API_KEY or IMMICH_API_TOKEN",
                }
            )
            continue

        if _operation_admin_only(operation) and not is_admin:
            blocked_tools.append(
                {
                    "tool": tool_name,
                    "reason": "Admin-only endpoint",
                }
            )
            continue

        is_write = method in {"POST", "PUT", "PATCH", "DELETE"}
        if is_write and not bool(write_capability.get("allowed")):
            reason = str(write_capability.get("reason") or "Write capability not allowed")
            blocked_tools.append({"tool": tool_name, "reason": reason})
            continue

        allowed_tools.append(tool_name)

    return {
        "allowed_tools": allowed_tools,
        "blocked_tools": blocked_tools,
        "base_path": base_path,
        "operations": operations,
    }


# def openapi_summary() -> dict[str, Any]:
#     """Return OpenAPI title, version, and path count."""
#     spec = _fetch_openapi_spec()
#     info = spec.get("info", {})
#     paths = spec.get("paths", {})
#     return {
#         "title": info.get("title"),
#         "version": info.get("version"),
#         "path_count": len(paths),
#     }


# def list_openapi_paths(limit: int = 20) -> list[str]:
#     """List OpenAPI method/path entries (limited)."""
#     spec = _fetch_openapi_spec()
#     paths = spec.get("paths", {})
#     entries: list[str] = []
#     for path, methods in paths.items():
#         for method in methods.keys():
#             entries.append(f"{method.upper()} {path}")
#             if len(entries) >= limit:
#                 return entries
#     return entries


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
#        "openapi_summary",
#        "list_openapi_paths",
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
    openapi_access = _openapi_tool_access()
    allowed_tools.extend(openapi_access["allowed_tools"])
    blocked_tools.extend(openapi_access["blocked_tools"])
    return {"allowed_tools": allowed_tools, "blocked_tools": blocked_tools}


def write_capability_report() -> dict[str, str | bool]:
    """Report optional write capability probe results."""
    return _discover_write_capability()


def _register_tools(capabilities: dict[str, dict[str, str | bool]]) -> None:
    for tool_func in (
        # openapi_summary,
        # list_openapi_paths,
        ping_server,
        get_server_info,
        get_server_version,
        tool_access_report,
        write_capability_report,
    ):
        mcp.tool()(tool_func)

    if capabilities.get("get_current_user", {}).get("allowed"):
        mcp.tool()(get_current_user)

    _register_openapi_tools()


def _register_openapi_tools() -> None:
    access = _openapi_tool_access()
    spec = _fetch_openapi_spec()
    base_path = access["base_path"]
    operations = access["operations"]
    allowed = set(access["allowed_tools"])
    used_names: set[str] = set()

    for entry in operations:
        method = entry["method"]
        path = entry["path"]
        operation = entry["operation"]
        tool_name = _tool_name_for_operation(method, path, operation)
        if tool_name in used_names:
            suffix = 2
            while f"{tool_name}_{suffix}" in used_names:
                suffix += 1
            tool_name = f"{tool_name}_{suffix}"
        used_names.add(tool_name)

        if tool_name not in allowed:
            continue

        summary = operation.get("summary") or operation.get("description") or ""
        permission = _operation_permission(operation)
        if permission:
            summary = f"{summary} (permission: {permission})".strip()
        if summary and len(summary) > 140:
            summary = summary[:137].rstrip() + "..."
        description = f"{method} {base_path}{path}"
        if summary:
            description = f"{description} - {summary}"

        requires_auth = _operation_requires_auth(operation, spec)
        param_specs = _operation_param_specs(entry)
        body_spec = _operation_request_body_spec(operation)
        params_summary = _format_param_summary(param_specs, body_spec, spec)
        example_summary = _format_example(param_specs, body_spec)
        response_info = _response_schema_info(operation, spec)
        response_hint = _format_response_hint(response_info, include_keys=True)

        details: list[str] = [params_summary]
        if example_summary:
            details.append(example_summary)
        details.append(response_hint)
        description = " | ".join([description, *details])

        if len(description) > 360 and example_summary:
            description = " | ".join([description.split(" | ")[0], params_summary, response_hint])
        if len(description) > 360 and "(keys:" in response_hint:
            response_hint = _format_response_hint(response_info, include_keys=False)
            description = " | ".join([description.split(" | ")[0], params_summary, response_hint])
        description = _truncate_description(description, 360)

        def _merge_cookie_header(
            headers: dict[str, Any], cookie_name: str, cookie_value: Any
        ) -> None:
            cookie_entry = f"{cookie_name}={cookie_value}"
            existing = headers.get("cookie")
            if existing:
                headers["cookie"] = f"{existing}; {cookie_entry}"
            else:
                headers["cookie"] = cookie_entry

        def _make_tool(
            method: str,
            path_template: str,
            require_auth: bool,
            specs: list[dict[str, Any]],
            request_body: dict[str, Any] | None,
        ):
            def tool(**kwargs: Any) -> Any:
                path_params = dict(kwargs.get("path_params") or {})
                query_params = dict(kwargs.get("query_params") or {})
                headers = dict(kwargs.get("headers") or {})
                json_body = kwargs.get("json_body")

                for spec in specs:
                    arg_name = spec["arg_name"]
                    if arg_name not in kwargs:
                        continue
                    value = kwargs[arg_name]
                    if value is None:
                        continue
                    location = spec["location"]
                    if location == "path":
                        path_params[spec["name"]] = value
                    elif location == "query":
                        query_params[spec["name"]] = value
                    elif location == "header":
                        headers[spec["name"]] = value
                    elif location == "cookie":
                        _merge_cookie_header(headers, spec["name"], value)

                if request_body and "body" in kwargs and kwargs["body"] is not None:
                    json_body = kwargs["body"]

                missing: list[str] = []
                for spec in specs:
                    if not spec["required"]:
                        continue
                    arg_name = spec["arg_name"]
                    location = spec["location"]
                    provided = arg_name in kwargs and kwargs[arg_name] is not None
                    if not provided:
                        if location == "path":
                            provided = spec["name"] in path_params
                        elif location == "query":
                            provided = spec["name"] in query_params
                        elif location == "header":
                            provided = spec["name"] in headers
                        elif location == "cookie":
                            provided = "cookie" in headers
                    if not provided:
                        missing.append(f"{location}:{spec['name']}")
                if request_body and request_body.get("required") and json_body is None:
                    missing.append("body")
                if missing:
                    raise ValueError(
                        "Missing required parameters: " + ", ".join(missing)
                    )

                final_path = _apply_path_params(path_template, path_params)
                full_path = f"{base_path}{final_path}"
                return _request(
                    method,
                    full_path,
                    params=query_params,
                    json_body=json_body,
                    require_auth=require_auth,
                    extra_headers=headers,
                )

            signature_params: list[inspect.Parameter] = []
            annotations: dict[str, Any] = {"return": Any}

            for spec in specs:
                arg_name = spec["arg_name"]
                param_type = spec["py_type"]
                annotations[arg_name] = param_type
                default = inspect._empty if spec["required"] else None
                signature_params.append(
                    inspect.Parameter(
                        arg_name,
                        inspect.Parameter.KEYWORD_ONLY,
                        default=default,
                        annotation=param_type,
                    )
                )

            if request_body:
                body_type = request_body["py_type"]
                annotations["body"] = body_type
                default = inspect._empty if request_body.get("required") else None
                signature_params.append(
                    inspect.Parameter(
                        "body",
                        inspect.Parameter.KEYWORD_ONLY,
                        default=default,
                        annotation=body_type,
                    )
                )

            legacy_type = dict[str, Any] | None
            for legacy_name in ("path_params", "query_params", "headers", "json_body"):
                annotations[legacy_name] = legacy_type
                signature_params.append(
                    inspect.Parameter(
                        legacy_name,
                        inspect.Parameter.KEYWORD_ONLY,
                        default=None,
                        annotation=legacy_type,
                    )
                )

            tool.__signature__ = inspect.Signature(signature_params)
            tool.__annotations__ = annotations
            return tool

        tool_func = _make_tool(method, path, requires_auth, param_specs, body_spec)
        mcp.tool(name=tool_name, description=description)(tool_func)


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
