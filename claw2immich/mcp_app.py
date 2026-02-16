from mcp.server.fastmcp import FastMCP

from .config import get_mcp_settings, get_transport_settings
from .constants import SERVER_INSTRUCTIONS
from .prompts import register_prompts_and_resources
from .tooling import _register_tools


def create_mcp() -> FastMCP:
    settings = get_mcp_settings()
    return FastMCP(
        "claw2immich",
        host=settings["host"],
        port=settings["port"],
        log_level=settings["log_level"],
        instructions=SERVER_INSTRUCTIONS,
    )


def run() -> None:
    mcp = create_mcp()
    register_prompts_and_resources(mcp)
    _register_tools(mcp)

    transport, mount_path = get_transport_settings()
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT must be stdio, sse, or streamable-http")
    mcp.run(transport=transport, mount_path=mount_path)
