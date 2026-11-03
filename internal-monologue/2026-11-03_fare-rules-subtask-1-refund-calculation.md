# Fare rules — Sub-Task 1: refund rules and calculation

**Requested:** implement only Sub-Task 1 of `fare-rules-refunds-plan.md` (backend refund rules and calculation).

**Done** (all in `booking_system_backend/schemas.py`, beside `SEAT_CLASS_MULTIPLIERS`):
- `REFUND_RULES` table: refund percent and cutoff hours per class (Economy 80%/72h, Flexi 100%/24h, Business 75%/none, Galaxium 100%/none).
- `parse_departure_time()`: parses ISO strings with a `Z` suffix into aware UTC datetimes.
- `calculate_refund(seat_class, base_price, departure_time, now)`: no DB access; class price rounded like `FlightOut`; returns 0 at or inside a cutoff and at or after departure.

**Checked:** short python one-liner covering 1s either side of the 72h and 24h cutoffs, and before/after departure for Business and Galaxium. No pytest tests yet (Sub-Task 5).

**Plan file:** Sub-Task 1 marked `[x] done` with handoff notes. Models, services, server, seed and frontend untouched.
