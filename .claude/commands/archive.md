**Archive** all eligible DONE and DENIED items from the implementation plan.

## Steps

1. **Read** `ai-docs/overview.xml` and `ai-docs/overview-features-bugs.xml`.
2. **Identify eligible items:**
   - `DONE` items: the item AND all its sub-items must be DONE, AND no active item has `depends-on` referencing it.
   - `DENIED` items: archive immediately (should already be archived by `/deny`, but catch any missed ones).
3. **For each eligible item:**
   a. **Move** from active section to `<archive>` in `overview-features-bugs.xml` with `archived="{today's date}"`.
   b. **For DONE items:** add a `<completed-features>` entry in `overview.xml`:
      - `id="CF-{item-id}"`, `completed="{date}"`, `source-item="{item-id}"`
      - Include title, description, files from the item's `<r>` block
   c. **For security items:** update `<security>` section in `overview.xml`:
      - DONE security items: evaluate if mitigation resolved the concern
      - DENIED security items: note that vulnerability is unaddressed
4. **Update** `<metadata><updated>` in `overview.xml`.
5. **Update** architecture, dependencies, or security sections if archived items introduced changes.
6. **Update changelog** in `overview-features-bugs.xml`.
7. **Report** to user:
   - Number of items archived
   - Items that could NOT be archived (and why: active dependents, sub-items not done)
   - Changes to overview.xml

## Important

- Do NOT archive items still referenced by active `depends-on`
- Always update BOTH XML files
- Keep XML valid
