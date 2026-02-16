import os
from functools import lru_cache
from typing import Any

from .config import _get_config
from .http_client import _probe, _request


def _format_probe_failure(method: str, path: str, probe: dict[str, Any]) -> str:
    status_code = probe.get("status_code")
    if isinstance(status_code, int):
        return f"Capability check failed (HTTP {status_code}) for {method} {path}"
    error = probe.get("error")
    detail = probe.get("detail")
    if error and detail:
        return f"Capability check failed: {error} ({detail})"
    if error:
        return f"Capability check failed: {error}"
    if detail:
        return f"Capability check failed: {detail}"
    return "Immich server error during capability check"


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

    capabilities["get_current_user"]["reason"] = _format_probe_failure(
        "GET", "/api/users/me", probe
    )
    return capabilities


@lru_cache
def _discover_write_capability() -> dict[str, str | bool]:
    method, path = _write_probe_settings()

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

    if status_code == 400:
        return {
            "configured": True,
            "allowed": True,
            "reason": "Allowed (write probe returned validation error)",
        }

    return {
        "configured": True,
        "allowed": False,
        "reason": _format_probe_failure(method, path, probe),
    }


def _write_probe_settings() -> tuple[str, str]:
    method = os.getenv("IMMICH_WRITE_PROBE_METHOD", "POST").strip().upper()
    if not method:
        method = "POST"
    path = os.getenv("IMMICH_WRITE_PROBE_PATH", "").strip()
    if not path:
        path = "/api/assets"
    return method, path
