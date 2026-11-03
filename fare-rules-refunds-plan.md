# Fare Rules and Refunds on Cancellation — Implementation Plan

## Overview

Give each seat class a different cancellation rule so the price tiers mean something. When a booking is cancelled, the backend computes a refund from the booking's seat class and the time left before departure, stores it on the booking, and returns it. Users see the refund before confirming. AI agents get the same information through MCP.

### Refund rules

| Class | Refund | Condition |
|---|---|---|
| Economy | 80% | cancelled more than 72h before departure, otherwise 0% |
| Flexi | 100% | cancelled more than 24h before departure, otherwise 0% |
| Business | 75% | any time before departure |
| Galaxium | 100% | any time before departure |

### Confirmed decisions

- Cancelling at or inside a cutoff refunds 0%. Cancelling after departure refunds 0%.
- The refund is a percentage of the class price paid (`price` × `SEAT_CLASS_MULTIPLIERS`), rounded like `FlightOut` prices.
- Rules live in one backend table next to `SEAT_CLASS_MULTIPLIERS` in `schemas.py`. Cutoff hours and percentage per class.
- Refund preview is a new operation exposed over REST **and** MCP, both calling one service function.
- Policy text for each class is a **static label map in the frontend types file**. This is simpler but its wording can drift from the backend rules. Accepted by the user.
- Service functions return `X | ErrorResponse` and never raise. REST errors stay HTTP 200 with `success: false`.

### Scope

- **Backend:** rule table, refund calculation, `refund_amount` on `Booking`, preview service + REST route + MCP tool, cancel stores and returns refund, seed update.
- **Frontend:** types, API client, refund preview in the cancel modal, refund on `BookingCard`, policy line per class on `FlightCard`.
- **Tests:** repair stale tests and fixtures, add refund tests on both sides of every cutoff.
- **Out of scope:** real payments, change flight date, partial cancellations, emails.

### Key findings from research

- `cancel_booking` in `services/booking.py` only restores a seat and sets status. There is no refund logic.
- No backend code parses `departure_time` today. Values are strings like `2099-01-01T09:00:00Z`. The `Z` suffix needs handling when parsing.
- There is no refund preview route or MCP tool.
- `MyBookings.tsx` already has a cancel confirmation modal with generic text. `BookingCard.tsx` already shows the class price.
- `FlightCard.tsx` renders one row per class in a `SEAT_CLASSES.map()` loop, which is where a policy line fits.
- Seeded bookings include `cancelled` ones with random classes, so existing cancelled rows need a sensible `refund_amount`.
- `tests/test_services.py` and `tests/test_rest.py` build `Flight(...)` with the removed `seats_available` and `Booking(...)` without `seat_class`. These tests are broken, not just stale. `conftest.py` fixtures are stale too.

### Architecture

```
Frontend (MyBookings cancel modal)
  -> GET refund preview (REST)        ->  services.booking.get_refund_preview
  -> POST cancel (REST)               ->  services.booking.cancel_booking
AI agent (MCP)
  -> get_refund_preview tool          ->  services.booking.get_refund_preview
  -> cancel_booking tool              ->  services.booking.cancel_booking

Both services use one shared refund calculation + the rule table in schemas.py
```

### Dependency order

```
1 (Rules + calculation)
 └─ 2 (Model, schemas, seed)
     └─ 3 (Services: preview + cancel)
         └─ 4 (REST + MCP)
             └─ 5 (Backend tests)
                 └─ 6 (Frontend types + API)
                     └─ 7 (Cancel modal preview)
                         └─ 8 (BookingCard + FlightCard policy)
                             └─ 9 (Docs + final validation)
```

---

## Sub-Task 1 — Backend: Refund rules and calculation

**Intent**: Define the per-class refund rules once and a single function that turns (class price, departure time, now) into a refund amount, so preview and cancel can never disagree.

