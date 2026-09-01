# UX/API review: can a good mobile app be built on this backend?

A read of `src/http/routeTable.ts`, `src/http/routes/**`, and the services behind them, as the substrate a phone client renders screens from. Most of the "blocks a good experience" findings below are now fixed by wiring routes to service functions that already existed; a handful of smaller "would be nice" items remain open.

## Fixed since the original review

- **Notifications and device tokens are now routed.** `GET /notifications`, `POST /notifications/:notificationId/read`, and `GET|POST|DELETE /devices` all exist (`routeTable.ts`), so push registration and the in-app notification center are both reachable. This was the single biggest gap in the original review: push was structurally impossible without it.
- **`GET /me/photos` exists**, wired to `photo.service.ts#listMyPhotos`, so the own-profile photo grid can be reloaded on app relaunch instead of only ever reflecting the last mutating call's response.
- **The new question-bank system is routed.** `GET/PUT` routes for the typed question bank, adaptive selection, tag intensity, and avoid-tags are wired (see `src/http/routes/questions.routes.ts`), and the old, unbounded, no-skip `questions`/`answers` system is gone entirely.
- **`MyProfileView` now returns the physical-attribute fields** (height, weight, body type, unit preference, distance-precision floor) that `updateMyProfile` already accepted, closing the broken save-then-reload round trip on the Settings screen.
- **`GET /venues/:venueId` exists**, and the ticket/voucher response now denormalizes venue name, address, and schedule directly onto each voucher (`src/http/serializers/tickets.ts`), so a wallet screen no longer needs to fetch the entire venue table to resolve one ticket.
- **`GET /me/capabilities` exists**, wired to `trust.service.ts#can()`, so a client can gray out a disabled action with its safe, documented reason code instead of guessing from a 403.
- **`GET /interests/incoming`/`outgoing` are enriched** with display name, primary photo, age, and approximate distance (`interest.service.ts`), closing what was the worst N+1 in the API (20 individual profile fetches to render one page of "who liked me").

## Still open

- **Error messages still leak internal vocabulary to the wire.** Several thrown `ValidationError`/`ConflictError` messages still bake in spec section references (`'... (spec §13.1)'`) or raw internal state names (`"Illegal date proposal transition: 'accepted' -> 'refunded'"`), and the response envelope sends `message` straight to the client with no `displayable` flag distinguishing safe copy from a diagnostic string. A `tests/unit/copyGuard.test.ts`-style scan already prevents spec citations from leaking into user-facing copy in `src/services/**`/`src/http/**`; a similar `userMessage`/`displayable` convention on `AppError` would let a client render one consistent generic fallback for everything else.
- **First photo rejection still doesn't carry a reason onto the wire in the returned object.** `photo.service.ts` computes rejection reasons internally and uses them in the 400 error body for `setPrimaryPhoto`, but the `UserPhoto` domain type `uploadPhoto` returns still has no `rejectionReasons` field, so a rejected photo comes back with only `moderationStatus: 'rejected'` and no why.
- **No idempotency key on message send.** `POST /conversations/:id/messages` has no client-supplied id and no unique constraint, so a dropped response after a successful send can double-send on retry. Compare `POST /interests`, which is naturally idempotent via `uq_interests_pending_pair`.
- **`GET /conversations` is still unbounded** and duplicates `/matches` with less data (no preview, no unread count, no cursor). Recommend clients standardize on `/matches`.
- **No "already liked" flag on a discovery card.** Tapping Like on someone already liked returns a 409 instead of a pre-disabled button. Low severity, cheap to add via a join against the caller's own outgoing-pending set.
- **The lock-contention 409 on date-proposal actions isn't distinguished from a real conflict.** A retry-safe "someone else is modifying this right now" and a genuine "already declined" both carry the same generic `conflict` code; a client can't tell them apart without pattern-matching message text.
- **No `completenessBreakdown` on `MyProfileView`.** The onboarding-progress number is still a bare 0-100 percentage with no per-field breakdown a client could use to say "add 2 more photos," even though the underlying computation already has that detail.
- **Inconsistent empty-state messaging.** Discovery embeds a real explanatory message when a page is empty; matches, interests, and tickets just return an empty array with no hint.

## What's genuinely well built, use as the template

`GET /matches` (`matches.service.ts`) is the one list endpoint that gets everything right in one call: display name, photo, distance, conversation status, a truncated message preview, unread count, and a real cursor. `GET /conversations/:id/timeline` merges messages and date-proposal events into one correctly keyset-paginated feed with venue names denormalized inline, avoiding the N+1 a naive client-side stitch would hit. The date-proposal flow (`dateProposal.service.ts`) is the most carefully retry-engineered surface in the API: every step is individually idempotent, a per-proposal advisory lock prevents a double-tap from double-capturing, and a crashed `acceptDateProposal` resumes exactly where it left off.
