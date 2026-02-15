---
description: 'Re-analyzes and replans an existing item based on new knowledge.'
name: 'update item'
argument-hint: 'Item ID.'
agent: 'agent'
---
Re-analyzes and replans an existing item based on new knowledge, changed requirements, or insights gained during implementation.

**Arguments:** `$ARGUMENTS` (item ID, context)

**Process:**

1. **Load** the item and all its related context:
   - The item itself (tasks, verification, result, security-impact)
   - Parent and child items (if epic)
   - Items in its `depends-on` chain
   - Affected files from `overview.xml` completed-features
   - Current state of referenced files in codebase

2. **Analyze** what changed:
   - New information provided by user in `[context]`
   - Code changes since the item was last updated
   - New dependencies or conflicts with other items
   - Resolved or new gaps in understanding

3. **Replan** the item:
   - Update `<justification>` if the reason changed
   - Revise `<tasks>` – add, remove, or rewrite tasks based on new knowledge
   - Revise `<verification>` – update tests if scope changed
   - Re-assess `complexity` – upgrade/downgrade based on new understanding
   - Re-assess `priority` – escalate or de-escalate as needed
   - Re-evaluate `<security-impact>` if `security="true"`
   - Update `<risks>` with newly discovered risks
   - For epics: re-evaluate `<acceptance-criteria>` and child items

4. **Preserve history** – add a `<replan>` entry inside the item:
   ```xml
   <replan date="2026-02-10">
     <reason>User provided context / new insight discovered</reason>
     <changes>Tasks 12.2–12.3 rewritten, complexity M→L, added security-impact</changes>
   </replan>
   ```

5. **Report** changes to user with before/after comparison

**Status rules for `/update-item`:**
- `PENDING` items: replan freely, status stays PENDING
- `APPROVED` items: replan, status stays APPROVED (user already authorized direction)
- `IN_PROGRESS` items: replan, status **resets to APPROVED** (user must re-confirm before continuing)
- `DONE` items: cannot replan – create a new item instead, or use `/update-item` on a `[REF]` item

**Examples:**
```
/update-item 12 We decided to use OAuth2 PKCE instead of implicit flow
→ Item 12 "OAuth Integration":
  BEFORE: 3 tasks, complexity M, no security-impact
  AFTER:  5 tasks, complexity L, security="true" (AUTH)
  - Task 12.1 rewritten: "Implement PKCE flow" (was "Implement implicit flow")
  - Task 12.4 added: "Remove implicit flow redirect URIs"
  - Task 12.5 added: "Add PKCE code_verifier validation test"
  - Complexity: M → L
  - Added security-impact: AUTH category
  - Replan entry recorded
→ Status remains APPROVED

/update-item 20 Root cause found – it's a connection pool issue not a race condition
→ Item 20 "Intermittent auth failures":
  BEFORE: hypothesis H1 CONFIRMED (race condition), 2 tasks
  AFTER:  hypothesis H1 REJECTED, H2 CONFIRMED (connection pool), 3 tasks
  - Analysis updated: root-cause changed to H2
  - Tasks completely rewritten for connection pool fix
  - Replan entry recorded
→ Status: IN_PROGRESS → APPROVED (reset, needs re-confirmation)
```