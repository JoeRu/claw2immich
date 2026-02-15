---
description: 'Show a summary of the current implementation plan.'
name: 'Plan summary'
argument-hint: 'No arguments.'
agent: 'agent'
---

Show a **plan summary** of the current implementation plan.

## Steps

1. **Read** `ai-docs/overview-features-bugs.xml`.
2. **Calculate** counts:
  - By status: PENDING, APPROVED, IN_PROGRESS, DONE (active only, not archived)
  - By type: feature, bug, refactoring, tech-debt
  - By priority: CRITICAL, HIGH, MEDIUM, LOW
  - Security items count
3. **Identify next actionable items:**
  - APPROVED items ready to start (no unresolved `depends-on`)
  - PENDING items that could be approved
  - IN_PROGRESS items (currently being worked on)
  - Blocked items (waiting on dependencies)
4. **Show archived count** from `<archive>` section.

## Output Format

```
Implementation Plan Summary
============================

Active Items: {total}
  By Status:   PENDING: {n} | APPROVED: {n} | IN_PROGRESS: {n}
  By Type:     Features: {n} | Bugs: {n} | Refactoring: {n} | Tech-debt: {n}
  By Priority: CRITICAL: {n} | HIGH: {n} | MEDIUM: {n} | LOW: {n}
  Security:    {n} items flagged

Archived: {n} items (DONE: {n}, DENIED: {n})

Next Actions:
  Ready to start:
    - Item {ID}: {title} ({type}, {priority})
  Awaiting approval:
    - Item {ID}: {title} ({type}, {priority})
  In progress:
    - Item {ID}: {title} ({type}, {priority})
  Blocked:
    - Item {ID}: {title} – waiting on: {dependency IDs}
```
