# Sub-Task 6 review

**Requested:** Verify Sub-Task 6 (frontend types and API client).

**Done:**
- Checked `src/types/index.ts`: `Booking.refund_amount`, `RefundPreview`, and `SEAT_CLASS_REFUND_POLICY` with the sync comment.
- Checked `src/services/api.ts`: `getRefundPreview` calls `GET /refund-preview/{id}` with JSDoc.
- Re-ran `npm run build` (passes) and `npm run lint` (13 problems, 11 errors and 2 warnings, matching the sub-task's reported baseline in untouched files; baseline not independently re-measured).
- Plan shows Sub-Tasks 1-6 done.
