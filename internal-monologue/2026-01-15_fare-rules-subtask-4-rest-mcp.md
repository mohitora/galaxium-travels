# Fare rules Sub-Task 4: REST route and MCP tool

**Requested:** Implement only Sub-Task 4 of `fare-rules-refunds-plan.md`: expose the refund preview over REST and MCP, and update cancel docstrings.

**Done (all in `booking_system_backend/server.py`):**
- Added `GET /refund-preview/{booking_id}` (`Bookings` tag, `Union[RefundPreviewOut, ErrorResponse]`) after the cancel route.
- Added MCP tool `get_refund_preview(booking_id)` using `SessionLocal()` and raising on `ErrorResponse`.
- Imported `RefundPreviewOut`; updated `cancel_booking` MCP and REST docstrings with the refund and the error codes `BOOKING_NOT_FOUND`, `ALREADY_CANCELLED`, `BOOKING_NOT_CANCELLABLE`.
- No services, tests, models, seed or frontend changes.

**Validated:** Throwaway TestClient + in-memory SQLite script (deleted afterwards): preview body, unknown id and completed booking errors (HTTP 200, `success: false`), cancel response `refund_amount`, `/openapi.json` route, MCP tool registered, called and error path. Existing pytest suite not run (broken until Sub-Task 5).

**Plan file:** Sub-Task 4 marked done with handoff notes for Sub-Tasks 5 and 6. Stopped for user review.
