# Project Documentation Context (Non-Obvious Only)

- **API errors are always HTTP 200** — do not confuse with REST conventions. Error shape: `{ success: false, error: string, error_code: string, details?: string }`. This applies to every endpoint including `/book`, `/cancel`, `/register`, `/user`.
- **`/mcp` endpoint** mounts a full FastMCP streaming server alongside the REST API. AI agents use this path; it is not a REST endpoint.
- **Seat class pricing is backend-computed.** The `Flight` model stores only `price` (base). `FlightOut` adds `economy_price`, `flexi_price`, `business_price`, `galaxium_price` as computed fields. The frontend never calculates prices itself.
- **No auth middleware exists.** Identity is purely name + email. The "user" concept is a record in the DB; anyone with the right name+email pair can act as that user.
- **`booking.db` is ephemeral** — wiped and re-seeded every server start. There is no persistent storage in production setup.
- **Tests live in `booking_system_backend/tests/`**, not alongside source files. Must be run from `booking_system_backend/` directory for pytest to resolve imports correctly (`conftest.py` manually inserts the parent directory into `sys.path`).
- **`seat-classes-plan.md`** in the repo root is the implementation plan for the seat class feature — all 11 sub-tasks are marked done.
