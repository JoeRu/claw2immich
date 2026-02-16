import os
from functools import lru_cache
from typing import Any

from .config import _get_config
from .http_client import _probe, _request


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


def _write_probe_settings() -> tuple[str, str]:
    method = os.getenv("IMMICH_WRITE_PROBE_METHOD", "POST").strip().upper()
    if not method:
        method = "POST"
    path = os.getenv("IMMICH_WRITE_PROBE_PATH", "").strip()
    if not path:
        path = "/api/assets"
    return method, path
