import logging

from mcp.server.fastmcp import FastMCP

from .config import get_mcp_settings, get_transport_settings, get_external_domain
from .constants import build_server_instructions
from .http_client import _request
from .prompts import register_prompts_and_resources
from .tooling import _register_tools

logger = logging.getLogger(__name__)


def _resolve_external_domain() -> str | None:
    """Get external domain from config (which handles all fallback logic)."""
    return get_external_domain()


def create_mcp() -> FastMCP:
    logger.info("Creating MCP server")
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
    logger.info("Starting MCP server run loop")
    mcp = create_mcp()
    register_prompts_and_resources(mcp)
    _register_tools(mcp)

    transport, mount_path = get_transport_settings()
    logger.info(f"Using transport: {transport}")
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT must be stdio, sse, or streamable-http")
    mcp.run(transport=transport, mount_path=mount_path)
