# Seat Classes — Implementation Plan

## Overview

Add four seat classes to every Galaxium Travels flight: **Economy**, **Flexi-Economy**, **Business**, and **Galaxium (First Class)**. Each class has its own seat inventory and a price derived from the flight's base price via a fixed multiplier. Users choose their class on the Flights page; the chosen class is stored on the booking and correctly restored on cancellation.

### Multipliers

| Class | Multiplier | Column name |
|---|---|---|
| Economy | 1× | `economy_seats` |
| Flexi-Economy | 1.5× | `flexi_seats` |
| Business | 3× | `business_seats` |
| Galaxium | 6× | `galaxium_seats` |

### Scope

- **Backend**: DB model, Pydantic schemas, booking service, seed data, REST endpoints, MCP tools
- **Frontend**: TypeScript types, API client, FlightCard, BookingModal, BookingCard, MyBookings page

The existing `seats_available` column is **removed** from `Flight`; total availability is the sum of the four class columns. The existing `price` column remains as the **base price**.

---

## Sub-Task 1 — Backend: Update Data Model

**Intent**: Replace the single `seats_available` column on `Flight` with four per-class seat columns, and add a `seat_class` column to `Booking`.

**Expected Outcomes**
- `Flight` model has `economy_seats`, `flexi_seats`, `business_seats`, `galaxium_seats` columns; `seats_available` is removed.
- `Booking` model has a `seat_class` column (`economy | flexi | business | galaxium`).
- `booking.db` is deleted so it is recreated fresh from the new schema on next startup.

**Todo List**
1. In `models.py`: remove `seats_available`; add `economy_seats`, `flexi_seats`, `business_seats`, `galaxium_seats` (all `Integer, nullable=False`).
2. In `models.py`: add `seat_class` column to `Booking` (`String, nullable=False`).
3. Delete `booking_system_backend/booking.db` so the DB is rebuilt on next run.

**Relevant Context**
- [`booking_system_backend/models.py`](booking_system_backend/models.py)
- [`booking_system_backend/db.py`](booking_system_backend/db.py) — `init_db()` calls `Base.metadata.create_all` on startup; no migration tooling is needed.

**Status**: [x] done

---

## Sub-Task 2 — Backend: Update Pydantic Schemas

**Intent**: Align all request/response contracts with the new model shape. `FlightOut` must expose the four seat counts and the computed per-class prices. `BookingRequest` and `BookingOut` must carry `seat_class`.

**Expected Outcomes**
- `FlightOut` replaces `seats_available` with `economy_seats`, `flexi_seats`, `business_seats`, `galaxium_seats` and adds computed price fields `economy_price`, `flexi_price`, `business_price`, `galaxium_price`.
- `BookingRequest` adds `seat_class: Literal["economy", "flexi", "business", "galaxium"]`.
- `BookingOut` adds `seat_class: str`.
- A helper constant `SEAT_CLASS_MULTIPLIERS` is defined (e.g. in `schemas.py` or a small new `constants.py`) so multipliers are defined in one place.

**Todo List**
1. Add `SEAT_CLASS_MULTIPLIERS` dict: `{"economy": 1.0, "flexi": 1.5, "business": 3.0, "galaxium": 6.0}`.
2. Update `FlightOut`: remove `seats_available`; add four `*_seats` fields; add four `*_price` computed fields (validator derives them from `price × multiplier`, rounded to nearest int).
3. Update `BookingRequest`: add `seat_class` field with a `Literal` type constraint.
4. Update `BookingOut`: add `seat_class: str`.

**Relevant Context**
- [`booking_system_backend/schemas.py`](booking_system_backend/schemas.py)
- Pydantic v2 `model_validator` or `@computed_field` can compute the price fields from `price` at serialisation time without storing them in the DB.

**Status**: [x] done

---

## Sub-Task 3 — Backend: Update Booking Service

**Intent**: Make `book_flight` and `cancel_booking` seat-class-aware. Booking decrements the correct class column; cancellation increments the same class column.

**Expected Outcomes**
- `book_flight` accepts `seat_class` and validates it is a known class.
- `book_flight` checks the specific class column (`flight.economy_seats`, etc.) instead of `seats_available`.
- `book_flight` stores `seat_class` on the new `Booking` record.
- `cancel_booking` reads `booking.seat_class` and increments the matching column on `Flight`.
- New error code `INVALID_SEAT_CLASS` returned when an unknown class string is passed.

**Todo List**
1. Update `book_flight` signature to include `seat_class: str`.
2. Add validation: if `seat_class` not in `SEAT_CLASS_MULTIPLIERS`, return `ErrorResponse(error_code="INVALID_SEAT_CLASS", ...)`.
3. Replace `flight.seats_available < 1` check with a per-class seat count check using `getattr(flight, f"{seat_class}_seats")`.
4. Decrement `getattr(flight, f"{seat_class}_seats")` instead of `seats_available`.
5. Pass `seat_class=seat_class` into the `Booking` constructor.
6. In `cancel_booking`: read `booking.seat_class`, increment `getattr(flight, f"{booking.seat_class}_seats")`.