**Expected Outcomes**
- A rule table in `schemas.py` next to `SEAT_CLASS_MULTIPLIERS` covers all four classes with a refund percentage and an optional cutoff in hours.
- One calculation function returns the refund amount for a given class, price and departure time, using the rules in the Overview.
- Departure times with a `Z` suffix parse correctly as UTC.
- Cancelling exactly at a cutoff, or after departure, returns 0.

**Todo List**
1. Add the rule table (percentage and cutoff hours per class; no cutoff for Business and Galaxium) beside `SEAT_CLASS_MULTIPLIERS`.
2. Add a helper that parses `departure_time` into an aware UTC datetime, handling `Z`.
3. Add the refund calculation, taking the class price from `base price × SEAT_CLASS_MULTIPLIERS`, rounded the same way as `FlightOut`.
4. Keep the function free of database access so it can be tested directly. Accept `now` as a parameter.

**Relevant Context**
- [`booking_system_backend/schemas.py`](booking_system_backend/schemas.py) — `SEAT_CLASS_MULTIPLIERS`, `FlightOut.compute_class_prices`
- [`booking_system_backend/services/booking.py`](booking_system_backend/services/booking.py) — `_seat_attr`, existing service style
- No existing datetime parsing in the backend; stored times are `String` columns

**Handoff notes (for Sub-Task 2 onwards)**
- All three additions are in [`booking_system_backend/schemas.py`](booking_system_backend/schemas.py), between `SEAT_CLASS_MULTIPLIERS` and `FlightOut`:
  - `REFUND_RULES: dict[str, dict[str, Optional[int]]]` — per class `{"refund_percent": int, "cutoff_hours": int | None}`.
  - `parse_departure_time(value: str) -> datetime` — returns an aware UTC datetime; handles `Z`.
  - `calculate_refund(seat_class: str, base_price: int, departure_time: str, now: datetime) -> int` — takes the **flight's base `price`** (not the class price) and the departure **string**. `now` must be an aware datetime (e.g. `datetime.now(timezone.utc)`); a naive `now` raises `TypeError`.
- Returns 0 at exactly the cutoff, inside it, at departure, and after departure. Unknown `seat_class` raises `KeyError` (callers validate the class first).
- To get the refund percentage for the preview schema (Sub-Task 2/3), read `REFUND_RULES[seat_class]["refund_percent"]` and the class price as `round(price * SEAT_CLASS_MULTIPLIERS[seat_class])`. If the percentage should be 0 when no refund applies, derive it from the returned amount or the preview service must decide; this is not done in Sub-Task 1.
- Sanity-checked by hand only (both sides of 72h and 24h, business/galaxium before and after departure, rounding). No pytest tests yet, those are Sub-Task 5.

**Status**: [x] done

---

## Sub-Task 2 — Backend: Model, schemas, seed

**Intent**: Persist the refund on the booking and make the API contracts carry it.

**Expected Outcomes**
- `Booking` has a nullable `refund_amount` integer. It is empty for bookings that are not cancelled.
- `BookingOut` exposes `refund_amount`.
- A response schema exists for the refund preview (booking id, seat class, class price, refund amount, refund percentage, and the departure time used).
- Seeded cancelled bookings have a `refund_amount` calculated by the shared function. Seeded non-cancelled bookings have none.
- `booking.db` is deleted so it is recreated from the new schema.

**Todo List**
1. Add `refund_amount` to `Booking` in `models.py` (nullable integer).
2. Add `refund_amount: Optional[int]` to `BookingOut`.
3. Add the preview response schema in `schemas.py`.
4. Update `seed.py` so cancelled bookings get a refund from the shared function. Seed flights depart in 2099, so these will show the long-notice refund.
5. Delete `booking_system_backend/booking.db`.

**Relevant Context**
- [`booking_system_backend/models.py`](booking_system_backend/models.py)
- [`booking_system_backend/schemas.py`](booking_system_backend/schemas.py) — `BookingOut`, `ErrorResponse`
- [`booking_system_backend/seed.py`](booking_system_backend/seed.py) — booking loop at lines 50–59; `SEAT_CLASSES` is a duplicate list of class names
- No migration tooling: `init_db()` only creates missing tables

