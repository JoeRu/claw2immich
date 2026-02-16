**Deny** an item in the implementation plan and archive it immediately.

**Arguments:** `$ARGUMENTS` (item ID followed by optional reason)

## Steps

1. **Read** `ai-docs/overview.xml` and `ai-docs/overview-features-bugs.xml`.
2. **Parse** `$ARGUMENTS`: first token is the item ID, rest is the denial reason.
3. **Verify** the item exists and has `status="PENDING"` or `status="APPROVED"`.
4. **Set** `status="DENIED"`.
5. **Add** the denial reason to the item's `<justification>` or as a note.
6. **Archive immediately**:
   - Move the item from active section to `<archive>` in `overview-features-bugs.xml`.
   - If the item has `security="true"` and the denial leaves a vulnerability unaddressed, add/keep the corresponding `<concern>` in `overview.xml` with a note.
7. **Check** if any other items have `depends-on` referencing this denied item → warn the user about broken dependencies.
8. **Update changelog** in `overview-features-bugs.xml`.
9. **Confirm** to user: item ID, title, DENIED status, reason.

## Important

- DENIED items are archived immediately
- Check for broken dependency chains
- Update security section in overview.xml if security item is denied without resolution
- Keep XML valid
