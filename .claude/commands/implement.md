---
description: 'Implement one or more items from the plan, verify, and update results.'
name: 'Implement items'
argument-hint: 'Optional item IDs, comma or space-separated. Leave empty for all approved.'
agent: 'agent'
---

**Implement** one or more items from the implementation plan end-to-end.

**Arguments:** `$ARGUMENTS` (optional: one or more item IDs, comma or space-separated. If empty, implement all APPROVED items.)

## Overview

This command takes items through the full lifecycle: analyze → approve (if needed) → implement → verify → update result. It is the primary command for getting work done.

## Steps

### 1. Read Context

- **Read** `ai-docs/overview.xml` (project context, architecture, completed features)
- **Read** `ai-docs/overview-features-bugs.xml` (all items)
- **Read** `CLAUDE.md` for project conventions and development workflow

### 2. Determine Items to Implement

- **If `$ARGUMENTS` contains item IDs**: parse them (support both comma-separated and space-separated). For each ID, verify the item exists in the XML.
- **If `$ARGUMENTS` is empty or not provided**: collect ALL items with `status="APPROVED"` from the XML. If none found, inform the user that there are no APPROVED items to implement and suggest using `/list approved` or `/approve`.
- Reject items that are already `DONE`, `DENIED`, or archived
- Respect the 5-item limit per interaction. If more than 5 items to process, process the first 5 and ask to continue.

### 3. Auto-Approve if Needed

For each item that is NOT yet `APPROVED` or `IN_PROGRESS`:
- If `status="PENDING"`: set to `APPROVED`, generate branch name following `{type}/item-{ID}-{slug}` pattern, populate `<branch>` element
- If `status="BACKLOG"`: set to `APPROVED` with branch name
- **Check dependencies**: if `depends-on` references items that are not DONE, **warn the user** but continue (the user explicitly requested implementation)
- **Security check**: evaluate security impact. Add `security="true"` and `<security-impact>` block if applicable

### 4. Set Status to IN_PROGRESS

- Update each item's status to `IN_PROGRESS` in the XML
- Update `<metadata><updated>` date

### 5. Analyze Each Item

For each item, before writing any code:
1. **Read the item's tasks** and verification/test plan from the XML
2. **Read all files** referenced in the item and related features
3. **Understand the current state** of the code that will be modified or tested
4. **Identify the approach**: what exactly needs to be built, changed, or tested
5. **Check feature completeness**: if changes touch features with `completeness != FULL` or `test-coverage == NONE`, note the risk (the [REF] items themselves are expected to address this)

### 6. Implement

Execute the tasks defined in the item:
- Follow the project conventions from `CLAUDE.md`
- Write clean, focused code – only what the item requires
- For test items ([REF]): set up test framework if needed, write the specified tests
- For features: implement the described functionality
- For bugs: fix the root cause as described in `<analysis>` or `<tasks>`
- For tech-debt: execute the cleanup/migration tasks
- Create files and directories as needed
- **Do NOT create a git branch** – work on the current branch unless the user explicitly requests branching

### 7. Verify

After implementation, verify the work:
- **Run tests** if tests were written or modified (use appropriate test runner for the language)
- **Check for syntax errors** in modified files (lint, parse, compile as appropriate)
- **Manual verification steps**: if `<manual-steps>` are defined, describe what to check and confirm basic functionality
- **If verification fails**: fix the issue and re-verify. If unable to fix, set outcome to `PROBLEM` with observations

### 8. Update Result Block

For each completed item, fill the `<r>` block:

```xml
<r>
  <outcome>DONE</outcome>
  <observations>What was noteworthy during implementation</observations>
  <lessons-learned>Insights for future work</lessons-learned>
  <files>
    <file>path/to/created-or-modified/file</file>
  </files>
</r>
```

- Set `outcome` to `DONE` if verification passed, `PROBLEM` if issues remain
- List ALL files that were created or modified
- Record observations about unexpected findings or decisions made
- Record lessons learned for future reference

### 9. Update Item Status

- If outcome is `DONE`: set `status="DONE"`
- If outcome is `PROBLEM`: keep `status="IN_PROGRESS"`, describe the problem in observations
- For [REF] items that are DONE: note that the corresponding feature in `overview.xml` should have its `test-coverage` updated (but defer actual archival to `/archive`)

### 10. Update Changelog

Add a single changelog entry summarizing all items processed:
```xml
<entry date="YYYY-MM-DD">Items X, Y, Z implemented. [Brief summary of what was done].</entry>
```

### 11. Report to User

For each item, report:
- Item ID, title, final status
- Files created/modified
- Test results (pass/fail counts if applicable)
- Any issues or warnings

## Important Rules

- **Always read the item and related code before implementing** – understand context first
- **Follow existing code patterns** – match the style, conventions, and structure of the existing codebase
- **Run verification** – never mark DONE without testing
- **Update the XML** – the plan must reflect reality after implementation
- **One changelog entry** per `/implement` invocation, not per item
- **Keep XML valid** – malformed XML breaks the workflow
- **Do not over-engineer** – implement exactly what the item describes, nothing more
- **If blocked**: set outcome to PROBLEM, describe the blocker, and inform the user