**Handoff notes (for Sub-Task 3 onwards)**
- [`models.py`](booking_system_backend/models.py): `Booking.refund_amount = Column(Integer, nullable=True)`. `None` for non-cancelled bookings.
- [`schemas.py`](booking_system_backend/schemas.py): `BookingOut.refund_amount: Optional[int] = None` (so cancel responses carry it automatically via `model_validate`).
- New `RefundPreviewOut` in `schemas.py` (after `BookingOut`, no `from_attributes`, built explicitly by the service). Fields: `booking_id: int`, `seat_class: str`, `class_price: int`, `refund_amount: int`, `refund_percent: int`, `departure_time: str`.
- **DECIDED (user): `refund_percent` is always the class rule percentage** (`REFUND_RULES[seat_class]["refund_percent"]`, e.g. 80 for Economy), even when `refund_amount` is 0. `refund_amount` carries whether a refund applies now. `class_price = round(flight.price * SEAT_CLASS_MULTIPLIERS[seat_class])`; `departure_time` is the flight's stored string.
- `seed.py` now imports `calculate_refund` from `schemas` and passes `datetime.now(timezone.utc)`, the flight `price` and `departure_time`. Cancelled seeded bookings get the long-notice refund; others are `None`. The duplicate `SEAT_CLASSES` list in `seed.py` was left as is.
- Validated: `python seed.py` against a fresh DB gave 11/11 cancelled bookings with a refund and 0 refunds on booked/completed. `booking.db` was deleted afterwards. Existing tests were not run (they are broken until Sub-Task 5).

**Status**: [x] done

---

## Sub-Task 3 — Backend: Services for preview and cancel

**Intent**: Add the preview operation and make cancellation store the refund, both through the shared calculation.

**Expected Outcomes**
- A preview service function returns the refund for a `booked` booking without changing anything.
- Preview returns an `ErrorResponse` for an unknown booking (`BOOKING_NOT_FOUND`) and for a booking that is not in `booked` status.
- `cancel_booking` stores `refund_amount` on the booking, still restores exactly one seat to the right class, and still returns `ErrorResponse` for not found and already cancelled.
- Neither function raises.

**Todo List**
1. Add the preview function in `services/booking.py`, loading the booking and its flight.
2. Handle a missing flight for a booking the same way `cancel_booking` already tolerates it, and decide the error behaviour in preview (return an `ErrorResponse`).
3. Update `cancel_booking` to compute and store the refund before commit.
4. Keep existing error codes unchanged.

**Relevant Context**
- [`booking_system_backend/services/booking.py`](booking_system_backend/services/booking.py) — `cancel_booking` at lines 74–100
- Error style: `ErrorResponse(error=..., error_code=..., details=...)`

**Handoff notes (for Sub-Task 4 onwards)**
- Added `get_refund_preview(db: Session, booking_id: int) -> RefundPreviewOut | ErrorResponse` in [`booking_system_backend/services/booking.py`](booking_system_backend/services/booking.py).
  - Preview returns `RefundPreviewOut` (with `booking_id`, `seat_class`, `class_price`, `refund_amount`, `refund_percent`, `departure_time`).
  - Preview error codes: `BOOKING_NOT_FOUND` (unknown booking), `ALREADY_CANCELLED` (status == 'cancelled'), `BOOKING_NOT_CANCELLABLE` (status != 'booked', e.g. 'completed'), `FLIGHT_NOT_FOUND` (missing flight).
- Updated `cancel_booking(db: Session, booking_id: int) -> BookingOut | ErrorResponse` in [`booking_system_backend/services/booking.py`](booking_system_backend/services/booking.py):
  - Uses shared `_compute_refund(flight, booking.seat_class)` to calculate and persist `refund_amount` on `Booking` prior to commit.
  - Returns `BookingOut` carrying `refund_amount`.
  - Tolerates missing flight by setting `refund_amount = 0` and not crashing.
  - Non-`booked` statuses: **DECIDED (user)** — `cancel_booking` now also returns `BOOKING_NOT_CANCELLABLE` for any status other than `booked` (e.g. `completed`), matching the preview. `ALREADY_CANCELLED` is still returned first for `cancelled`. Seats are not changed on rejection.
  - `cancel_booking` error codes: `BOOKING_NOT_FOUND`, `ALREADY_CANCELLED`, `BOOKING_NOT_CANCELLABLE`. REST and MCP in Sub-Task 4 need no signature change; update docstrings to mention these.
