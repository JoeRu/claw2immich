OPENAPI_SPEC_URL = (
    "https://raw.githubusercontent.com/immich-app/immich/main/open-api/immich-openapi-specs.json"
)
DEFAULT_BASE_URL = "http://localhost:2283"
DEFAULT_TIMEOUT = 10.0
MAX_SUMMARY_LEN = 140
MAX_DESCRIPTION_LEN = 360
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
def build_server_instructions(external_domain: str | None) -> str:
    if external_domain:
        domain_note = f"External domain for link building: {external_domain}. "
    else:
        domain_note = (
            "External domain for link building: call GET /api/server-config "
            "and read externalDomain. "
        )
    return (
        "claw2immich MCP server for Immich. "
        "Use tool descriptions (method/path) to choose OpenAPI tools. "
        f"{domain_note}"
        "Workflow groups: discovery (tool_access_report, write_capability_report, "
        "server config), assets (assets/search), people (people/faces), albums "
        "(albums/share), utilities (server info/version). "
        "Do: check tool_access_report when permissions are uncertain and follow "
        "inputSchema prefixes path_/query_/body. "
        "Don't: guess domains or tool names. "
        "Example instructions string: \"1) Read tool_access_report and server "
        "config. 2) Pick tools by description. 3) Use inputSchema prefixes and "
        "required params.\" "
        "Read docs://usage-guide for more workflow examples and parameter naming."
    )


SERVER_INSTRUCTIONS = build_server_instructions(None)
