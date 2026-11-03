# Fare rules Sub-Task 6: frontend types and API client

**Requested:** Implement only Sub-Task 6 of `fare-rules-refunds-plan.md`.

**Done:**
- `src/types/index.ts`: added `Booking.refund_amount: number | null`, `RefundPreview` interface, and `SEAT_CLASS_REFUND_POLICY` (static text, comment to keep in sync with backend `REFUND_RULES`).
- `src/services/api.ts`: added `getRefundPreview(bookingId)` calling `GET /refund-preview/{id}`.
- No code constructed `Booking` literals, so the required field broke nothing.
- `npm run build` passes. `npm run lint` unchanged: 13 pre-existing problems (11 errors, 2 warnings), none introduced, none fixed.
- Plan file: Sub-Task 6 marked done with handoff notes for Sub-Tasks 7 and 8.
- Stopped before Sub-Task 7.
