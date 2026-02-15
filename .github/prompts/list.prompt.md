---
description: 'List implementation-plan items with optional filters.'
name: 'List items'
argument-hint: 'Optional filters: status, type, priority, or security.'
agent: 'agent'
---

**List items** from the implementation plan with optional filtering.

**Arguments:** `$ARGUMENTS` (optional filter: status, type, priority, or "security")

## Steps

1. **Read** `ai-docs/overview-features-bugs.xml`.
2. **Parse filter** from `$ARGUMENTS`. Supported filters (can be combined):
   - **By status:** `pending`, `approved`, `in_progress`, `done`, `denied`
   - **By type:** `feature`, `bug`, `refactoring`, `tech-debt`
   - **By priority:** `critical`, `high`, `medium`, `low`
   - **Special:** `security` (all items with `security="true"`)
   - **No filter:** show all active (non-archived) items
3. **Display** matching items in a compact table format:

## Output Format

```
{filter description or "All active items"} ({count} items)

ID | Type        | Priority | Status      | Complexity | Title
---|-------------|----------|-------------|------------|------
 1 | feature     | HIGH     | APPROVED    | M          | OAuth integration
 2 | bug         | CRITICAL | IN_PROGRESS | S          | [SECURITY] SQL injection
 3 | refactoring | MEDIUM   | PENDING     | L          | [REF] Payment flow mapping
```

4. If no items match the filter, inform the user.
5. At the bottom, show a brief summary: total count, breakdown by status.

## Examples

- `/list` → all active items
- `/list pending` → only PENDING items
- `/list bug high` → HIGH priority bugs
- `/list security` → all security-flagged items
- `/list feature pending` → PENDING features
