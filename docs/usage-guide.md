# claw2immich MCP Usage Guide

This guide explains how to use the MCP server to discover tools and perform common Immich workflows. It is designed for MCP clients and AI agents.

## Tool Documentation
Tools include:
- `name` and `description` (always includes the HTTP method and path)
- `inputSchema` (JSON Schema for arguments)
- parameter prefixes: `path_`, `query_`, `header_`, `cookie_`, and `body`

Descriptions are enriched with:
- `params:` summary of required path/query/body fields
- `example:` short call sketch when required inputs exist
- `returns:` response schema title and key fields when available

When you need a capability, search for a tool by description. Example: look for a tool whose description begins with `GET /api/assets/{id}` when you need an asset by id.

### Parameter Naming
OpenAPI tool parameters are exposed as explicit fields:
- `path_<name>` for path parameters
- `query_<name>` for query parameters
- `header_<name>` for header parameters
- `cookie_<name>` for cookie parameters
- `body` for JSON request bodies

Legacy parameters (`path_params`, `query_params`, `headers`, `json_body`) still work but are not recommended for new clients.

## Resources and Prompts
- Resources provide readable docs. Use `resources/list` then `resources/read` for `docs://usage-guide`.
- Prompts provide workflow templates for common tasks and can be fetched via `prompts/list` and `prompts/get`.

## Client Handling
Clients automatically receive server info, instructions, capabilities, and tool lists on connect. Use this to inform tool selection and reduce guesswork.

## Workflow Examples
These examples use tool descriptions and parameter prefixes rather than hard-coded tool names.

### Get an Image (Asset by ID)
1. List tools and locate the one whose description starts with `GET /api/assets/{id}`.
2. Call the tool with `path_id` set to the asset id.

Example call:
- Tool: description `GET /api/assets/{id}`
- Args: `{ "path_id": "<asset-id>" }`

### Find a Person
1. Look for tools with descriptions containing `people`, `person`, or `faces` (for example `GET /api/people` or `POST /api/people/search`).
2. If the tool accepts a query, pass `query_<field>` or `body` based on the `inputSchema`.

Example call:
- Tool: description contains `people/search`
- Args: `{ "body": { "name": "Ada" } }`

### Find a Location
1. Look for tools with descriptions containing `locations` or `map` (for example `GET /api/locations` or `POST /api/search/metadata`).
2. Provide query or body fields for the location name or bounding box.

Example call:
- Tool: description contains `locations/search`
- Args: `{ "query_name": "Seattle" }`

### Get the Newest Photo
1. Look for a tool that lists assets (for example `GET /api/assets` or `GET /api/search`).
2. Use query parameters for sorting or filtering by date if available (check `inputSchema`).

Example call:
- Tool: description contains `assets`
- Args: `{ "query_sort": "desc", "query_take": 1 }`

### Upload a Photo
1. Look for tools with descriptions like `POST /api/assets` or `POST /api/assets/upload`.
2. Inspect the `inputSchema` to determine whether to pass `body` or header metadata.
3. Provide the required fields for upload as described by the schema.

Example call:
- Tool: description contains `assets/upload`
- Args: `{ "body": { "filename": "example.jpg", "deviceAssetId": "...", "assetData": "..." } }`

### Share an Album
1. Find tools with descriptions like `POST /api/albums` (create) and `POST /api/albums/{id}/share` or `POST /api/albums/{id}/link`.
2. Use `path_id` for the album id and pass share options via `body`.

Example call:
- Tool: description contains `albums/{id}/share`
- Args: `{ "path_id": "<album-id>", "body": { "allowDownload": true } }`

## Tips
- Always call `tool_access_report` first when permissions are uncertain.
- Write tools only appear when your credentials allow `POST /api/assets` (use `write_capability_report` to see the reason).
- Use tool descriptions to select the right tool without relying on exact names.
