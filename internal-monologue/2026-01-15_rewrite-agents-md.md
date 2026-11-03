# Rewrite AGENTS.md

**Requested:** Analyze the codebase and create/improve `AGENTS.md` with commands (incl. single test) and code style guidelines.

**Done:**
- Verified the existing `AGENTS.md` and `.bob/rules-*/AGENTS.md` against code (models, schemas, services, conftest, pytest.ini, start.sh, frontend types/api).
- Rewrote `AGENTS.md`: merged commands, backend/frontend patterns, test setup, and style rules. Removed obvious info.
- Flagged `.bob/rules/basic_rules.md` as stale (three seat classes, wrong multipliers, non-existent `seatClasses.ts`).
- Mode-specific `.bob/rules-*/AGENTS.md` were accurate; left unchanged.
