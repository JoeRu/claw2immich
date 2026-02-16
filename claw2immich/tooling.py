import inspect
from typing import Any

from .capabilities import (
    _discover_capabilities,
    _discover_user_profile,
    _discover_write_capability,
)
from .config import _get_config
from .constants import MAX_DESCRIPTION_LEN, MAX_SUMMARY_LEN, WRITE_METHODS
from .http_client import _request
from .openapi import (
    _apply_path_params,
    _fetch_openapi_spec,
    _format_example,
    _format_param_summary,
    _format_response_hint,
    _list_openapi_operations,
    _openapi_base_path,
    _operation_admin_only,
    _operation_param_specs,
    _operation_permission,
    _operation_request_body_spec,
    _operation_requires_auth,
    _response_schema_info,
    _tool_name_for_operation,
    _truncate_description,
)


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

        is_write = method in WRITE_METHODS
        if is_write and not bool(write_capability.get("allowed")):
            reason = str(
                write_capability.get("reason") or "Write capability not allowed"
            )
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
        # "openapi_summary",
        # "list_openapi_paths",
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


def _register_tools(mcp) -> None:
    capabilities = _discover_capabilities()
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

    _register_openapi_tools(mcp)


def _register_openapi_tools(mcp) -> None:
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
        if summary and len(summary) > MAX_SUMMARY_LEN:
            summary = summary[: MAX_SUMMARY_LEN - 3].rstrip() + "..."
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

        if len(description) > MAX_DESCRIPTION_LEN and example_summary:
            description = " | ".join(
                [description.split(" | ")[0], params_summary, response_hint]
            )
        if len(description) > MAX_DESCRIPTION_LEN and "(keys:" in response_hint:
            response_hint = _format_response_hint(response_info, include_keys=False)
            description = " | ".join(
                [description.split(" | ")[0], params_summary, response_hint]
            )
        description = _truncate_description(description, MAX_DESCRIPTION_LEN)

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

                if (
                    request_body
                    and "body" in kwargs
                    and kwargs["body"] is not None
                ):
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
                if (
                    request_body
                    and request_body.get("required")
                    and json_body is None
                ):
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
                default = (
                    inspect._empty if request_body.get("required") else None
                )
                signature_params.append(
                    inspect.Parameter(
                        "body",
                        inspect.Parameter.KEYWORD_ONLY,
                        default=default,
                        annotation=body_type,
                    )
                )

            legacy_type = dict[str, Any] | None
            for legacy_name in (
                "path_params",
                "query_params",
                "headers",
                "json_body",
            ):
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
