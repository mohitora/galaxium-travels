# Project Architecture Rules (Non-Obvious Only)

- **Dual-protocol by design.** Every booking operation is exposed as both a REST endpoint and an MCP tool. New features must be implemented in the service layer first, then wired to both transports in `server.py`. Services are the canonical implementation.
- **DB is stateless across restarts.** `seed.py` always clears and re-seeds on startup. Any planned feature that requires persistent state (e.g. user-uploaded data, preferences) needs the seed wipe removed first.
- **No migration tooling.** Schema changes require deleting `booking.db`. Plan accordingly — any field added to `models.py` must also be added to `schemas.py`, `seed.py` fixture data, and `tests/conftest.py` fixtures.
- **Seat inventory is distributed across 4 columns** (`economy_seats`, `flexi_seats`, `business_seats`, `galaxium_seats`). There is no aggregate `seats_available`. Any feature that needs total availability must sum the four.
- **Computed fields belong in `FlightOut`, not in the DB or frontend.** The price multiplier pattern (`SEAT_CLASS_MULTIPLIERS` in `schemas.py`) is the established convention for derived data.
- **Frontend state is minimal by design.** Only user identity is global (React Context + localStorage). All flight and booking data is fetched fresh on each page mount — there is no cache or global store.
- **Test isolation pattern:** tests use in-memory SQLite + `monkeypatch` on `SessionLocal` in both `db` and `server` modules. Adding a third module that imports `SessionLocal` directly breaks test isolation unless patched in `conftest.py`.
- **`booking_system_backend/` and `booking_system_frontend/` are fully independent projects** — no shared code, no monorepo tooling. Changes that span both (e.g. adding a new field to the API) must be coordinated across both package boundaries manually.
