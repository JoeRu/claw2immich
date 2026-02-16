Run a **security audit** of the codebase.

**Arguments:** `$ARGUMENTS` (optional: specific area like "auth", "api", or "status")

## Modes

### `/security` (no arguments) – Full audit
1. **Read** `ai-docs/overview.xml` security section and all items with `security="true"` in `overview-features-bugs.xml`.
2. **Scan the codebase** against all 7 security categories:
   - **AUTH**: Authentication, authorization, session management, token handling
   - **INPUT**: Injection (SQL, XSS, command), validation, sanitization
   - **DATA**: Storage encryption, PII handling, data leakage, backup security
   - **NETWORK**: TLS, CORS, CSP, SSRF, API security, rate limiting
   - **CRYPTO**: Key management, hashing, signing, random number generation
   - **ACCESS**: File permissions, path traversal, privilege escalation
   - **DISCLOSURE**: Error messages, stack traces, debug endpoints, version exposure
3. **Cross-reference** with existing security items to avoid duplicates.
4. **Create bug items** for each new finding:
   - `type="bug"`, `security="true"`, `status="PENDING"`
   - Title prefixed with `[SECURITY]`
   - `priority="HIGH"` minimum, `CRITICAL` if exploitable without auth or affects data integrity
   - Full `<security-impact>` block
5. **Update** `<security>` section in `overview.xml` with new concerns.
6. **Update changelog**.
7. **Report** summary: total findings, by category, by severity, new vs. already tracked.

### `/security <area>` – Focused audit
Same process but limited to the specified area (e.g., "auth" → AUTH category, "api" → INPUT + NETWORK).

### `/security status` – Security posture overview
1. Read both XML files.
2. Report:
   - Open concerns in `overview.xml`
   - Security items by status (PENDING, IN_PROGRESS, DONE)
   - Uncovered areas (categories with no items or old audits)

## Important

- Respect the 5-item-per-interaction limit for new findings
- Security bugs default to `priority="HIGH"` minimum
- Always cross-reference to avoid duplicates
- Keep XML valid
