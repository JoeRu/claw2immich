import os
from pathlib import Path
from typing import Any

from .constants import DEFAULT_BASE_URL


def get_mcp_settings() -> dict[str, Any]:
    host = os.getenv("MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port_raw = os.getenv("MCP_PORT", "8000").strip()
    log_level = os.getenv("MCP_LOG_LEVEL", "INFO").strip().upper() or "INFO"
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError("MCP_PORT must be an integer") from exc
    return {"host": host, "port": port, "log_level": log_level}


def get_transport_settings() -> tuple[str, str | None]:
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
    mount_path = os.getenv("MCP_MOUNT_PATH", "").strip() or None
    return transport, mount_path


def _get_config() -> dict[str, str]:
    base_url = os.getenv("IMMICH_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    api_key = os.getenv("IMMICH_API_KEY", "").strip()
    api_token = os.getenv("IMMICH_API_TOKEN", "").strip()
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        raise ValueError("IMMICH_BASE_URL must start with http:// or https://")
    return {"base_url": base_url, "api_key": api_key, "api_token": api_token}


def get_usage_guide_path() -> str:
    base_dir = Path(__file__).resolve().parents[1]
    return str(base_dir / "docs" / "usage-guide.md")