- Validation: Verified with throwaway in-memory SQLite test covering all 4 seat classes on both sides of cutoffs (+100h, +48h, +10h, -5h), DB non-mutation on preview, seat restoration & `refund_amount` storage on cancel, and all preview/cancel error codes.

**Status**: [x] done

---

## Sub-Task 4 — Backend: REST route and MCP tool

**Intent**: Expose the preview over both transports, keeping them in step as the project requires.

**Expected Outcomes**
- A REST GET route for the preview, returning the preview schema or `ErrorResponse`, under the `Bookings` tag.
- An MCP tool for the preview that raises `Exception(result.details or result.error)` on error, like the other tools.
- The existing cancel route and MCP tool return the stored refund through `BookingOut` with no signature changes.
- Tool docstrings describe the refund so agents can use them.

**Todo List**
1. Add the REST route in `server.py` after `/cancel/{booking_id}`.
2. Add the MCP tool in `server.py`, using `SessionLocal()` directly and closing it in `finally`.
3. Update the `cancel_booking` MCP tool and REST docstrings to mention the refund.
4. Confirm `/docs` shows the new route.

**Relevant Context**
- [`booking_system_backend/server.py`](booking_system_backend/server.py) — MCP tools at lines 19–97, REST routes at lines 133–178
- Do not import `SessionLocal` in any new module, so test isolation stays intact

**Handoff notes (for Sub-Task 5 and 6 onwards)**
- All changes are in [`booking_system_backend/server.py`](booking_system_backend/server.py) only. No new module; `RefundPreviewOut` added to the `schemas` import.
- **REST**: `GET /refund-preview/{booking_id}` (tag `Bookings`, `response_model=Union[RefundPreviewOut, ErrorResponse]`, function `refund_preview_endpoint`, placed right after `/cancel/{booking_id}`). `booking_id` is an int path param (non-int -> HTTP 422).
  - Success body: `{"booking_id": int, "seat_class": str, "class_price": int, "refund_amount": int, "refund_percent": int, "departure_time": str}`. Example: Economy, base price 1000, >72h notice -> `class_price 1000, refund_amount 800, refund_percent 80`.
  - Errors are HTTP 200 with `{"success": false, "error", "error_code", "details"}`. Codes: `BOOKING_NOT_FOUND`, `ALREADY_CANCELLED`, `BOOKING_NOT_CANCELLABLE`, `FLIGHT_NOT_FOUND`.
- **MCP**: tool `get_refund_preview(booking_id: int) -> RefundPreviewOut`; uses `SessionLocal()` with `db.close()` in `finally`; raises `Exception(result.details or result.error)` on `ErrorResponse` (fastmcp surfaces it as a `ToolError` whose message contains the details text, not the error code).
- **Cancel** (`POST /cancel/{booking_id}` and MCP `cancel_booking`): signatures unchanged; docstrings now mention the refund and codes `BOOKING_NOT_FOUND`, `ALREADY_CANCELLED`, `BOOKING_NOT_CANCELLABLE`. Success body is `BookingOut` with `refund_amount` (e.g. `800`).
- For Sub-Task 5: the MCP tool can be tested in-process with `from fastmcp import Client; async with Client(server.mcp) as cl: await cl.call_tool("get_refund_preview", {"booking_id": 1})` (fastmcp 4.1.4); `res.structured_content` holds the dict. The REST `client` fixture patches `server.SessionLocal`, so MCP calls use the same test session.
- For Sub-Task 6: the frontend base route is `${API_URL}/refund-preview/${bookingId}` with GET; response union is preview type or `ErrorResponse` (`isErrorResponse`). Note `refund_percent` is the class rule even when `refund_amount` is 0.
- Validation (throwaway script, deleted afterwards): preview body for a booked Economy booking; unknown id -> HTTP 200 `BOOKING_NOT_FOUND`; completed -> `BOOKING_NOT_CANCELLABLE`; preview after cancel -> `ALREADY_CANCELLED`; cancel response has `refund_amount`; `/openapi.json` lists the route under `Bookings`; MCP tool registered and returns correct body; MCP error raises. The broken pytest suite was not run.

