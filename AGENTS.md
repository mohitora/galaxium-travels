# AGENTS.md

This file provides guidance to agents when working with code in this repository.

Two independent sub-projects (no shared code, no monorepo tooling) — run commands from their own directories:
- `booking_system_backend/` — Python 3.11 FastAPI + FastMCP + SQLAlchemy/SQLite
- `booking_system_frontend/` — React 19 + Vite + TypeScript (strict) + Tailwind

## Commands

```bash
# Backend (from booking_system_backend/) — use uv, never plain pip (macOS 26 breaks pip/ensurepip)
uv venv --python 3.11 .venv && uv pip install -r requirements.txt && source .venv/bin/activate
python server.py                       # :8080, Swagger /docs, MCP /mcp
pytest                                 # must run from booking_system_backend/ (pytest.ini: testpaths=tests)
pytest tests/test_rest.py::TestBookEndpoint::test_book_flight_success    # single test
pytest tests/test_services.py::TestBookingService::test_book_flight_success

# Frontend (from booking_system_frontend/)
npm run dev      # :5173
npm run build    # tsc -b && vite build — this is the type-check; there is no separate tsc script
npm run lint     # eslint (typescript-eslint recommended + react-hooks + react-refresh)

./start.sh       # repo root: starts both (requires uv + node)
```

No Python linter/formatter is configured. Frontend has no test runner.

## Backend

- **Seat classes: exactly four** — `economy`, `flexi`, `business`, `galaxium`. `Flight` has `{class}_seats` columns; no `seats_available`. Access via `getattr/setattr(flight, f"{seat_class}_seats")` (`services/booking.py:_seat_attr`), never hard-code.
- **`SEAT_CLASS_MULTIPLIERS` in `schemas.py` is the single source of truth** (1.0 / 1.5 / 3.0 / 6.0). `FlightOut` computes `{class}_price` from `Flight.price` in a `model_validator`; the DB never stores them.
- **Refund rules live in `schemas.py:REFUND_RULES`** (percent + cutoff hours per class) with `calculate_refund` / `parse_departure_time`; `refund_percent` in the preview is always the class rule, even when `refund_amount` is 0. Preview = `services/booking.py:get_refund_preview`, exposed as `GET /refund-preview/{booking_id}` and MCP tool `get_refund_preview`. `cancel_booking` stores `refund_amount`; both reject non-`booked` statuses (`ALREADY_CANCELLED`, `BOOKING_NOT_CANCELLABLE`).
- **Service layer returns `X | ErrorResponse`, never raises.** REST routes return it directly; `@mcp.tool()` wrappers in `server.py` do `raise Exception(result.details or result.error)`.
- **All REST errors are HTTP 200** with body `{success: false, error, error_code, details}`. Only request-validation failures are 422 (e.g. missing `seat_class`).
- **New operation = service function + FastAPI route + `@mcp.tool()`** in `server.py`; both transports call the same service. MCP tools use `SessionLocal()` directly (not `get_db`). The `FastMCP` instance is created before `FastAPI` so lifespans can be combined; mounted via `app.mount("/mcp", mcp_app)`.
- **DB is cleared and re-seeded on every server start** (`seed.py`, in lifespan). `init_db()` only creates missing tables — after editing `models.py`, delete `booking.db` (no migrations), and update `schemas.py`, `seed.py`, and test fixtures too.
- Timestamps (`departure_time`, `arrival_time`, `booking_time`) are `String` columns holding ISO strings. `price` is an integer.
- Schemas wrap ORM objects with `class Config: from_attributes = True`; use `Schema.model_validate(obj)`.
- Style: one-line docstring on every public function; imports are flat top-level (`from models import ...`, not package-relative) — `conftest.py` inserts the backend dir into `sys.path`.

### Tests
- In-memory SQLite (`StaticPool`), fresh schema per test. The `client` fixture monkey-patches **`db.SessionLocal` and `server.SessionLocal`** and `server.seed` (no-op), and overrides `get_db`. A new module importing `SessionLocal` directly must be patched in `conftest.py` too.
- Use `make_flight(hours_until_departure=..., price=...)` and `make_booking(flight, seat_class, status)` from `conftest.py` when departure timing matters (seed flights are in 2099).
- Tests assert `status_code == 200` and inspect the body for errors.

## Frontend

- Types/constants for seat classes live in `src/types/index.ts` (`SeatClass`, `SEAT_CLASSES`, `SEAT_CLASS_LABELS`, `SEAT_CLASS_COLORS`) — import, don't redeclare. Per-class access: `flight[\`${cls}_seats\` as keyof Flight]` / `_price` (see `FlightCard.tsx`). The frontend never computes prices; it reads the backend's `{class}_price`.
- `src/services/api.ts`: always check `isErrorResponse(res)` (`res.success === false`) before using data. `BookingRequest` must include `seat_class`. Base URL from `VITE_API_URL` (default `http://localhost:8080`).
- Auth is name + email only, stored in `localStorage` key `galaxium_user` via `useUser`; it throws outside `<UserProvider>` (wraps app in `App.tsx`).
- User-facing errors: `toast` from `react-hot-toast`. Enter animations: Framer Motion `initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}`.
- Common components are imported from the barrel `src/components/common/index.ts`; add new ones there.
- No inline hex/`background`/`color` in JSX. Use Tailwind tokens `space-dark`, `space-blue`, `cosmic-purple`, `nebula-pink`, `alien-green`, `solar-orange`, `star-white`, `bg-space-gradient`, `bg-cosmic-gradient`, plus `.glass-card`, `.btn-primary`, `.btn-secondary`, `.input-field` from `src/index.css`.
- `tsconfig.app.json` enforces `strict`, `noUnusedLocals`, `noUnusedParameters`, `verbatimModuleSyntax` (use `import type`). Add a concise JSDoc to every public function.

## Repo conventions & gotchas

- After every interaction, write a short summary to `internal-monologue/YYYY-MM-DD_concise-description.md`.
- `.bob/rules/basic_rules.md` is **stale** on seat classes: it says three classes (no `flexi`), multipliers ×1/1.5/2.5, and references a non-existent `src/utils/seatClasses.ts`. Trust the code and this file; `src/utils/` only has `formatters.ts` (`formatCurrency`).
- Mode-specific supplements: `.bob/rules-agent|ask|plan/AGENTS.md`.
