import re
from functools import lru_cache
from typing import Any
from urllib.parse import quote

import httpx

from .constants import (
    DEFAULT_TIMEOUT,
    HTTP_METHODS,
    MAX_DESCRIPTION_LEN,
    OPENAPI_SPEC_URL,
)
from .http_client import _probe, _request


def _permission_is_read(permission: str | None) -> bool:
    if not permission:
        return False
    upper = permission.upper()
    if "READ" not in upper:
        return False
    if any(token in upper for token in ("WRITE", "UPLOAD", "CREATE", "DELETE")):
        return False
    return True


def _version_tag_from_payload(payload: dict[str, Any]) -> str:
    major = payload.get("major")
    minor = payload.get("minor")
    patch = payload.get("patch")
    if not all(isinstance(value, int) for value in (major, minor, patch)):
        raise ValueError("Immich server version payload is missing major/minor/patch")
    return f"v{major}.{minor}.{patch}"


def _versioned_spec_url(version_tag: str) -> str:
    return (
        "https://raw.githubusercontent.com/immich-app/immich/"
        f"{version_tag}/open-api/immich-openapi-specs.json"
    )


def _require_server_health() -> None:
    health = _probe("GET", "/api/health")
    if health.get("ok"):
        return
    status_code = health.get("status_code")
    if status_code == 404:
        fallback = _probe("GET", "/api/server/ping")
        if fallback.get("ok"):
            return
        detail = fallback.get("detail") or fallback.get("error") or "unknown error"
        raise ValueError(f"Immich health check failed: {detail}")
    detail = health.get("detail") or health.get("error") or "unknown error"
    raise ValueError(f"Immich health check failed: {detail}")


@lru_cache
def _fetch_openapi_spec() -> dict[str, Any]:
    _require_server_health()

    version_payload = _request("GET", "/api/server/version")
    if not isinstance(version_payload, dict) or version_payload.get("error"):
        detail = (
            version_payload.get("detail")
            if isinstance(version_payload, dict)
            else "unknown error"
        )
        raise ValueError(f"Failed to fetch Immich server version: {detail}")

    version_tag = _version_tag_from_payload(version_payload)
    spec_url = _versioned_spec_url(version_tag)

    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        response = client.get(spec_url)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ValueError(
            f"OpenAPI spec not available for {version_tag}: "
            f"HTTP {exc.response.status_code}"
        ) from exc
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
            if method_upper not in HTTP_METHODS:
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
        schema = (
            param.get("schema")
            if isinstance(param.get("schema"), dict)
            else None
        )
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
        "py_type": _schema_to_python_type(
            schema if isinstance(schema, dict) else None
        ),
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


def _resolve_schema(
    schema: dict[str, Any] | None,
    spec: dict[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(schema, dict):
        return None
    ref_name = _schema_ref_name(schema)
    if not ref_name:
        return schema
    components = spec.get("components", {})
    schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
    resolved = schemas.get(ref_name)
    return resolved if isinstance(resolved, dict) else None


def _schema_title(
    schema: dict[str, Any] | None,
    spec: dict[str, Any],
) -> str | None:
    if not isinstance(schema, dict):
        return None
    if "oneOf" in schema or "anyOf" in schema:
        return None
    schema_type = schema.get("type")
    if schema_type == "array":
        items = schema.get("items")
        item_title = _schema_title(
            items if isinstance(items, dict) else None,
            spec,
        )
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


def _schema_keys(
    schema: dict[str, Any] | None,
    spec: dict[str, Any],
) -> list[str]:
    resolved = _resolve_schema(schema, spec) or schema
    if not isinstance(resolved, dict):
        return []
    schema_type = resolved.get("type")
    if schema_type == "array":
        items = resolved.get("items")
        return _schema_keys(
            items if isinstance(items, dict) else None,
            spec,
        )
    properties = resolved.get("properties")
    if not isinstance(properties, dict):
        return []
    keys = list(properties.keys())
    return keys[:3]


def _response_schema_info(
    operation: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any]:
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
        title = _schema_title(
            schema if isinstance(schema, dict) else None,
            spec,
        )
        keys = _schema_keys(
            schema if isinstance(schema, dict) else None,
            spec,
        )
        return {"title": title, "keys": keys}
    return {"title": None, "keys": []}


def _format_param_summary(
    param_specs: list[dict[str, Any]],
    body_spec: dict[str, Any] | None,
    spec: dict[str, Any],
) -> str:
    required: dict[str, list[str]] = {
        "path": [],
        "query": [],
        "header": [],
        "cookie": [],
    }
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
        schema = (
            body_spec.get("schema")
            if isinstance(body_spec.get("schema"), dict)
            else None
        )
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


def _truncate_description(text: str, max_len: int = MAX_DESCRIPTION_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def _sanitize_tool_name(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def _tool_name_for_operation(
    method: str,
    path: str,
    operation: dict[str, Any],
) -> str:
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
