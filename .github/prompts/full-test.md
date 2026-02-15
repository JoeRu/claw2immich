
---
description: 'Executes all available tests in the project.'
name: 'run full test'
agent: 'agent'
---
Executes all available tests in the project, maps failures to items, and sets affected items back to a problem state.

**Process:**

**Step 1 – Discover and run tests:**
1. **Detect** test frameworks and runners (pytest, jest, go test, cargo test, etc.)
2. **Run** the full test suite, capture all output
3. **Parse** results: total, passed, failed, errored, skipped

**Step 2 – Map failures to items:**

For each failed/errored test:
1. **Identify** the failing test file and the source files involved in the failure
2. **Search** `overview-features-bugs.xml` for items whose `<r><files>` or `<verification><tests><file>` match the failing files
3. **Search** `overview.xml` `<completed-features>` for features whose `<files>` or `<test-files>` match
4. **Categorize** the failure:

| Match | Action |
|---|---|
| Maps to a DONE item | Set item `<r><outcome>` to `PROBLEM`, move back from `<archive>` to active items, status → `IN_PROGRESS` |
| Maps to an IN_PROGRESS item | Set `<r><outcome>` to `PROBLEM`, add failure details to `<r><observations>` |
| Maps to a completed feature (CF) | Create new `<item type="bug" status="PENDING">` with `ref-feature="CF-ID"` |
| Maps to no known item or feature | Create new `<item type="bug" status="PENDING">` with file references |
