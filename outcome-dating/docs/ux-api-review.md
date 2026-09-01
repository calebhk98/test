# UX/API Review: Can a Good Mobile App Be Built on This Backend?

Scope: `src/http/routeTable.ts`, `src/http/routes/**`, `src/http/serializers/**`, and the
services behind them, read as the substrate a phone client has to render screens from.
No code changed — findings only.

**Bottom line:** the backend is well-engineered where it was clearly reviewed for scale
(discovery, timeline, matches all show real batching/pagination discipline), but several
whole features were built at the service layer and never wired to an HTTP route, and two
of the most-hit screens in the app (the "who liked me" inbox, and any first-run photo grid
reload) sit on a genuine N+1 or a dead end. Those are fixable without new business logic —
they're wiring gaps, not design gaps — which makes them cheap to fix and expensive to ship
around.

---

## Executive summary

- **Worst forced round trip:** `GET /interests/incoming` and `GET /interests/outgoing`
  (`src/http/routes/interests.routes.ts`) return bare `Interest` rows — `senderId`/
  `recipientId` and status timestamps only (`src/domain/types.ts` `Interest`, mapped by
  `src/services/interest.service.ts#mapRow`). No display name, no photo, no age. This is
  the "who liked me" / "your sent likes" screen — probably the single most-opened screen
  in a dating app after the discovery grid — and rendering one page of 20 requires the
  list call plus **20 separate `GET /profiles/:userId` calls**.
- **Most important missing state:** there is no way for a client to know something new
  happened without polling. `src/services/notification.service.ts` (list, mark-read) and
  `src/services/notifications/devices.ts` (push token registration) are fully built and
  tested, but **zero HTTP route exposes either one** — not in `src/http/routeTable.ts`,
  not in any `src/http/routes/*.ts` file. A push token can never reach the server, so push
  notifications are structurally impossible even though the whole delivery pipeline
  (`NOTIFICATION_TEMPLATES`, `deliverPending`, adapters under `src/services/notifications/`)
  exists and is exercised by tests.
- **Top 5 API changes**, in priority order (full list and file targets at the end):
  1. Wire `notification.service.ts#listMyNotifications`/`markNotificationRead` and
     `notifications/devices.ts#registerDeviceToken` to HTTP routes.
  2. Enrich `GET /interests/incoming`/`outgoing` with the counterpart's display name,
     primary photo, and age (mirror what `matches.service.ts` already does correctly).
  3. Add `GET /me/photos` (wire the already-built `photo.service.ts#listMyPhotos`), and
     add rejection-reason text to the photo upload response.
  4. Add `GET /venues/:venueId` (wire the already-built `venue.service.ts#getVenue`), and
     denormalize venue name + schedule onto the ticket/voucher response.
  5. Route `trust.service.ts#can()` — the capability/"why is this disabled" check that
     already exists with safe, user-displayable `reasonCode`s — so a client can gray out
     a button instead of guessing from a 403.

---

## 1. Onboarding & first-run

**What exists today:** `POST /auth/register` → `GET /me`, `PATCH /me/profile`,
`POST /me/photos`×N, `PUT /me/answers`, `PATCH /me/filters`. Each step's own endpoint is
fine in isolation.

**What's missing — blocks a good experience.** There is no aggregate "where am I in
onboarding" endpoint. `profileCompleteness` (`src/http/serializers/profile.ts`
`MyProfileView.profileCompleteness`) is a single 0–100 number computed by
`profile.service.ts#computeProfileCompleteness` from a documented weighted formula (name
15, bio 15, city 10, core fields 10, ≥1 photo 20, ≥3 photos 10, ≥5 answers 15, ≥1 tag 5) —
but **the breakdown is never returned**, only the total. A client cannot render "add 2 more
photos to finish your profile" from a `62`; it can only show a generic progress bar and
guess. The formula is entirely deterministic server-side — this is a pure serialization
gap, not a missing feature.