**Relevant Context**
- [`booking_system_backend/services/booking.py`](booking_system_backend/services/booking.py)

**Status**: [x] done

---

## Sub-Task 4 — Backend: Update Server Endpoints and MCP Tools

**Intent**: Thread `seat_class` through all REST endpoints and MCP tools that create bookings. Update `list_flights` response to use `FlightOut` (no changes needed to its query — schema change is additive). Update `book_flight` endpoint and MCP tool to accept and forward `seat_class`.

**Expected Outcomes**
- `POST /book` accepts `seat_class` in the request body and passes it to `booking.book_flight`.
- `book_flight` MCP tool signature includes `seat_class: str` parameter.
- All other endpoints are unchanged.
- Swagger UI at `/docs` reflects the updated schemas.

**Todo List**
1. In `server.py` REST handler `book_flight_endpoint`: pass `request.seat_class` to `booking.book_flight(...)`.
2. In `server.py` MCP tool `book_flight`: add `seat_class: str` parameter and forward it.

**Relevant Context**
- [`booking_system_backend/server.py`](booking_system_backend/server.py) lines 30–43 (MCP tool), lines 145–151 (REST handler).

**Status**: [x] done

---

## Sub-Task 5 — Backend: Update Seed Data

**Intent**: Replace the single `seats_available` and one `price` seed values with four per-class seat counts per flight, and assign a valid `seat_class` to each seeded booking.

**Expected Outcomes**
- All 10 seeded flights have values for `economy_seats`, `flexi_seats`, `business_seats`, `galaxium_seats` (no `seats_available`).
- All 20 seeded bookings have a `seat_class` value drawn from the four valid classes.
- Existing price values are kept as base prices.

**Todo List**
1. Update each `Flight(...)` constructor call: remove `seats_available=N`; add `economy_seats`, `flexi_seats`, `business_seats`, `galaxium_seats` (suggested defaults: 10, 8, 4, 2 — or vary per flight for realism).
2. Update the booking seed loop: replace the current `status` random choice with also randomly choosing `seat_class` from `["economy", "flexi", "business", "galaxium"]`.
3. Pass `seat_class=seat_class` into each `Booking(...)` constructor.

**Relevant Context**
- [`booking_system_backend/seed.py`](booking_system_backend/seed.py)

**Status**: [x] done

---

## Sub-Task 6 — Frontend: Update TypeScript Types

**Intent**: Keep the TypeScript interfaces in sync with the updated backend schemas so every downstream component gets correct types and autocompletion.

**Expected Outcomes**
- `Flight` interface removes `seats_available`; adds `economy_seats`, `flexi_seats`, `business_seats`, `galaxium_seats`, `economy_price`, `flexi_price`, `business_price`, `galaxium_price`.
- `Booking` interface adds `seat_class: SeatClass`.
- `BookingRequest` interface adds `seat_class: SeatClass`.
- A `SeatClass` union type is exported: `'economy' | 'flexi' | 'business' | 'galaxium'`.
- A `SEAT_CLASSES` constant array and a `SEAT_CLASS_LABELS` map are exported for use across UI components.

**Todo List**
1. Add `export type SeatClass = 'economy' | 'flexi' | 'business' | 'galaxium'`.
2. Add `export const SEAT_CLASSES: SeatClass[]` and `export const SEAT_CLASS_LABELS` (display names).
3. Update `Flight` interface: remove `seats_available`; add the eight new fields.
4. Update `Booking` interface: add `seat_class: SeatClass`.
5. Update `BookingRequest` interface: add `seat_class: SeatClass`.

**Relevant Context**
- [`booking_system_frontend/src/types/index.ts`](booking_system_frontend/src/types/index.ts)

**Status**: [x] done

---

## Sub-Task 7 — Frontend: Update API Client

**Intent**: Ensure `bookFlight()` sends `seat_class` in the request body. No other API calls need changes.

**Expected Outcomes**
- `bookFlight(data: BookingRequest)` automatically carries `seat_class` because `BookingRequest` now includes it — no other change needed beyond the type update in Sub-Task 6.
- (Verify no hardcoded field lists in `api.ts` would accidentally drop `seat_class`.)

**Todo List**
1. Read `src/services/api.ts` `bookFlight` function and confirm it passes the whole `data` object as the request body (it does — no field list to update).
2. No code change required if the function already forwards the full `BookingRequest` object.

**Relevant Context**
- [`booking_system_frontend/src/services/api.ts`](booking_system_frontend/src/services/api.ts)

**Status**: [x] done

---

