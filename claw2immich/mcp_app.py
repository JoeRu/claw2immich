from mcp.server.fastmcp import FastMCP

from .config import get_mcp_settings, get_transport_settings
from .constants import build_server_instructions
from .http_client import _request
from .prompts import register_prompts_and_resources
from .tooling import _register_tools


def _resolve_external_domain() -> str | None:
    payload = _request("GET", "/api/server-config")
    if isinstance(payload, dict) and not payload.get("error"):
        domain = payload.get("externalDomain") or payload.get("external_domain")
        if isinstance(domain, str) and domain.strip():
            return domain.strip()
    return None


def create_mcp() -> FastMCP:
    settings = get_mcp_settings()
    instructions = build_server_instructions(_resolve_external_domain())
    return FastMCP(
        "claw2immich",
        host=settings["host"],
        port=settings["port"],
        log_level=settings["log_level"],
        instructions=instructions,
    )


def run() -> None:
    mcp = create_mcp()
    register_prompts_and_resources(mcp)
    _register_tools(mcp)

    transport, mount_path = get_transport_settings()
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT must be stdio, sse, or streamable-http")
    mcp.run(transport=transport, mount_path=mount_path)
