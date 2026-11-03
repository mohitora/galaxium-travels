# Sub-Task 3 review

**Requested:** Verify Sub-Task 3 (refund preview and cancel services).

**Done:**
- Re-read `services/booking.py` and re-ran a throwaway in-memory check across all classes at +100h, +48h, +10h and -5h. Preview never mutated data, and cancel matched preview.
- User decided cancel and preview must agree, so `cancel_booking` now returns `BOOKING_NOT_CANCELLABLE` for any status other than `booked`.
- Re-checked: `completed` rejected with the seat count unchanged, `cancelled` still `ALREADY_CANCELLED`, `booked` cancels with refund 800.
- Corrected the Sub-Task 3 handoff note in `fare-rules-refunds-plan.md`.