## Sub-Task 8 — Frontend: Update FlightCard

**Intent**: Replace the single "Book Now" button with four per-class booking options that show the class name, its price, and its seat count.

**Expected Outcomes**
- Each flight card shows a 2×2 grid (or a column) of four class buttons.
- Each button displays: class label, derived price, remaining seats.
- A button is disabled and labelled "Sold Out" when that class has 0 seats.
- A low-seat warning (≤2) is shown per class in `solar-orange`.
- Clicking a class button calls `onBook(flight, seatClass)` — the parent receives both the flight and the chosen class.
- The `FlightCardProps` interface gains a `seat_class` parameter in the callback: `onBook: (flight: Flight, seatClass: SeatClass) => void`.

**Todo List**
1. Update `FlightCardProps.onBook` signature to `(flight: Flight, seatClass: SeatClass) => void`.
2. Remove the single seats/price block; replace with a 4-row class selector (label, price, seat count, Book button per row).
3. Style each class row distinctly (e.g. Economy — default white, Flexi — blue tint, Business — purple gradient, Galaxium — gold/amber gradient).
4. Pass `seatClass` when calling `onBook`.

**Relevant Context**
- [`booking_system_frontend/src/components/flights/FlightCard.tsx`](booking_system_frontend/src/components/flights/FlightCard.tsx)
- `SEAT_CLASS_LABELS` constant from Sub-Task 6.

**Status**: [x] done

---

## Sub-Task 9 — Frontend: Update Flights Page

**Intent**: The `Flights` page owns the `handleBookFlight` callback wired to `FlightCard`. It must now also hold the selected seat class and pass it through to `BookingModal`.

**Expected Outcomes**
- `handleBookFlight(flight, seatClass)` stores both `selectedFlight` and `selectedSeatClass` in local state.
- `selectedSeatClass` is passed as a prop to `BookingModal`.
- Search/filter logic is unchanged.

**Todo List**
1. Add `selectedSeatClass` state (`SeatClass | null`).
2. Update `handleBookFlight` to accept and store `seatClass`.
3. Pass `seatClass={selectedSeatClass}` prop to `<BookingModal>`.

**Relevant Context**
- [`booking_system_frontend/src/pages/Flights.tsx`](booking_system_frontend/src/pages/Flights.tsx)

**Status**: [x] done

---

## Sub-Task 10 — Frontend: Update BookingModal

**Intent**: `BookingModal` must display the chosen seat class and its price, and include `seat_class` in the booking API call.

**Expected Outcomes**
- `BookingModalProps` gains `seatClass: SeatClass`.
- The modal summary shows the seat class label prominently.
- The price shown is `flight[`${seatClass}_price`]` (the computed price from `FlightOut`).
- `bookFlight({..., seat_class: seatClass})` is called on confirmation.

**Todo List**
1. Add `seatClass: SeatClass` to `BookingModalProps`.
2. Show a "Seat Class" row in the flight summary section (class label + icon/badge).
3. Replace `flight.price` with `flight[`${seatClass}_price`]` in the price display.
4. Add `seat_class: seatClass` to the `bookFlight(...)` call.

**Relevant Context**
- [`booking_system_frontend/src/components/bookings/BookingModal.tsx`](booking_system_frontend/src/components/bookings/BookingModal.tsx)

**Status**: [x] done

---

## Sub-Task 11 — Frontend: Update BookingCard and MyBookings Page

**Intent**: Booked seat class should be visible in the user's booking history.

**Expected Outcomes**
- `BookingCard` shows the seat class as a badge or labelled row beneath the booking status.
- `MyBookings` requires no logic changes — `Booking` objects from the API will already carry `seat_class` once the backend is updated.

**Todo List**
1. In `BookingCard`: add a seat class badge (e.g. a coloured pill using the same class colour scheme from Sub-Task 8) showing `SEAT_CLASS_LABELS[booking.seat_class]`.
2. Display the class-specific price on the booking card (the `flight.{seatClass}_price` value if the `flight` prop is present).

**Relevant Context**
- [`booking_system_frontend/src/components/bookings/BookingCard.tsx`](booking_system_frontend/src/components/bookings/BookingCard.tsx)
- [`booking_system_frontend/src/pages/MyBookings.tsx`](booking_system_frontend/src/pages/MyBookings.tsx)

**Status**: [x] done

---

## Dependency Order

Sub-tasks must be implemented in this sequence (each depends on the one before):

```
1 (DB model)
 └─ 2 (schemas)
     └─ 3 (service)
         └─ 4 (server/MCP)
             └─ 5 (seed)
                 └─ 6 (TS types)
                     └─ 7 (API client — verify only)
                         └─ 8 (FlightCard)
                             └─ 9 (Flights page)
                                 └─ 10 (BookingModal)
                                     └─ 11 (BookingCard + MyBookings)
```