**Status**: [x] done

---

## Sub-Task 5 — Backend: Repair and extend tests

**Intent**: Existing tests build objects with removed fields, so they cannot run today. Repair them, then prove the rules on both sides of each cutoff.

**Expected Outcomes**
- `conftest.py` fixtures use the four per-class seat columns and include `seat_class`.
- Existing service and REST tests build `Flight` with per-class seats and `Booking` with `seat_class`, and pass.
- New tests cover, for each class, a case on each side of its cutoff. Economy around 72h, Flexi around 24h, Business and Galaxium at any notice.
- Tests cover after-departure cancellation returning 0, preview not changing any data, preview errors, and exactly one seat restored to the correct class.
- Test flights use departure times relative to now, since seed flights are in 2099.

**Todo List**
1. Fix `sample_flight_data` and `sample_booking_data` in `conftest.py`.
2. Fix `Flight(...)` and `Booking(...)` construction in `tests/test_services.py` and `tests/test_rest.py`.
3. Add direct tests of the calculation function using a fixed `now`.
4. Add service tests for preview and for cancel storing `refund_amount`.
5. Add REST tests for the preview route and for the refund in the cancel response. Assert HTTP 200 and inspect the body for errors.
6. Run `pytest` from `booking_system_backend/`.

**Relevant Context**
- [`booking_system_backend/tests/conftest.py`](booking_system_backend/tests/conftest.py)
- [`booking_system_backend/tests/test_services.py`](booking_system_backend/tests/test_services.py) — cancel tests at lines 167–234
- [`booking_system_backend/tests/test_rest.py`](booking_system_backend/tests/test_rest.py) — `TestCancelEndpoint` at lines 181–222
- `pytest.ini`: tests run from `booking_system_backend/`

