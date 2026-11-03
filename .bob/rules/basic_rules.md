# Project Overview
Galaxium Travels — an interplanetary flight booking system. The backend also exposes an **MCP server** (mounted at `/mcp`) alongside the REST API, both served from the same FastAPI process on port 8080.

## Stack
- **Backend**: Python/FastAPI + SQLAlchemy (SQLite) + FastMCP. Entry point: `booking_system_backend/server.py`, run via `python server.py`.
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS. Run via `npm run dev` (from `booking_system_frontend/`).

## Commands

### Backend (run from `booking_system_backend/`, with `.venv` active)
```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Run server
python server.py   # http://localhost:8080, Swagger at /docs, MCP at /mcp

# Run all tests
pytest

# Run a single test function
pytest tests/test_services.py::TestBookingService::test_book_flight_success -v

# Run a single test file
pytest tests/test_rest.py -v
```

### Frontend (run from `booking_system_frontend/`)
```bash
npm run dev      # http://localhost:5173
npm run build    # tsc -b && vite build
npm run lint     # eslint .
```

### Start both together (from repo root)
```bash
./start.sh
```

## Critical Backend Patterns

### Error handling: return ErrorResponse, don't raise
Service functions return `BookingOut | ErrorResponse` (or similar). **Never raise exceptions** from service layer — return an `ErrorResponse` instance instead. REST endpoints return these directly; MCP tools convert them to `raise Exception(result.details or result.error)`.

### Seat classes: exactly three, specific names
Valid seat classes are `"economy"`, `"business"`, `"galaxium"`. The Flight model has three separate seat columns (`economy_seats`, `business_seats`, `galaxium_seats`). There is no generic `seats_available` column — the `SEAT_CLASS_MAP` in `services/booking.py` maps class names to column names.

### Timestamps are ISO strings, stored as String columns
Both `departure_time`/`arrival_time` on Flight and `booking_time` on Booking are `String` columns (not DateTime). `booking_time` is written as `datetime.utcnow().isoformat()`.

### Pydantic schemas use `model_validate()`, not `from_orm()`
All schemas that wrap ORM models use `class Config: from_attributes = True`. Construct them with `BookingOut.model_validate(obj)`, not `.from_orm()`.

### Tests use in-memory SQLite + monkeypatching
`conftest.py` patches both `db.SessionLocal` and `server.SessionLocal` (the MCP tools use `SessionLocal` directly, bypassing FastAPI dependency injection). Each test gets a fresh DB; `seed()` is patched to a no-op.

## Critical Frontend Patterns

### API base URL from env
Configure `VITE_API_URL` in `.env` (see `.env.example`). Defaults to `http://localhost:8080`.

### Error detection: check `response.success === false`
Use the `isErrorResponse(response)` helper from `src/services/api.ts` to distinguish `ErrorResponse` from success types. It checks `response.success === false`.

### Seat class utilities: use `src/utils/seatClasses.ts`
Use `getSeatClassPrice(basePrice, seatClass)` for price with multipliers (economy ×1, business ×1.5, galaxium ×2.5) and `getSeatCount(flight, seatClass)` to read per-class seat counts. **Price is stored as an integer (cents/whole units)**; `formatCurrency` in `src/utils/formatters.ts` formats it as USD.

### TypeScript strictness
`tsconfig.app.json` enables `strict`, `noUnusedLocals`, `noUnusedParameters`, and `verbatimModuleSyntax`. All types live in `src/types/index.ts`.

### Tailwind custom tokens
Use project-specific color tokens: `space-dark`, `space-blue`, `cosmic-purple`, `nebula-pink`, `alien-green`, `solar-orange`, `star-white`. Backgrounds: `bg-space-gradient`, `bg-cosmic-gradient`.

## Coding Standards

- Always include a concise JSDoc comment on every public function (frontend TypeScript) and a one-line docstring on every public function (backend Python). One sentence is enough.
- Be very concise in all code comments, docstrings, and prose. Prefer short, direct sentences.

## Interaction Logging

After every interaction, write a summary Markdown file to the `internal-monologue/` folder in the repo root.
- Filename format: `YYYY-MM-DD_concise-description.md` (e.g. `2026-01-15_update-readme.md`).
- Content: a brief summary of what was requested and what was done.
- Create the `internal-monologue/` folder if it does not exist.
