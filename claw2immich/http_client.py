from typing import Any

import httpx

from .config import _get_config
from .constants import DEFAULT_TIMEOUT


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
        raise ValueError(
            "IMMICH_API_KEY or IMMICH_API_TOKEN must be set for this call"
        )
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
