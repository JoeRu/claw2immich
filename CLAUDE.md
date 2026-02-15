# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

claw2immich is a Python MCP (Model Context Protocol) server that exposes the Immich REST API. It uses FastMCP for server scaffolding and httpx for HTTP requests to the Immich API. The OpenAPI spec from Immich is the source of truth for API shape.

## Development Setup

- **Python**: >= 3.12
- **Package manager**: uv
- **Dependencies**: `uv sync` to install
- **Run**: `python main.py` (stdio transport for Claude Desktop)
- **Test**: `pytest tests/` (integration tests exist in [tests/](tests/))

## Architecture

- Single entry point in [main.py](main.py) using `FastMCP("claw2immich")` with stdio transport
- MCP tools are defined as plain functions registered via `_register_tools()` based on runtime capability discovery
- `_get_config()` reads `IMMICH_BASE_URL`, `IMMICH_API_KEY`, and `IMMICH_API_TOKEN` from environment variables
- `_request()` handles all HTTP calls; `_probe()` does non-throwing connectivity/permission checks
- `_discover_capabilities()` and `_discover_write_capability()` probe the Immich server at startup to determine which tools to expose
- OpenAPI spec is fetched and cached via `_fetch_openapi_spec()` for introspection tools

## Key Conventions

- No formatter or linter configured; keep style minimal and consistent with existing code
- Immich API key/token handling is security-sensitive — never log secrets
- OpenAPI spec source: https://github.com/immich-app/immich/blob/main/open-api/immich-openapi-specs.json

## AI-Assisted Development Workflow

Read [CLAUDE-implementation-plan-chapter.md](CLAUDE-implementation-plan-chapter.md) for details.

This project uses an XML-based planning system under [ai-docs/](ai-docs/):
- `overview.xml` — project architecture baseline
- `overview-features-bugs.xml` — feature/bug tracking
- `implementation-plan-template-v3.1.xml` — XML schema reference

Workflow prompts live in [.github/prompts/](.github/prompts/). Key ones:
- `init_overview.prompt.md` — baseline codebase scan
- `implement.prompt.md` — plan item execution (max 5 items per invocation)
- `feature.prompt.md`, `bug.prompt.md`, `refactor.prompt.md` — create new items

Item lifecycle: BACKLOG → PENDING → APPROVED → IN_PROGRESS → DONE

## Security

- Security audit process is documented in [security.prompt.md](.github/prompts/security.prompt.md)
- Auth is handled via `_build_headers()` — supports both API key (`x-api-key`) and bearer token
- `require_auth=True` on a request will raise if neither credential is set
