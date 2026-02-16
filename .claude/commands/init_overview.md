Run the **initial code analysis** as described in `CLAUDE-implementation-plan-chapter.md`.

## Steps

1. If `ai-docs/overview.xml` or `ai-docs/overview-features-bugs.xml` already exist, **back them up** as `.bak` files before overwriting.
2. Create the `ai-docs/` directory if it doesn't exist.
3. **Scan the entire codebase** following the analysis steps:
   - Directory structure, languages, frameworks, config files, package manifests
   - Architecture patterns, layers, entry points, data flow
   - System requirements and external dependencies
   - Map all existing features from routes, modules, tests, README
   - Assess feature completeness (`FULL`/`PARTIAL`/`UNKNOWN`) and test coverage (`TESTED`/`PARTIAL`/`NONE`/`UNKNOWN`)
   - Note inbound and outbound interfaces
   - Check for security concerns
   - Detect environments (dev/staging/prod)
4. **Generate** `ai-docs/overview.xml` with the full project baseline using the schema from `CLAUDE-implementation-plan-chapter.md`.
5. **Generate** `ai-docs/overview-features-bugs.xml` with discovered issues, TODOs, and `[REF]` items for features that are not FULL + TESTED. All items start as `status="PENDING"`.
6. Read `ai-docs/implementation-plan-template-v3.1.xml` for the XML schema reference.
7. Report a summary to the user: patterns found, dependencies, features discovered (with completeness breakdown), items created.

## Important

- No item limit for initial analysis
- Every feature not rated FULL + TESTED gets a `[REF]` item in `overview-features-bugs.xml`
- Keep XML valid and well-formed
- Follow the exact XML structure from `CLAUDE-implementation-plan-chapter.md`
