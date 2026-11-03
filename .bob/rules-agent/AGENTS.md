# Project Coding Rules (Non-Obvious Only)

## Backend

- Use `uv pip install` / `uv venv --python 3.11` — never plain `pip` on this machine (macOS 26 breaks `pip`/`ensurepip`).
- `SEAT_CLASS_MULTIPLIERS` in `booking_system_backend/schemas.py` is the single source of truth for pricing. Update it there; computed prices in `FlightOut` derive from it automatically via `model_validator`.
- Seat operations use `getattr(flight, f"{seat_class}_seats")` / `setattr(...)` — do not hard-code attribute names. See `services/booking.py:_seat_attr()`.
- Adding a new endpoint: expose it as both a FastAPI route **and** a `@mcp.tool()` in `server.py`. Both call the same service function.
- Delete `booking.db` whenever you change `models.py` — there is no migration tooling; `init_db()` only creates missing tables, it does not alter existing ones.
- Tests monkey-patch **both** `db.SessionLocal` and `server.SessionLocal` (see `conftest.py`). If you add a new module that imports `SessionLocal` directly, patch it too.

## Frontend

- Per-class seat/price access pattern: `flight[\`${seatClass}_seats\`]` and `flight[\`${seatClass}_price\`]` — cast with `as keyof Flight` for TypeScript. See `FlightCard.tsx:seatCount/seatPrice`.
- `useUser()` throws if called outside `<UserProvider>`. The provider wraps the entire app in `App.tsx`.
- All user-facing errors go through `react-hot-toast`. Import `toast` from `react-hot-toast` directly.
- Framer Motion is used for all enter animations. Follow the pattern in existing components: `initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}`.
- New common components must be added to `src/components/common/index.ts` barrel export.
- Do not add inline `background`, `color`, or hex values in JSX — use Tailwind custom tokens from `tailwind.config.js`.
