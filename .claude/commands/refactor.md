Create a **refactoring item** in the implementation plan. The user's argument is the refactoring description.

**Arguments:** `$ARGUMENTS` (refactoring description with optional modifiers)

## Steps

1. **Read** `ai-docs/overview.xml` and `ai-docs/overview-features-bugs.xml`.
2. **Parse** the description from `$ARGUMENTS`. Extract optional modifiers:
   - `!critical`, `!high`, `!medium`, `!low` → override priority (default: MEDIUM)
   - `!security` → mark as security-relevant
   - `@<ID>` → set `depends-on`
   - `^<ID>` → set `parent` (sub-item of epic)
3. **Search** existing items for duplicates.
4. **If duplicate found** → inform user, update existing item if needed.
5. **If no duplicate** → create new item:
   - `type="refactoring"`, `status="PENDING"`, default `priority="MEDIUM"`
   - Assign next sequential ID
   - Estimate complexity (S/M/L/XL)
   - If `!security`: add `security="true"`, add `<security-impact>` block
   - Add justification, tasks, verification section
6. **Impact check**: identify affected features. Warn if any have incomplete mapping or missing tests.
7. **Update changelog** in `overview-features-bugs.xml`.
8. **Confirm** to user: item ID, title, type, priority, status.

## Important

- Never skip `status="PENDING"`
- Always search for duplicates first
- Respect the 5-item-per-interaction limit
- Keep XML valid
