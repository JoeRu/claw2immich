OPENAPI_SPEC_URL = (
    "https://raw.githubusercontent.com/immich-app/immich/main/open-api/immich-openapi-specs.json"
)
DEFAULT_BASE_URL = "http://localhost:2283"
DEFAULT_TIMEOUT = 10.0
MAX_SUMMARY_LEN = 140
MAX_DESCRIPTION_LEN = 360
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SERVER_INSTRUCTIONS = (
    "claw2immich MCP server for Immich. "
    "Use tool descriptions (method/path) to choose OpenAPI tools. "
    "Read docs://usage-guide for workflow examples and parameter naming."
)
