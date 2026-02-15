# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

claw2immich is a Python MCP (Model Context Protocol) server that exposes the Immich REST API. It uses FastMCP for server scaffolding and httpx for HTTP requests to the Immich API. The OpenAPI spec from Immich is the source of truth for API shape.

## Development Setup

- **Python**: >= 3.12
- **Package manager**: uv
- **Dependencies**: `uv sync` to install
- **Run**: `python main.py` (stdio transport for Claude Desktop)
- **Test**: No test runner configured yet

## Architecture

- Single entry point in `main.py` using `FastMCP("claw2immich")` with stdio transport
- MCP tools are defined as decorated functions (`@mcp.tool()`) that map to Immich API endpoints
- httpx is used for all HTTP calls to the Immich REST API
- No package modules yet — currently a single-file structure

## AI-Assisted Development Workflow
Read `CLAUDE-implementation-plan-chapter.md` for details.

This project uses an XML-based planning system under `ai-docs/`:
- `overview.xml` — project architecture baseline
- `overview-features-bugs.xml` — feature/bug tracking
- `implementation-plan.xml` — current roadmap
- `implementation-plan-template-v3.1.xml` — XML schema reference

Workflow prompts live in `.github/prompts/`. Key ones:
- `init_overview.prompt.md` — baseline codebase scan
- `implement.prompt.md` — plan item execution (max 5 items per invocation)
- `feature.prompt.md`, `bug.prompt.md`, `refactor.prompt.md` — create new items

Item lifecycle: BACKLOG → PENDING → APPROVED → IN_PROGRESS → DONE

## Key Conventions

- No formatter or linter configured; keep style minimal and consistent with existing code
- Immich API key/token handling is security-sensitive — never log secrets
- OpenAPI spec source: https://github.com/immich-app/immich/blob/main/open-api/immich-openapi-specs.json
