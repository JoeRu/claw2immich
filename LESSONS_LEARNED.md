# Lessons Learned

- Keep architecture notes and file mappings current after refactors to avoid drift.
- Validate XML structure after large plan edits to prevent malformed tracking files.
- Test modules may rely on imports in entry point files even if unused in production code.
- Verify documentation completeness before assuming new content is needed; related features may have already addressed the requirement.
- Docker compose examples should use commented lines with ${VAR:-default} pattern for optional configuration to guide users while keeping defaults clean.
- Regular update scans verify XMLs match codebase reality and catch orphaned items or new features.
- Helper utilities for development/maintenance workflows don't need feature tracking as they're dev-only tools not part of the product.
