# Plan: fare rules and refunds

**Requested:** A well-structured plan for the fare rules and refunds feature.

**Done:**
- Ran an explore sub-agent over backend and frontend, then verified the key files directly (`seed.py`, `server.py`, `services/`, `test_services.py`).
- Asked how policy text should reach the frontend. User chose a static label map in `src/types/index.ts`, plus a preview REST route and MCP tool.
- Wrote `fare-rules-refunds-plan.md` with 9 sub-tasks, all pending.
- Found the existing service and REST tests build `Flight` with the removed `seats_available` and `Booking` without `seat_class`, so the plan includes repairing them.