**Handoff notes (for Sub-Task 6 onwards)**
- Backend only; no production code changed, no bug found. `pytest` from `booking_system_backend/`: **102 passed**. Single node id verified (`tests/test_rest.py::TestCancelEndpoint::test_cancel_booking_success`). The 4 warnings are existing SQLAlchemy/Pydantic deprecations in `models.py`/`schemas.py`.
- [`tests/conftest.py`](booking_system_backend/tests/conftest.py): `sample_flight_data` now uses the four `{class}_seats` columns; `sample_booking_data` includes `seat_class`. Added `iso_utc(dt)` helper and two factory fixtures: `make_flight(hours_until_departure=24*365, price=1000, **seats)` (departure relative to now, 5 seats per class by default) and `make_booking(flight, seat_class="economy", status="booked")` (creates a user + booking). Both use `db_session`, so they work with the `client` fixture; no new module imports `SessionLocal`.
- [`tests/test_services.py`](booking_system_backend/tests/test_services.py) and [`tests/test_rest.py`](booking_system_backend/tests/test_rest.py): all `Flight`/`Booking` constructions and `/book` bodies repaired. Added `test_book_flight_invalid_seat_class` (service), `test_book_flight_missing_seat_class` (REST 422). New classes: `TestRefundPreviewService`, `TestCancelRefundService` (services); `TestRefundPreviewEndpoint` plus refund cases in `TestCancelEndpoint` (REST).
- New [`tests/test_refund_rules.py`](booking_system_backend/tests/test_refund_rules.py): `TestParseDepartureTime`, `TestCalculateRefund` with a fixed aware `NOW`. Covers 1s over / exactly / 1s inside the 72h (Economy) and 24h (Flexi) cutoffs, Business/Galaxium at any notice, at/after departure for all classes, `Z` suffix as UTC, rounding, naive `now` -> `TypeError`, unknown class -> `KeyError`.
- Not covered: the MCP `get_refund_preview` tool (the plan's in-process `fastmcp.Client` approach was not added; the tool shares the tested service function).
- For the frontend: real values for a base price of 1000 with long notice are Economy 1000 -> refund 800 (80%), Flexi 1500 -> 1500 (100%), Business 3000 -> 2250 (75%), Galaxium 6000 -> 6000 (100%). Inside the cutoff, `refund_amount` is 0 but `refund_percent` stays the rule value (80 for Economy), so the UI must key off `refund_amount`, not `refund_percent`, to decide whether a refund applies.

**Status**: [x] done

---

## Sub-Task 6 — Frontend: Types and API client

**Intent**: Keep TypeScript contracts in sync with the backend and add the preview call.

**Expected Outcomes**
- `Booking` has `refund_amount` (number or null).
- A preview response type exists matching the backend schema.
- `src/services/api.ts` has a function that calls the preview route.
- A static map of one-line refund policy text per seat class lives in `src/types/index.ts`, next to `SEAT_CLASS_LABELS`. Its wording matches the rule table in the Overview.

**Todo List**
1. Add `refund_amount` to the `Booking` interface.
2. Add the preview response interface.
3. Add the preview API function with a JSDoc line, following `cancelBooking`.
4. Add the policy text map to `src/types/index.ts` (for example, Economy: 80% refund up to 72h before departure).

**Relevant Context**
- [`booking_system_frontend/src/types/index.ts`](booking_system_frontend/src/types/index.ts) — `Booking`, `SEAT_CLASS_LABELS`
- [`booking_system_frontend/src/services/api.ts`](booking_system_frontend/src/services/api.ts) — `cancelBooking`, `isErrorResponse`
- Risk: the static policy text can drift from the backend rule table. Note this in a code comment on the map.

**Handoff notes (for Sub-Task 7 and 8 onwards)**
- Frontend only; no components, pages or backend touched. Two files changed: [`src/types/index.ts`](booking_system_frontend/src/types/index.ts) and [`src/services/api.ts`](booking_system_frontend/src/services/api.ts).
- New exports in `src/types/index.ts`:
  - `SEAT_CLASS_REFUND_POLICY: Record<SeatClass, string>` (placed after `SEAT_CLASS_LABELS`). Values: `'80% refund more than 72h before departure'`, `'100% refund more than 24h before departure'`, `'75% refund any time before departure'`, `'100% refund any time before departure'`. Comment notes it is static and must match `REFUND_RULES` in `schemas.py`.
  - `RefundPreview` interface: `booking_id`, `seat_class: SeatClass`, `class_price`, `refund_amount`, `refund_percent`, `departure_time`.
  - `Booking.refund_amount: number | null` (required field). `BookingWithFlight` inherits it.
- New export in `src/services/api.ts`: `getRefundPreview(bookingId: number): Promise<RefundPreview | ErrorResponse>` calling `GET /refund-preview/${bookingId}`. Use `isErrorResponse(res)` before reading it. Backend errors arrive as HTTP 200 `success: false` with codes `BOOKING_NOT_FOUND`, `ALREADY_CANCELLED`, `BOOKING_NOT_CANCELLABLE`, `FLIGHT_NOT_FOUND`.
- **Sub-Task 7**: decide "refund applies" from `refund_amount > 0`, not `refund_percent` (always the class rule, e.g. 80 for Economy even when `refund_amount` is 0). `cancelBooking` already returns `Booking` with `refund_amount`.
- **Sub-Task 8**: `BookingCard` can read `booking.refund_amount` directly (null when not cancelled). `FlightCard` can use `SEAT_CLASS_REFUND_POLICY[cls]` inside its `SEAT_CLASSES.map()` loop.
- Making `refund_amount` required did not break any code: no frontend code constructs `Booking` objects literally, so no fixes were needed.
- Validation from `booking_system_frontend/`: `npm run build` passes. `npm run lint` is unchanged from the pre-change baseline: 13 problems (11 errors, 2 warnings), all pre-existing and not fixed (`no-explicit-any` in `BookingModal.tsx`, `UserIdentification.tsx`, `Flights.tsx`, `MyBookings.tsx` and `api.ts` `isErrorResponse`; `react-refresh/only-export-components` in `useUser.tsx`; `exhaustive-deps` warnings in `Flights.tsx` and `MyBookings.tsx`; unused `error` in `formatters.ts` at lines 69 and 98). The `api.ts` one moved from line 110 to 123 because of the inserted function.

**Status**: [x] done

---

## Sub-Task 7 — Frontend: Refund preview in the cancel modal

**Intent**: Show "You'll get $X back" before the user confirms, using the backend as the source of the number.

**Expected Outcomes**
- Opening the cancel modal fetches the preview for that booking.
- The modal shows the refund amount, or a clear zero-refund message, while keeping the existing confirm and keep buttons.
- Loading and error states are handled with `isErrorResponse` and `toast`.
- After confirming, the booking list reflects the cancelled booking and its refund.

**Todo List**
1. In `MyBookings.tsx`, call the preview function when the cancel modal opens for a booking.
2. Render the refund amount with `formatCurrency` inside the modal.
3. Handle preview failure without blocking cancellation, and use a toast for errors.
4. After a successful cancel, refresh state so the refund appears.

**Relevant Context**
- [`booking_system_frontend/src/pages/MyBookings.tsx`](booking_system_frontend/src/pages/MyBookings.tsx) — `handleCancelClick`, `handleConfirmCancel`, cancel modal near lines 175–203
- [`booking_system_frontend/src/utils/formatters.ts`](booking_system_frontend/src/utils/formatters.ts) — `formatCurrency`
- Use `Modal` from the common barrel export and existing Tailwind tokens

**Status**: [ ] pending

---

## Sub-Task 8 — Frontend: BookingCard and FlightCard

**Intent**: Make the rules visible before booking and the outcome visible after cancelling.

**Expected Outcomes**
- `BookingCard` shows the refunded amount on cancelled bookings that have one.
- Each class row on `FlightCard` shows its one-line policy from the static map.
- No inline hex colours, and the strict TypeScript flags still pass.

**Todo List**
1. In `BookingCard.tsx`, show the refund for `status === 'cancelled'` when `refund_amount` is present.
2. In `FlightCard.tsx`, add the policy line inside the per-class row loop, using `SEAT_CLASS_*`-style lookup.
3. Add a JSDoc line to any new public function.

**Relevant Context**
- [`booking_system_frontend/src/components/bookings/BookingCard.tsx`](booking_system_frontend/src/components/bookings/BookingCard.tsx) — `canCancel` at line 42, price at line 103
- [`booking_system_frontend/src/components/flights/FlightCard.tsx`](booking_system_frontend/src/components/flights/FlightCard.tsx) — `SEAT_CLASSES.map()` at lines 102–142

**Status**: [ ] pending

---

## Sub-Task 9 — Docs and final validation

**Intent**: Leave the project documented and verified end to end.

**Expected Outcomes**
- `pytest` passes from `booking_system_backend/`.
- `npm run build` and `npm run lint` pass from `booking_system_frontend/`.
- With both servers running, a Flexi, an Economy and a Galaxium booking each show the correct refund in the modal and on the card.
- `AGENTS.md` mentions the refund rule table location and the new preview operation. The stale fixtures note is removed once fixed.
- `.bob/rules/basic_rules.md` seat-class section is corrected, because it still describes three classes (separate cleanup, only if the user wants it).
- A summary is written to `internal-monologue/`.

**Todo List**
1. Run `pytest`, `npm run build`, `npm run lint` and fix any failures.
2. Run the app and check the three bookings above through the UI.
3. Update `AGENTS.md` for the new rule table, preview route and MCP tool.
4. Write the `internal-monologue/` summary.

**Relevant Context**
- [`AGENTS.md`](AGENTS.md)
- [`start.sh`](start.sh) to run both servers

**Status**: [ ] pending
