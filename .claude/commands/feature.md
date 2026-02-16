Create a **feature item** in the implementation plan. The user's argument is the feature description.

**Arguments:** `$ARGUMENTS` (feature description with optional modifiers)

## Steps

1. **Read** `ai-docs/overview.xml` and `ai-docs/overview-features-bugs.xml`.
2. **Parse** the description from `$ARGUMENTS`. Extract optional modifiers:
   - `!critical`, `!high`, `!medium`, `!low` → override priority (default: MEDIUM for features)
   - `!security` → mark as security-relevant
   - `@<ID>` → set `depends-on`
   - `^<ID>` → set `parent` (sub-item of epic)
3. **Search** existing items for duplicates matching the description.
4. **If duplicate found** → inform user, update existing item if needed.
5. **If no duplicate** → create new item:
   - `type="feature"`, `status="PENDING"`, default `priority="MEDIUM"`
   - Assign next sequential ID
   - Estimate complexity (S/M/L/XL). If XL → create epic with `<acceptance-criteria>` and sub-items
   - If `!security`: add `security="true"`, add `<security-impact>` block
   - Add justification, tasks, verification section
6. **Impact check**: identify which existing features could be affected. Warn if any have `completeness != FULL` or `test-coverage == NONE`.
7. **Update changelog** in `overview-features-bugs.xml`.
8. **Confirm** to user: item ID, title, type, priority, status, complexity.

## Important

- Never skip `status="PENDING"`
- Always search for duplicates first
- XL items must be decomposed into sub-items
- Respect the 5-item-per-interaction limit
- Keep XML valid
