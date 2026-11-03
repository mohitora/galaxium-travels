# Sub-Task 3: Backend Services for Preview and Cancel

## Request
Implement Sub-Task 3 from `fare-rules-refunds-plan.md`:
- Add `get_refund_preview` service function in `booking_system_backend/services/booking.py` returning `RefundPreviewOut | ErrorResponse` without mutating DB state.
- Update `cancel_booking` to calculate and store `refund_amount` on the `Booking` record before committing.
- Share refund calculation logic between preview and cancel.
- Validate using an in-memory SQLite script across all seat classes on both sides of cutoff boundaries.
- Update plan file with handoff notes.

## Actions Taken
1. Added helper `_compute_refund(flight: Flight, seat_class: str, now: Optional[datetime] = None) -> int` to `booking_system_backend/services/booking.py` ensuring consistent calculation.
2. Implemented `get_refund_preview(db: Session, booking_id: int) -> RefundPreviewOut | ErrorResponse`:
   - Validates booking exists (`BOOKING_NOT_FOUND`).
   - Checks if cancelled (`ALREADY_CANCELLED`).
   - Rejects non-`booked` statuses (`BOOKING_NOT_CANCELLABLE`).
   - Checks if associated flight exists (`FLIGHT_NOT_FOUND`).
   - Returns `RefundPreviewOut` with class price, refund amount, class rule `refund_percent`, and departure time.
3. Updated `cancel_booking(db: Session, booking_id: int) -> BookingOut | ErrorResponse`:
   - Computes `refund_amount` via `_compute_refund` (or 0 if flight is missing).
   - Sets `booking.refund_amount = refund_amount`.
   - Restores exactly one seat in the booking's seat class.
   - Sets `booking.status = "cancelled"` and commits.
4. Validated implementation with a throwaway in-memory script covering:
   - Economy (>72h and <=72h).
   - Flexi (>24h and <=24h).
   - Business (before dep and after dep).
   - Galaxium (before dep and after dep).
   - DB non-mutation on preview.
   - Seat count increments and `refund_amount` persistence on cancel.
   - All error handling codes (`BOOKING_NOT_FOUND`, `ALREADY_CANCELLED`, `BOOKING_NOT_CANCELLABLE`, `FLIGHT_NOT_FOUND`).
5. Updated `fare-rules-refunds-plan.md` Sub-Task 3 status to `[x] done` with detailed handoff notes.
