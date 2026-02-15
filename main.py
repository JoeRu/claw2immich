from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("claw2immich")  # Name deines Servers

@mcp.tool()
def beispiel_tool(param: str) -> str:
    """Beschreibung: Tut etwas mit param."""
    return f"Ergebnis für {param}"

def main():
    mcp.run(transport="stdio")  # Für lokale Nutzung (z.B. Claude Desktop)

if __name__ == "__main__":
    main()
