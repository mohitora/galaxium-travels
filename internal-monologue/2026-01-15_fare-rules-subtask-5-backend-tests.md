# Fare rules Sub-Task 5 — backend tests

**Requested:** Implement only Sub-Task 5 of `fare-rules-refunds-plan.md`: repair stale tests/fixtures and add refund tests.

**Done:**
- `tests/conftest.py`: fixed `sample_flight_data` / `sample_booking_data`; added `iso_utc`, `make_flight` (departure relative to now) and `make_booking` factories.
- `tests/test_services.py`, `tests/test_rest.py`: replaced `seats_available` with the four per-class seat columns, added `seat_class` to every `Booking` and `/book` body. Added service tests for `get_refund_preview` and refund behaviour of `cancel_booking`, and REST tests for `GET /refund-preview/{id}` and `refund_amount` in `/cancel`.
- New `tests/test_refund_rules.py`: direct tests of `parse_departure_time` / `calculate_refund` with a fixed aware `now` (both sides of the 72h and 24h cutoffs, Business/Galaxium, after departure, `Z` suffix).
- `fare-rules-refunds-plan.md`: Sub-Task 5 marked done with handoff notes.
- `AGENTS.md` and `.bob/rules-agent/AGENTS.md`: removed stale-fixture notes; `AGENTS.md` now mentions `REFUND_RULES`, the preview route/tool and the new fixtures.

**Validation:** `pytest` from `booking_system_backend/`: 102 passed (4 pre-existing deprecation warnings). Single node id run passed. No production code changed; no bug found. MCP tool itself is not covered by a test.
