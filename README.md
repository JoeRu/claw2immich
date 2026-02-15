# claw2immich

Fresh project. The goal is to build an MCP server that exposes the Immich REST API.

## Goals
- Provide an MCP server interface for Immich endpoints.
- Keep the OpenAPI spec as the source of truth for API shape.

## Scope
### In scope
- MCP server scaffolding and tool definitions for Immich endpoints.
- Configuration for Immich base URL and API key/token.

### Out of scope
- Full Immich client UI.
- Production deployment or hosting.

## OpenAPI spec
Source: https://github.com/immich-app/immich/blob/main/open-api/immich-openapi-specs.json

Workflow (manual for now):
1. Download the latest spec when Immich updates.
2. Reconcile endpoint/tool mappings against the new spec.
3. Update any generated or hand-written mappings.

## Run (placeholder)
```
python main.py
```

## Test (placeholder)
No test runner configured yet.
Project to implement a MCP Server for Immich