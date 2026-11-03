# Fare rules — Sub-Task 2: model, schemas, seed

**Requested:** Implement only Sub-Task 2 of `fare-rules-refunds-plan.md`.

**Done:**
- `models.py`: added nullable `Booking.refund_amount` (Integer).
- `schemas.py`: added `BookingOut.refund_amount: Optional[int] = None` and new `RefundPreviewOut` (booking_id, seat_class, class_price, refund_amount, refund_percent, departure_time).
- `seed.py`: cancelled bookings get `refund_amount` via `calculate_refund` (aware UTC `now`, flight `price`, `departure_time`); others stay `None`. Left the duplicate `SEAT_CLASSES` list alone.
- Validated with a fresh `booking.db`: all cancelled rows have a refund, booked/completed have none. Deleted `booking.db` afterwards.
- Plan file: Sub-Task 2 marked done with handoff notes (incl. open decision on `refund_percent` semantics for Sub-Task 3).

**Not touched:** services, server, tests, frontend.