Compounding this: an onboarding checklist screen (photos done? questions done? filters
set? email verified?) currently requires assembling state from **five separate calls**
(`GET /me` for email verification, `GET /me/profile` for completeness, `GET /me/photos` —
which doesn't exist, see §3 — `GET /me/answers`, `GET /me/filters`), with no single source
of truth for "what step is next."

**Fix:** extend `MyProfileView` (`src/http/serializers/profile.ts`) with a
`completenessBreakdown: { hasName, hasBio, hasCity, photoCount, answeredQuestionCount,
tagCount }` object built from the same query `computeProfileCompleteness` already runs, so
the client can render specific missing-step copy instead of a bare percentage.

---

## 2. Question flow — blocks a good experience

This is the starkest gap in the whole review. There are **two parallel question systems**
in the codebase, and the client is stuck with the worse one.

- **New system** (`src/domain/questions/*`, `question.service.ts`'s second half): typed
  questions (scale/single-choice/multi-choice/frequency), value **+ importance**
  (`irrelevant` … `deal_breaker`), a ladder presentation, per-question skip/prefer-not-to-say
  on *any* question, deal-breaker-derived hard filters, tag intensity, avoid-tags, and — the
  piece that actually matters for a phone UI — `selectNextQuestionsForMe`, an adaptive "what
  should we ask next" selector, plus `listActiveQuestionBank`, which is properly
  cursor-paginated (default page 50, max 200; `src/services/question.service.ts` lines
  ~529–563). This is the system spec §8's value+importance model and the deal-breaker
  filters actually describe, and it's covered by `tests/unit/question.service.test.ts` and
  `tests/unit/questionBank600.test.ts`.
- **Old system**, the only one wired to HTTP (`src/http/routes/questions.routes.ts`):
  `GET /questions` → `question.service.ts#listActiveQuestions`, which has **no limit, no
  cursor, no category filter** — it is `SELECT * FROM questions WHERE active = true`, full
  stop. If the bank has hundreds of rows (the new bank's own test is literally named
  `questionBank600.test.ts`), a brand-new user's first screen fetches the entire bank in one
  uncapped response before they've answered a single question. `PUT /me/answers` only
  accepts flat 1–5 self/partner pairs; there's no ladder, no importance, no deal-breaker
  capture.

**Net effect for the client:** the question-flow screen the task explicitly calls out has
no "next 10 questions" endpoint, no adaptive ordering, no importance/deal-breaker capture,
and the one endpoint it does have returns an unbounded payload on first load.

**Fix:** route the new system —
`GET /question-bank` → `listActiveQuestionBank` (cursor pagination, already built),
`GET /question-bank/next` → `selectNextQuestionsForMe` (already built),
`PUT /question-bank/answers/:slug` → `putMyQuestionAnswer` (already built),
`GET/PUT /me/tag-intensity`, `GET/PUT /me/avoid-tags` — all in a new
`src/http/routes/questionBank.routes.ts`. Failing that, at minimum add a `limit`/`cursor` to
the *old* `GET /questions` in `src/http/routes/questions.routes.ts` so first load isn't
unbounded.

---

## 3. Profile / Settings (own profile + photos)

### 3a. The photo grid cannot be rendered — blocks a good experience

`photo.service.ts#listMyPhotos` is fully implemented (line 161) but is **only ever called
internally**, by `reorderPhotos`'s return value. There is no `GET /me/photos` route
(confirmed against `src/http/routeTable.ts` and every `app.get(...)` in
`src/http/routes/profile.routes.ts`), and the own-profile serializer,
`MyProfileView` in `src/http/serializers/profile.ts`, has **no `photoUrls` field at all**
(compare `PublicProfileResponse` two blocks below it in the same file, which does have
one). The only photo state a client ever sees is the direct return value of whichever
mutating call it last made (`POST /me/photos`, `.../primary`, `.../reorder`). On app
relaunch, the "your photos" grid on the profile-edit screen has **no endpoint to load
from at all** — it's not slow, it's impossible without the client caching state itself
(which then desyncs across devices).

Compounding this: `PhotoAnalysisResult.rejectionReasons` (`src/services/media/
moderation.port.ts`) is computed by the moderation port and used internally by
`setPrimaryPhoto`'s 400 error body, but the `UserPhoto` domain type
(`src/domain/types.ts`) that `uploadPhoto` actually returns has **no reason field** — a
rejected/flagged photo comes back with `moderationStatus: 'rejected'` and no "why." A user
sees a photo silently vanish from acceptability with zero explanation.

**Fix:** add `GET /me/photos` → `photo.service.ts#listMyPhotos` in
`src/http/routes/profile.routes.ts`; add `rejectionReasons: string[]` to `UserPhoto`
(`src/domain/types.ts`) and thread it through `photo.service.ts#mapPhoto`.

### 3b. Physical-attribute fields are computed but silently dropped — blocks a good experience

`profile.service.ts`'s own module doc says it outright: `ProfileWithAttributes` (returned
by `getMyProfile`/`updateMyProfile`) carries `heightCm`, `weightG`, `weightVisible`,
`bodyType`, `unitPreference`, `distancePrecisionFloorKm` — but `MyProfileView`
(`src/http/serializers/profile.ts`) was never updated to forward them. A user sets their
height in Settings (`PATCH /me/profile` with `heightCm`), the write succeeds, and the very
next `GET /me/profile` **does not return it** — a plainly broken save-then-reload round
trip on the Settings screen, for a feature the backend otherwise fully supports (it does
show up on the *public* profile view, `PublicProfileResponse`, just not to the owner
editing it).

**Fix:** add the six fields to `MyProfileView` and `serializeMyProfile` in
`src/http/serializers/profile.ts`.

---

## 4. Discovery grid

This is one of the better-built surfaces. `getDiscoveryGrid` (`src/services/
discovery.service.ts`) batches every gate (moderation, capacity, mutual filters, shared
tags) across the whole candidate pool instead of per-row, caps the candidate pool at 500
(`MAX_CANDIDATE_POOL_SIZE`), and the card shape (`DiscoveryCardView`,
`src/http/serializers/discovery.ts`) is deliberately thin — no compatibility score, no
popularity, at most one shared tag. Pagination is a real cursor. Empty state is handled:
`NO_CANDIDATES_MESSAGE` is embedded directly in the response body when `items` is empty
(`discovery.routes.ts`), so the client doesn't need a second call or a hardcoded string to
explain a dead grid. This is the pattern the rest of the API should copy.

**Minor gap — would be nice.** `DiscoveryCandidate` has no "you already sent this person
an interest" flag. A user can tap Like on a card they already liked and get a 409
(`'You already have a pending interest with this person.'`) instead of the button simply
being disabled. Low severity (cheap to recover from), but easy to fix by joining the
caller's own outgoing-pending set into the card query.

---

## 5. Profile detail (viewing someone else) — single call, fine

`GET /profiles/:userId` → `serializePublicProfile` returns everything the profile-detail
screen needs in one call: photos, bio, distance, trust level, visible tags, height/body
type. No round-trip issue here.

---

## 6. Interests — "who liked me" / "your sent likes" — **worst N+1 in the API**

`GET /interests/incoming` and `GET /interests/outgoing`
(`src/http/routes/interests.routes.ts`) send the raw `Interest` object straight through
with no serializer at all (`reply.send(await interestService.listOutgoing(...))`), and
`Interest` (`src/domain/types.ts`) carries only `id`, `senderId`, `recipientId`, `status`,
`policySnapshot`, and status timestamps. **No display name. No photo. No age.**

This is the single most damaging round-trip problem in the review, worse than the ticket
one below, because it sits on a screen every active user opens constantly: to render one
page of 20 incoming likes with a name and photo, a client must follow the list call with
**20 individual `GET /profiles/:userId` calls**. On cellular, that's the difference
between a screen that paints in one round trip and one that trickles in over 20,
individually-latent requests, each with its own auth/TLS overhead. There is no reasonable
way to build a good "who liked me" screen against this endpoint as it stands.

As a secondary issue, `policySnapshot` (internal config values: `interest.expiry_hours`,
`interest.outgoing_pending_limit`, `interest.incoming_pending_limit`) is sent to the
client verbatim on every row — harmless but pure noise the client will never use, on a
response that's already too thin where it matters.

**Fix:** give `interest.service.ts#listOutgoing`/`listIncoming` a batched profile-lookup
join (same pattern `matches.service.ts#listMyMatches` already uses correctly — see §7),
and add a real serializer in `src/http/serializers/interests.ts` (doesn't exist yet)
exposing `displayName`/`primaryPhotoUrl`/`age`/`approximateDistanceKm` per row instead of
the bare ids, dropping `policySnapshot` from the wire shape.

---

## 7. Matches list — well designed, use as the template

`GET /matches` (`src/services/matches.service.ts`) is the one list endpoint in this API
that gets it right: one call returns `displayName`, `primaryPhotoUrl`,
`approximateDistanceKm`, `conversationStatus`, `lastMessagePreview` (truncated to 140
chars — good payload discipline), `lastMessageAt`, `unreadCount`, and a pre-computed
`lastActivityAt` sort key the client never has to re-derive. It's properly cursor-paginated
and documents its own degenerate case (a row can be silently dropped if the other party
blocked the caller or deleted their account, without corrupting `nextCursor`/pagination).
This is exactly the shape `GET /interests/*` (§6) and the ticket list (§10) are missing —
worth pointing whoever fixes those at this file as the reference implementation.

**Minor inconsistency — would be nice.** `GET /conversations` (the older, spec-literal
§24.7 route, `conversation.service.ts#listMyConversations`) is unbounded — no cursor, no
limit, returns every conversation the caller has ever had — and returns none of the
richness `/matches` does (no preview, no unread count). Since every `conversations` row is
definitionally a match (`matches.service.ts`'s own module doc: a conversation is created
in exactly one place, `acceptInterest`), these are two views of the same data with very
different quality and one of them unbounded. A heavy user with hundreds of matches turns
`GET /conversations` into an ever-growing payload. Recommend clients standardize on
`/matches` and either paginate `/conversations` to match or deprecate it.

---

## 8. Conversation / chat

`GET /conversations/:id/timeline` (`src/services/timeline.service.ts`) is the standout
piece of this review — it deliberately solves the N+1 that a naive "messages + date
proposals" screen would otherwise have, by merging both streams into one `UNION ALL`
query with correct keyset pagination, and denormalizing `venueName` inline so a date-card
in the middle of a chat thread doesn't need a follow-up venue call. This is good, and
should be the client's primary feed for a conversation screen (not `GET /messages` +
`GET /date-proposals` stitched client-side).

**Real-time gap — blocks a good experience, cross-cutting, see §13.** There is no way to
know a new message arrived without polling `GET /conversations/:id/timeline` on a loop.
See the Notifications section below.

**Retry safety — would be nice.** `POST /conversations/:id/messages`
(`message.service.ts#sendMessage`) has no client-supplied idempotency key and no unique
constraint tying a send to a client-generated id. A dropped response on flaky cellular
(request succeeded server-side, ack lost) gives the client no way to distinguish "my
message didn't send, retry" from "it sent, I just didn't hear back" — retrying blindly can
double-send. Compare `POST /interests`, which is naturally idempotent on retry because of
the `uq_interests_pending_pair` unique constraint (a retried duplicate 409s cleanly instead
of creating a second row). Messages have no equivalent guard.

**Fix:** accept an optional client-generated `clientMessageId` on
`POST /conversations/:id/messages`, unique-indexed per conversation, so a retried send is a
safe no-op / returns the original row instead of creating a duplicate.

---

## 9. Date proposal flow

The state machine and payment choreography here (`dateProposal.service.ts`) are the most
carefully retry-engineered part of the codebase, and it's worth saying so: every step is
individually idempotent, a per-proposal `pg_try_advisory_lock` prevents a client
double-tap from double-capturing or double-refunding, and a crashed/retried
`acceptDateProposal` resumes exactly where it left off rather than re-charging anyone. This
is exactly the offline/retry discipline the rest of the money-moving surface should have.

**One rough edge for a client — would be nice.** The advisory-lock loser gets a
`ConflictError` — `'This date proposal is already being modified by a concurrent
request.'` — which is a *retry-safe, transient* condition (try again in a second), but it
carries the same generic `409 conflict` code as a genuine illegal-state conflict (e.g.
accepting an already-declined proposal), which is *not* retry-safe. A client cannot tell
these apart from the error code alone and has to pattern-match on message text, which is
fragile. **Fix:** give the lock-contention case its own `code` (e.g. `locked_retry`) so a
client can safely auto-retry one and surface the other as a real error.

**Missing enrichment — blocks a good experience.** `GET /date-proposals/:id`
(`dates.routes.ts`) sends the raw `DateProposal` domain object straight through with no
serializer — `venueId` only, no venue name/address; `proposerId`/`recipientId` only, no
counterpart name/photo. A client landing on this screen directly (e.g. from a push deep
link, once push exists) has to separately resolve the venue (see §10 below — there is no
single-venue GET) and the other participant's profile. Inside an existing conversation
this is masked by the timeline endpoint's denormalization (§8), but a direct fetch has no
such help.

---

## 10. Wallet / Tickets

`GET /tickets` (`voucher.service.ts#listMyVouchers`) returns raw `Voucher[]` — `id`,
`dateProposalId`, `venueId`, `code`, `qrPayload`, `status`, `issuedAt`, `expiresAt`,
`redeemedAt`. **No venue name or address, and no date/time** — those live on
`DateProposal`, not `Voucher`. To render a wallet screen ("Coffee at The Daily Grind, Sat
6:00 PM") for M tickets, a client needs the list call, plus one `GET /date-proposals/:id`
per ticket for the schedule, plus a venue lookup per ticket.

The venue lookup is the worse half: `venue.service.ts#getVenue` (single-venue fetch) is
fully implemented but **has no route** — only `GET /venues` (full list) and
`GET /venues/:venueId/time-slots` are wired (`src/http/routeTable.ts`,
`src/http/routes/dates.routes.ts`). `listActiveVenues` also has **no pagination** — it's
`SELECT * FROM venues WHERE active = true ORDER BY name`, unbounded. So resolving one
ticket's venue name means fetching the *entire active venue table* and filtering
client-side, and doing that per ticket compounds it further absent client-side caching.

**Fix:** add `GET /venues/:venueId` → the already-built `venue.service.ts#getVenue`
(`src/http/routes/dates.routes.ts`), and add a `src/http/serializers/tickets.ts` that
denormalizes `venueName`, `venueAddress`, `scheduledStart`, `scheduledEnd` onto each
voucher row the same way `timeline.service.ts` already does for date-proposal events in
chat — the query pattern already exists in this codebase, it just isn't applied here.

---

## 11. Trust & safety page

`GET /me/trust` is a clean single call (`trustService.getMyTrustSummary` +
`serializeTrustSummary`): trust level, gated raw score, static `actionableImprovements`/
`recentNegativeEvents` copy. Good.

**Missing wiring — blocks a good experience.** `trust.service.ts#can()` (line ~503) is
exactly the capability-check primitive the review is looking for: given an action
(`browse` / `send_interest` / `chat` / `send_links` / `propose_date`) and a trust level, it
returns `{ allowed, limited?, linkMode?, reasonCode? }` where `reasonCode` is explicitly
documented as "static, stable reason code — safe to show to the user." This is precisely
the "why is this action unavailable" state the task brief asks about — and **it is never
called from any HTTP route** (`grep` across `src/http/routes/*.ts` for it returns nothing;
`trust.routes.ts` only wires `getMyTrustSummary`/`listMyTrustEvents`/`submitAppeal`). A
client currently has two bad options: reimplement the trust-tier comparisons locally (which
will drift from `trust.link_min_level`/`interest.*` config the moment an admin retunes
them), or find out an action is blocked by attempting it and parsing a 403/429. Neither is
what "the button is visibly disabled with a reason" needs.

**Fix:** add `GET /me/capabilities` (or `GET /me/capabilities/:action`) →
`trustService.can()` in `src/http/routes/trust.routes.ts`, returning the decision for each
`TrustGatedAction` so the client can pre-render disabled states.

---

## 12. Payments / wallet settings

`POST/GET/DELETE /payment-methods` is a clean, minimal surface — card brand/last4 only,
never a raw token (`src/http/serializers/payment.ts`). No round-trip issue.

The payment/date-proposal money flow's retry safety is covered in §9 above.

---

## 13. Real-time — cross-cutting, most important gap in the review

Spec §20.2 requires three channels: push, email, **in-app notification center** (marked
`MUST`, conformance ID `C-20.2.1` in `docs/conformance.md`). The service layer fully
implements this:

- `src/services/notification.service.ts`: `notify` (writes a row from a fixed
  `NOTIFICATION_TEMPLATES` registry, structured-payload-only, no free text — a genuinely
  good design), `listMyNotifications` (cursor-paginated, `unreadOnly` filter),
  `markNotificationRead`, `deliverPending`.
- `src/services/notifications/devices.ts`: device/push-token registration, with correct
  reassignment semantics for a shared/resold device.

**None of it is reachable over HTTP.** `src/http/routeTable.ts` has no `/notifications`
entry, no `/devices` entry, and `grep` for either across `src/http/routes/*.ts` returns
nothing. Concretely, this means:

- A client can never register an APNs/FCM token, so **push notifications are impossible
  in production**, independent of which push adapter (`fake.push.ts`/`apns.push.ts`/
  `fcm.push.ts`) is configured — the pipeline has nothing to send *to*.
- There is no in-app notification feed endpoint, so the one channel spec §20.2 calls
  "notification center" doesn't exist as an API surface either.
- Several event types have **no other endpoint that would ever surface them** to a
  client, notification center or not: `trust_level_changed`, `safety_notice`,
  `chat_cooling`, `interest_expiring_soon`. A user's trust level can change, or a safety
  banner condition can fire, and there is currently no way for any client to learn about
  it at all — not even by polling something else.
- Every other "did something change" question (new match, new message, new incoming
  interest, ticket issued, date accepted) is left to the client polling the relevant list
  endpoint on a timer. That's expensive at scale (multiplied by every active session) and
  each of those endpoints is a *state* fetch, not a *change* fetch — there's no
  `If-Modified-Since`/`ETag`/`updatedSince` support anywhere in this API for cheap
  poll-and-diff, so a "did anything change" poll costs the same as a full re-render.

**Fix, in priority order:**
1. `POST /devices` / `DELETE /devices/:id` → `notifications/devices.ts#registerDeviceToken`
   (new `src/http/routes/devices.routes.ts`) — without this, push is dead on arrival
   regardless of anything else.
2. `GET /notifications` (cursor-paginated, `unreadOnly` query param already supported by
   the service) and `POST /notifications/:id/read` →
   `notification.service.ts#listMyNotifications`/`markNotificationRead` (new
   `src/http/routes/notifications.routes.ts`).
3. Longer-term: an `updatedSince` or cursor parameter on the cheap list endpoints
   (`/matches`, `/interests/incoming`) so a foreground poll can ask "anything new since
   my last cursor" instead of re-fetching the current page every time.

---

## 14. Errors as user experience — cross-cutting

The error envelope itself (`src/http/errors.ts`) is well-designed: a stable
`{ error: { code, message, details } }` shape, a real typed hierarchy
(`src/lib/errors.ts`), and `code` is explicitly documented as a frozen part of the API
contract. Several messages are also deliberately, correctly generic for privacy reasons —
e.g. `RECIPIENT_UNAVAILABLE_MESSAGE` in `interest.service.ts` intentionally can't be told
apart from a filter mismatch, an inbox-full recipient, or a chat-cap recipient, so an
attacker can't probe someone's filters by sending interests and reading error text. That's
the right tradeoff and worth preserving.

But `message` is inconsistently treated as user-facing vs. developer-facing, and because
the envelope sends `message` straight to the wire, whatever string a service throws *is*
what a client not doing manual per-code copy-mapping will show a user. Concrete
examples actually thrown today:

- **Spec section references baked into the string**, verbatim:
  - `src/services/dateProposal.service.ts:388` —
    `'Date proposals can only be created from an active conversation (spec §13.1)'`
  - `src/services/behavioralPrompt.service.ts:188` —
    `'Both selfValue and partnerValue are required when not skipping (§8.1 dual answer)'`
- **Raw parameter/internal-name leaks** — every one of these is a real thrown
  `ValidationError`/`ConflictError` message, not a log line:
  - `'voucherId must be a uuid'`, `'dateProposalId must be a uuid'`,
    `'userId must be a uuid'` (multiple services)
  - `'photoId does not belong to candidateUserId.'` (photoExperiment.service.ts)
  - `'Illegal date proposal transition: \'accepted\' -> \'refunded\''`
    (dateProposal.service.ts) — exposes the internal state-machine vocabulary directly
  - `'Cannot capture a hold in status \'authorized\''` (payment.service.ts) — same, for
    payment hold states

None of these are wrong to *have* as internal diagnostic text — the problem is they're the
same string that reaches `error.message` on the wire, with nothing about the response
distinguishing "safe to show verbatim" from "log this, show generic copy instead."

**Fix:** add a `userMessage` (or `displayable: boolean`) convention to `AppError`
(`src/lib/errors.ts`) — services that already write good, generic, privacy-conscious copy
(the interest/date-proposal rate-limit messages, `RECIPIENT_UNAVAILABLE_MESSAGE`, the §30.x
static-copy constants) opt in explicitly; everything else defaults to a generic
per-`code` fallback the client owns, so a validation slip in a new service can't leak
internal vocabulary by default.

---

## 15. Empty / first-run / edge states

- **Discovery grid** (§4) handles this well: an empty page embeds
  `NO_CANDIDATES_MESSAGE` directly in the body.
- **Reality dashboard** (`GET /discovery/reality`) gives a new user with no matches
  three honest counts (`matchesMyFilters`/`whoseFiltersIMatch`/`mutualMatchPool`) in one
  call — good building block for "here's why you're not seeing anyone yet."
- **Matches / interests / tickets / notifications-that-don't-exist-yet**: all just return
  an empty array with no explanatory `message` field, unlike discovery. Not wrong (an
  empty list is self-explanatory in most of these), but inconsistent — a client has to
  hardcode its own "no matches yet" / "no tickets yet" copy for every one of these screens
  instead of getting a hint from the API the way it does for discovery. Low severity,
  **would be nice** for consistency.
- **Post-date check-in** (`GET /date-proposals/:id/check-in`) 404s when the caller hasn't
  submitted one yet (`postDateFeedback.service.ts#getMyCheckIn`) — a reasonable, standard
  "absence via 404" pattern; flagged only because it's the one first-run case in the API
  that uses 404-as-empty-state rather than 200-with-empty-body, worth the client knowing
  going in.
- **Photo upload, first photo** (§3a): a rejected/flagged first photo has no reason string
  reaching the wire at all (see §3a) — this is the sharpest first-run edge case in the
  review: a brand-new user's very first action can fail silently.

---

## 16. Optimistic updates & offline — cross-cutting summary

| Operation | Retry-safe today? | Notes |
|---|---|---|
| `POST /interests` | Yes | `uq_interests_pending_pair` unique constraint makes a retried duplicate 409 cleanly. |
| `POST /date-proposals/:id/accept`/`cancel`/`decline` | Yes | Per-proposal advisory lock + resumable checkpoints (see §9). Best offline design in the API. |
| `POST /conversations/:id/messages` | **No** | No idempotency key; a retried send after a dropped ack can double-send (see §8). |
| `POST /webhooks/payments` | Yes | Explicitly documented as idempotent (dup ledger-row check). |
| `POST /reports` | Unverified — no unique constraint spotted; likely double-files a duplicate report on retry, low harm (moderation dedupes downstream) but not confirmed here. |
| `PATCH /me/filters`, `PATCH /me/profile` | Yes (PUT/PATCH-shaped, naturally idempotent) | |

The one gap worth fixing is messages (§8's fix above); the rest of the money-moving and
matching surface is in good shape for a lossy connection.

---

## Ranked findings

### Blocks a good experience
1. `GET /interests/incoming`/`outgoing` return no profile enrichment — forces a 1+N round
   trip on the "who liked me" screen (§6).
2. No HTTP route for notifications or device-token registration — push is impossible,
   several event types are unreachable by any client mechanism (§13).
3. No `GET /me/photos` — the own-profile photo grid cannot be reloaded via any endpoint
   (§3a).
4. New question-bank system (adaptive selection, importance, deal-breakers) is fully built
   and unrouted; the live `/questions` route is unbounded (§2).
5. `MyProfileView` silently drops height/weight/body-type/unit-preference/distance-floor
   fields the service computes — a broken Settings save-then-reload round trip (§3b).
6. Ticket/wallet screen has no venue name/schedule on the voucher, and no single-venue GET
   exists to resolve it without fetching the entire venue table (§10).
7. `trust.service.ts#can()` — the "why is this disabled" capability check — is built and
   unrouted, forcing client-side reimplementation of trust-tier gating logic (§11).
8. Error messages leak spec section references and internal state-machine/parameter names
   to the client verbatim (§14).
9. First photo rejection carries no reason to the wire — a new user's first action can
   fail with zero explanation (§3a, §15).

### Would be nice
- Discovery card has no "already liked" flag (§4).
- `GET /conversations` is unbounded and duplicates `/matches` with less data (§7).
- No idempotency key on message send (§8).
- Lock-contention 409 on date-proposal actions isn't distinguished from a real conflict
  (§9).
- No quota/reset-time visibility for interest rate limits (interest.service.ts enforces
  outgoing-pending, daily, and recipient-capacity caps entirely server-side with no GET to
  preview remaining quota, and `RateLimitError` carries `limit` but no `resetsAt`/
  `retryAfterSeconds` — a client can't show a countdown, only "try again later").
- Inconsistent empty-state messaging across list endpoints (§15).

---

## Priority list of API additions

For each: the concrete change and the file it lands in. All of these wire *existing,
already-implemented, already-tested* service functions unless noted otherwise — none
require new business logic.

1. **`POST /devices`, `DELETE /devices/:id`** → `notifications/devices.ts#registerDeviceToken`
   — new `src/http/routes/devices.routes.ts`.
2. **`GET /notifications`, `POST /notifications/:id/read`** →
   `notification.service.ts#listMyNotifications`/`markNotificationRead` — new
   `src/http/routes/notifications.routes.ts`.
3. **Enrich `GET /interests/incoming`/`outgoing`** with `displayName`/`primaryPhotoUrl`/
   `age`/`approximateDistanceKm` — `src/services/interest.service.ts`
   (`listOutgoing`/`listIncoming`, batched profile join like `matches.service.ts`), new
   `src/http/serializers/interests.ts`, wired in `src/http/routes/interests.routes.ts`.
4. **`GET /me/photos`** → `photo.service.ts#listMyPhotos` —
   `src/http/routes/profile.routes.ts`. Add `rejectionReasons: string[]` to `UserPhoto`
   (`src/domain/types.ts`) and `photo.service.ts#mapPhoto`.
5. **`GET /venues/:venueId`** → `venue.service.ts#getVenue` —
   `src/http/routes/dates.routes.ts`. Denormalize venue name/schedule onto vouchers via a
   new `src/http/serializers/tickets.ts`, following `timeline.service.ts`'s existing
   pattern.
6. **`GET /me/capabilities`** → `trust.service.ts#can()` for each `TrustGatedAction` —
   `src/http/routes/trust.routes.ts`.
7. **Add the six missing physical-attribute fields to `MyProfileView`** —
   `src/http/serializers/profile.ts`.
8. **Route the new question bank**: `GET /question-bank`, `GET /question-bank/next`,
   `PUT /question-bank/answers/:slug`, `GET/PUT /me/tag-intensity`,
   `GET/PUT /me/avoid-tags` — new `src/http/routes/questionBank.routes.ts`, all backed by
   existing `question.service.ts` exports. Add pagination to the old `GET /questions` at
   minimum if the new bank isn't routed yet — `src/http/routes/questions.routes.ts`.
9. **`clientMessageId` idempotency key on `POST /conversations/:id/messages`** —
   `src/services/message.service.ts` + a unique index.
10. **`completenessBreakdown` on `MyProfileView`** — `src/http/serializers/profile.ts`,
    `src/services/profile.service.ts#computeProfileCompleteness`.
