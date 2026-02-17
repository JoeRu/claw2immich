from functools import lru_cache

from .config import get_usage_guide_path


@lru_cache
def _load_usage_guide() -> str:
    try:
        with open(get_usage_guide_path(), "r", encoding="utf-8") as guide_file:
            return guide_file.read()
    except OSError as exc:
        return f"Usage guide not available: {exc}"


def register_prompts_and_resources(mcp) -> None:
    @mcp.resource("docs://usage-guide")
    def usage_guide() -> str:
        """Return the MCP usage guide markdown."""
        return _load_usage_guide()

    @mcp.prompt(title="Immich: Get image", description="Retrieve a single image or video asset by its ID.")
    def prompt_get_image(asset_id: str) -> str:
        return (
            "Find the tool whose description starts with 'GET /api/assets/{id}'. "
            "Call it with path_id set to the asset id. "
            f"Asset id: {asset_id}."
        )

    @mcp.prompt(title="Immich: Find person", description="Search for a person by name using people or face endpoints.")
    def prompt_find_person(person_name: str) -> str:
        return (
            "Locate a tool with 'people' or 'person' in the description (often a "
            "search endpoint). "
            "Check inputSchema to decide whether to pass query_ fields or a body "
            "payload. "
            f"Target name: {person_name}."
        )

    @mcp.prompt(title="Immich: Find location", description="Search for assets or places by location name.")
    def prompt_find_location(location_name: str) -> str:
        return (
            "Locate a tool with 'locations' or 'map' in the description. "
            "Provide query_ or body fields based on inputSchema. "
            f"Target location: {location_name}."
        )

    @mcp.prompt(title="Immich: Newest photo", description="Fetch the most recent photos sorted by date.")
    def prompt_newest_photo(limit: int = 1) -> str:
        return (
            "Locate a tool that lists assets (description includes '/api/assets' or "
            "'/api/search'). "
            "Use query parameters for sorting by time desc and limit. "
            f"Limit: {limit}."
        )

    @mcp.prompt(title="Immich: Upload photo", description="Upload a photo or video file to the Immich library.")
    def prompt_upload_photo(filename: str) -> str:
        return (
            "Locate a tool with description starting 'POST /api/assets' or "
            "'POST /api/assets/upload'. "
            "Inspect inputSchema and send required metadata in body. "
            f"Filename: {filename}."
        )

    @mcp.prompt(title="Immich: Share album", description="Share an existing album with other users or via link.")
    def prompt_share_album(album_id: str) -> str:
        return (
            "Locate a tool with description 'POST /api/albums/{id}/share' or "
            "similar. "
            "Call with path_id and body fields for sharing options. "
            f"Album id: {album_id}."
        )

    @mcp.prompt(title="Immich: Search assets", description="Search assets using metadata filters and text queries.")
    def prompt_search_assets(query: str) -> str:
        return (
            "Locate the tool whose description starts with 'POST /api/search/assets'. "
            "Use inputSchema to decide between query_ fields and a body payload. "
            "Prefer body when the schema requires filters or query text. "
            f"Search query: {query}."
        )

    @mcp.prompt(title="Immich: Smart search", description="Run a CLIP-based smart search using natural language queries.")
    def prompt_search_smart(query: str) -> str:
        return (
            "Locate the tool whose description starts with 'POST /api/search/smart'. "
            "Use inputSchema prefixes (query_/body) and provide the search query in body when required. "
            f"Smart search query: {query}."
        )
