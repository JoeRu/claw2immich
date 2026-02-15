# Project Guidelines

## Code Style
- Python 3.12+ project metadata in [pyproject.toml](pyproject.toml#L1-L10); current code uses a simple `main()` with `__name__` guard in [main.py](main.py#L1-L6).
- No formatter or linter config is defined in [pyproject.toml](pyproject.toml#L1-L10); keep style minimal and consistent with [main.py](main.py#L1-L6).

## Architecture
- Single-file entry point only; no package modules yet beyond [main.py](main.py#L1-L6).

## Build and Test
- Build: No build command defined in [pyproject.toml](pyproject.toml#L1-L10).
- Test: No test runner or tests configured (README is empty and [pyproject.toml](pyproject.toml#L1-L10) has no test tooling).

## Project Conventions
- AI plan/overview workflows are defined in prompt files; follow [init_overview.prompt.md](.github/prompts/init_overview.prompt.md#L1-L33) for baseline scans and [implement.prompt.md](.github/prompts/implement.prompt.md#L1-L52) for plan item execution.
- Plan artifacts and schema live under ai-docs/, with the template at [ai-docs/implementation-plan-template-v3.1.xml](ai-docs/implementation-plan-template-v3.1.xml).

## Integration Points
- Dependencies suggest HTTP and MCP CLI integration points (`httpx`, `mcp[cli]`), but no usage exists yet in [pyproject.toml](pyproject.toml#L1-L10).

## Security
- Security audit process is documented in [security.prompt.md](.github/prompts/security.prompt.md#L1-L49); no app-level security code exists yet.