---
description: 'Create a bug item in the implementation plan with optional modifiers.'
name: 'Create bug item'
argument-hint: 'Bug description with optional modifiers.'
agent: 'agent'
---

Create a **bug item** in the implementation plan. The user's argument is the bug description.

**Arguments:** `$ARGUMENTS` (bug description with optional modifiers)

## Steps

1. **Read** `ai-docs/overview.xml` and `ai-docs/overview-features-bugs.xml`.
2. **Parse** the description from `$ARGUMENTS`. Extract optional modifiers:
   - `!critical`, `!high`, `!medium`, `!low` → override priority (default: HIGH for bugs)
   - `!security` → mark as security-relevant
   - `@<ID>` → set `depends-on`
   - `^<ID>` → set `parent` (sub-item of epic)
3. **Search** existing items for duplicates matching the description.
4. **If duplicate found** → inform user, update existing item if needed.
5. **If no duplicate** → create new item:
   - `type="bug"`, `status="PENDING"`, default `priority="HIGH"`
   - Assign next sequential ID
   - Estimate complexity (S/M/L/XL)
   - If `!security`: add `security="true"`, prefix title with `[SECURITY]`, add `<security-impact>` block
   - Add tasks, verification section
6. **Impact check**: identify which existing features could be affected. Warn if any have `completeness != FULL` or `test-coverage == NONE`.
7. **Update changelog** in `overview-features-bugs.xml`.
8. **Confirm** to user: item ID, title, type, priority, status.

## Important

- Never skip `status="PENDING"`
- Always search for duplicates first
- Respect the 5-item-per-interaction limit
- Keep XML valid
