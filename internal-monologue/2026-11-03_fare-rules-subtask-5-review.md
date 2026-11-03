# Sub-Task 5 review

**Requested:** Verify Sub-Task 5 (repair and extend backend tests).

**Done:**
- Ran `pytest` from `booking_system_backend/`: 102 passed, 4 warnings (existing Pydantic class-config deprecations). A single node id also passed.
- Checked `AGENTS.md` now documents `REFUND_RULES`, the preview route and tool, and the `make_flight` / `make_booking` fixtures, and no longer calls the fixtures stale.
- Noted pytest recreates `booking.db` via the app lifespan (existing behaviour); deleted it again.
- Gap noted: no dedicated test for the MCP `get_refund_preview` tool.
