---
description: 'Show the current status and details of a specific item.'
name: 'Item status'
argument-hint: 'Item ID.'
agent: 'agent'
---

Show the **current status** of a specific item in the implementation plan.

**Arguments:** `$ARGUMENTS` (item ID)

## Steps

1. **Read** `ai-docs/overview-features-bugs.xml`.
2. **Find** the item with the given ID (check both active items and archive).
3. **Display** the item details:
   - ID, title, type, status, priority, complexity
   - Branch name (if APPROVED or later)
   - `depends-on` with status of each dependency
   - `parent` reference (if sub-item)
   - Tasks list with completion status
   - Security flag and impact (if applicable)
   - Verification/test plan
   - Result block `<r>` (if DONE)
4. If the item is not found, inform the user.

## Output Format

```
Item {ID} "{title}"
  Type: {type} | Status: {status} | Priority: {priority} | Complexity: {complexity}
  Branch: {branch or "not yet assigned"}
  Depends on: {IDs with their statuses, or "none"}
  Parent: {parent ID or "none"}
  Security: {yes/no, categories if yes}
  Tasks: {completed}/{total}
    - [{done/pending}] {task description}
  Verification: {test count} tests planned
```
