# Fare rules Sub-Task 7: refund preview in cancel modal

**Requested:** Implement only Sub-Task 7 of `fare-rules-refunds-plan.md`: show the refund preview in the cancel modal on `MyBookings.tsx`.

**Done:**
- `MyBookings.tsx` only. `handleCancelClick` fetches `getRefundPreview`; stale responses are ignored via a request-id ref; `handleCloseCancelModal` resets preview state.
- Modal shows a spinner while loading, "You'll get {amount} back" when `refund_amount > 0`, else "No refund applies if you cancel now", plus the class policy text. A preview failure shows a toast and an inline note but never blocks cancelling.
- Success toast now uses the cancel response's `refund_amount`. The list reloads via `loadData()`, so `refund_amount` is in state.
- Plan file: Sub-Task 7 marked done with handoff notes for Sub-Task 8.

**Validation:**
- `npm run build` passes. `npm run lint` unchanged at 13 problems (11 errors, 2 warnings), all pre-existing.
- curl against the live backend: Economy booking previewed at 800000 (80%), cancelled with `refund_amount` 800000, second preview gave `ALREADY_CANCELLED`. Server stopped and `booking.db` deleted (it is tracked in git, so it shows as deleted).
- Not verified in a browser; the modal was not visually checked.
