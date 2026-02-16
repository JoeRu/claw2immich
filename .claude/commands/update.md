Run code analysis in **update mode** as described in `CLAUDE-implementation-plan-chapter.md`.

**Precondition:** Both `ai-docs/overview.xml` and `ai-docs/overview-features-bugs.xml` must already exist. If they don't, inform the user to run `/init` first.

## Steps

1. **Read** both XML files.
2. **Scan the codebase** (same analysis steps as `/init`).
3. **Step 1 – Drift detection on overview.xml:**
   - Compare architecture, system requirements, external dependencies, interfaces, environments, security against current codebase
   - Update any mismatches
4. **Step 2 – Feature verification:**
   - Verify files still exist for each feature in `<completed-features>`
   - Check for new files belonging to existing features
   - Re-assess completeness and test-coverage
   - Discover new features not yet in overview.xml → add them + create `[REF]` items if needed
   - Flag STALE features where files were deleted/renamed
5. **Step 3 – Item verification on overview-features-bugs.xml:**
   - Verify referenced files still exist
   - Check `depends-on` and `parent` references are still valid
   - Flag stale items (PENDING/APPROVED for too long without progress)
6. **Step 4 – Report** a verification summary to the user using the format from the chapter:
   - overview.xml changes
   - Feature verification results (OK / changed / STALE / NEW)
   - Item warnings (stale, broken refs)
   - Count of changes made and items created
7. **Update changelog** in `overview-features-bugs.xml`.

## Important

- Do NOT recreate the files from scratch – update them in place
- Keep XML valid
- Update `<metadata><updated>` in overview.xml
