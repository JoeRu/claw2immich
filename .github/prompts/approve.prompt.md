---
description: 'Approve one or more implementation-plan items and assign branches.'
name: 'Approve items'
argument-hint: 'Item IDs, space-separated.'
agent: 'agent'
---

**Approve** one or more items in the implementation plan.

**Arguments:** `$ARGUMENTS` (one or more item IDs, space-separated)

## Steps

1. **Read** `ai-docs/overview.xml` and `ai-docs/overview-features-bugs.xml`.
2. **Parse** item IDs from `$ARGUMENTS`.
3. **Respect the 5-item limit** – if more than 5 IDs provided, process the first 5 and ask for confirmation to continue.
4. For each item ID:
   a. **Verify** the item exists and has `status="PENDING"`.
   b. **Check dependencies** – if `depends-on` references items that are not DONE, warn the user.
   c. **Set** `status="APPROVED"`.
   d. **Generate branch name** following the pattern `{type}/item-{ID}-{slug}` (max 5 words, kebab-case from title).
   e. **Populate** `<branch>` element in the item.
   f. **Security check** – evaluate security impact if not already done. Add `security="true"` and `<security-impact>` if applicable.
5. **Update changelog** in `overview-features-bugs.xml`.
6. **Confirm** to user: for each item show ID, title, new status, branch name.

## Important

- Only PENDING items can be approved
- Always generate branch names on approval
- Warn about unresolved dependencies
- Keep XML valid
