# Architecture

A companion to [`README.md`](../README.md) for someone about to change code,
not just run it: the module dependency graph and what's allowed to call
what, the invariants that must never break, where each is enforced and
which test would catch a violation, and the extension points you'll
actually reach for.

## Layering

```
src/http/routes/*.routes.ts   Fastify handlers. Parse/validate input
                               (zod), call exactly one service function,
                               serialize the result through an explicit
                               allowlist serializer (src/http/serializers/*)
                               — never `{...spread}` a DB row onto the wire.
        │
        ▼
src/services/*.service.ts     Business logic. Every exported function's
                               first parameter is `Ctx` (src/lib/ctx.ts).
                               Reads/writes Postgres directly via `ctx.db`
                               — no ORM, no repository layer.
        │
        ▼
Postgres (db/migrations/*.sql)
```

`src/jobs/*.job.ts` sits beside the HTTP layer, not below it: a job is a
thin, named wrapper around one (or a short chain of) service functions,
called with a `system`-actor `Ctx` (`src/http/deps.ts#systemCtx`) instead
of a request-scoped one. Jobs never reimplement domain logic — if you find
yourself writing SQL directly in a `*.job.ts` file, that logic almost
certainly belongs in the service it's wrapping instead.

`src/domain/` holds pure, side-effect-free logic and shared types: entity
shapes (`types.ts`), the typed-question-bank scoring/selection engine
(`questions/`), unit conversion and branded value types (`units/`), and the
static-copy localization catalogue (`i18n/`). Nothing under `src/domain/`
imports from `src/services/` or touches `Ctx`/the database — that's what
makes it safe for `src/services/**` to depend on freely in one direction.

## The service dependency graph

`INTERFACES.md` is the frozen record of the graph as originally designed,
for the ~24 files five parallel agents built against — deliberately
acyclic, with an explicit "may call" list per module and the rule that an
edge not on that list needs discussion, not a silent addition. The
codebase has grown to 60+ files under `src/services/` since (a whole
`notifications/` delivery subsystem, `stats`/`timeline`/`matches`
read-model services, `venueSettlement`/`disputeResolution` for gaps the
spec left open, `retention`, `photoAltText`, `postDateFeedback`), but the
discipline — no cycles, a new cross-module call is a deliberate decision —
is still the working rule, and every new file added since has kept it.

```
discovery      ──▶ filter, compatibility, trust, moderation, photoExperiment
interest       ──▶ conversation, notification, photoExperiment, discovery
message        ──▶ textscan, trust, conversation, notification
dateProposal   ──▶ venue, payment, voucher, conversation, notification, trust
redemption     ──▶ voucher, dateProposal, conversation, trust
moderation     ──▶ report, trust, notification
appeal         ──▶ moderation, trust
payment        ──▶ ledger
question       ──▶ compatibility
behavioralPrompt ─▶ question
photoExperiment ─▶ photo
profile        ──▶ discovery
report         ──▶ moderation
```

Leaves (safe for anything to depend on, nothing to worry about cycling
back): `notification`, `textscan`, `ledger`, `filter`, `compatibility`,
`conversation`, `venue`, `voucher`. `trust` is a near-leaf (only calls
`notification`).

**Two enforced asymmetries worth knowing before you add a call:**

- **`redemption.service.ts`, not `voucher.service.ts` or
  `dateProposal.service.ts`, owns "scan ticket → complete date."**
  `voucher.markRedeemed` and `dateProposal.markCompletedByRedemption` are
  narrow, single-purpose functions `redemption.redeemByStaff`/`redeemBySelf`
  call in sequence inside one transaction, alongside
  `conversation.establishConversation` and two `trust.recordTrustEvent`
  calls. `voucher.service.ts` and `dateProposal.service.ts` never call each
  other directly — that's what keeps the graph above acyclic. If you're
  tempted to have one call the other directly, put the new logic in
  `redemption.service.ts` instead.
- **Actor-scoped functions trust `ctx.actor`, never a parameter for "who's
  asking."** `redemption.redeemByStaff` reads `ctx.actor.venueId`
  (requires `ctx.actor.type === 'venue_staff'`) rather than taking a
  `venueId` argument — a parameter a caller could pass a venue they don't
  work for. Use `requireUserActor(ctx)` (`src/lib/ctx.ts`) as the standard
  guard at the top of a user-only function.

### Transactions compose through `Ctx`, not through service-to-service parameters

`src/db/tx.ts#withTransaction(fn)` hands `fn` a `DbClient` bound to one
Postgres transaction. A caller wraps it in `withDb(ctx, db)` and passes
*that* `Ctx` into every nested service call that must share the
transaction:

```ts
await withTransaction(async (db) => {
  const txCtx = withDb(ctx, db);
  // every call below shares one transaction
  await payment.captureHold(txCtx, holdId);
  await voucher.issueVoucher(txCtx, dateProposalId);
});
```

There is exactly one `withTransaction` at the top of an outer flow (voucher
redemption, date-proposal acceptance); every nested service call shares
that `db` via `withDb`. Don't open a second, nested transaction inside a
service a caller might already be calling from inside one of these.

## Invariants

Each of these is a bug if violated, not a design choice up for
interpretation in a PR review. For each: where it's enforced, and which
test would fail first if it broke.

| Invariant | Enforced in | Test that would catch a violation |
|---|---|---|
| **Hard filters are never overridden by scoring.** `filter.passesMutualFilters` is a hard gate `discovery.getDiscoveryGrid` runs before compatibility scoring; scoring only sorts the already-filtered set. | `src/services/discovery.service.ts` (calls `filter.service.ts#passesMutualFiltersForCandidates` before ranking), `src/services/eligibility.service.ts` | `tests/unit/discovery.test.ts` — *"a perfect compatibility score never overrides a failed hard filter, through the real batched pipeline"* |
| **No compatibility threshold hides a candidate.** Only filters, blocks, moderation visibility, and capacity limits (incoming-interest cap, active-conversation cap) remove a candidate from discovery — never a low score. | `discovery.service.ts#getDiscoveryGrid` | `tests/unit/discovery.test.ts` (sort/tie-break/threshold-never-hides cases) |
| **Nobody is charged unless both holds authorize.** `captureHold` is only called for either side after confirming both `payment_holds` rows reached `authorized`; `payment.service.ts` exposes no "capture both" convenience that could skip that check. | `dateProposal.service.ts#acceptDateProposal` (Step 3, both captures gated on both authorizations already having happened in Step 1/2) | `tests/unit/dateProposal.test.ts` (every §14.5 failure branch — proposer-fails, recipient-fails, capture-fails-proposer, capture-fails-recipient-after-proposer-captured — each asserting `payment_holds.status` *and* the ledger nets to zero) |
| **A ticket exists only after capture.** `voucher.issueVoucher` is called exactly once, immediately after both `captureHold` calls return `captured`, in the same logical flow as the `charged → ticketed` transition. | `dateProposal.service.ts#acceptDateProposal` | `tests/unit/dateProposal.test.ts` — the happy-path test asserts a voucher exists (`status: 'issued'`) once the proposal reaches `ticketed`; every §14.5 failure-branch test (proposer-authorize-fails, recipient-authorize-fails, either capture-fails) asserts the proposal lands on `payment_failed`, never `charged`/`ticketed` — since `issueVoucher` is only reachable from the code path past both captures, a proposal that never reaches `charged` cannot have called it |
| **A refund, not a release, undoes money that already moved.** A hold that never captured is *released* (voided); a hold whose money already moved is *refunded*. | `payment.service.ts#releaseHold` / `#refundHold`; the choice between them in `dateProposal.service.ts`'s failure branches | `tests/unit/dateProposal.test.ts` — *"capture fails for the recipient AFTER the proposer already captured"*, asserting the proposer's hold status is specifically `refunded`, not `released` |
| **The payment ledger is insert-only.** No update/delete function exists in `ledger.service.ts`; a correction is always a new, offsetting row. | `ledger.service.ts` (no mutator besides `recordEntry`) | `tests/unit/payment.test.ts` (checks the ledger row *count* and the processor's own `_debugGetIntent()` state agree at every step — a silent correction would desync these) |
| **Exact coordinates never reach anyone but the profile's own owner.** Discovery and any *other* user's profile view report only a shared, bucketed, per-viewer-pair-jittered approximate distance (`domain/units/distance.ts#approximateDistanceBetween`) — never raw `latitude`/`longitude`. The one deliberate exception is `GET /me/profile`: a user editing their own profile needs their own coordinates back (e.g. to re-render a map pin). | `discovery.service.ts`, `profile.service.ts#getPublicProfile` (its `PublicProfileView` structurally has no coordinate fields); `http/serializers/profile.ts#serializeMyProfile` is the one, explicitly-commented place exact coordinates are allowed onto the wire, and only for the profile's own owner | `tests/unit/distancePrivacy.test.ts` — runs an actual least-squares multilateration attack against the real function and asserts it fails by an order of magnitude worse than an unmitigated control |
| **A reporter's identity is never disclosed to the reported user.** No function in `report.service.ts`/`moderation.service.ts` returns a reporter id to anyone but an admin actor. | `report.service.ts` | `tests/unit/report.test.ts` — *"submitReport never exposes the reporter identity in a way reachable by the reported user"* |
| **No generated prose reaches a user.** Notifications are `templateKey` + structured `payload` only, drawn from a fixed registry (`NOTIFICATION_TEMPLATES`); text-pattern scanning is regex/keyword-only (`textscan.service.ts#PATTERN_GROUPS`); no spec-section citation or internal identifier leaks into a user-visible string. | `notification.service.ts#notify` (rejects an unregistered `templateKey` and a payload carrying a `body`/`text`/`message`/`html` key), `textscan.service.ts` (no model call anywhere in the file) | `tests/unit/notification.test.ts` (rejects a free-text-smuggling payload; every template key matches `^[a-z0-9_]+_v\d+$`), `tests/unit/copyGuard.test.ts` (a real lexical scan of every string literal under `src/services/**`/`src/http/**` for a `§` mark or a "spec" citation) |
| **Venue staff cannot see chats, emails, or payment details.** `redemption.redeemByStaff`'s result type (`RedeemResult`) is deliberately narrow — it never touches `messages`, `users.email`, or `payment_methods`/`payment_holds`. | `redemption.service.ts` | `tests/http/roles.test.ts` (RBAC assertions per actor type) |
| **Policy snapshots are immutable once captured.** `interest.sendInterest`/`dateProposal.proposeDate` each snapshot the relevant config keys once, into the row's own `policy_snapshot` jsonb column; every later expiry/refund calculation on that row reads `row.policySnapshot[...]`, never live config again. A `config.set` call must never change the behavior of an already-created row. | `config.service.ts` (the `scope: 'snapshot'` vs `scope: 'live'` distinction per key), every read of `policySnapshot` in `dateProposal.service.ts`/`interest.service.ts` | `tests/foundation.test.ts` (asserts a config change doesn't alter an existing snapshot) |
| **Zero human moderation.** Every `moderation.service.ts`/`appeal.service.ts` function resolves to an automated outcome — there is no "queue for human review" state. | `moderation.service.ts#applyThresholds`, `appeal.service.ts` | `tests/unit/moderation.test.ts`, `tests/unit/appeal.test.ts` |

## Extension points

### Add a question type

`src/domain/questions/typeHandlers.ts` is the one place a `QuestionType`'s
behavior is defined. `scoring.ts` and `selector.ts` call
`getTypeHandler(type)` and never hardcode a list of types — adding a fifth
type means adding one `QuestionTypeHandler` entry to `TYPE_HANDLERS`,
implementing four functions against the new type's own definition shape:

```ts
export interface QuestionTypeHandler {
  type: QuestionType;
  validateSelfValue(def, raw): ValidationResult;
  validatePreferenceValue(def, raw): ValidationResult;
  satisfaction(def, selfValue, preferenceValue): number; // 0..1, one direction
  isAcceptable(def, selfValue, preferenceValue): boolean; // zero-tolerance, for deal-breaker filters
}
```

Add the new `QuestionType` literal and its `QuestionTypeDefinition` shape
in `src/domain/questions/types.ts` first — the handler map's key type
comes from there. Then extend `tests/unit/questionScoring.test.ts` with the
new type's cases; that file already exercises every existing handler
through the same table-driven pattern.

### Add a notification event

1. Add the event to `NotificationEventType` (`src/domain/types.ts`).
2. Add exactly one entry to `NOTIFICATION_TEMPLATES`
   (`src/services/notification.service.ts`) — a static, versioned key
   (`snake_case_v1`), never a format string. `Record<NotificationEventType, string>`
   makes a missing entry a `tsc` error.
3. Call `notification.notify(ctx, { userId, eventType, channel, payload })`
   from wherever the event actually happens — `payload` may only carry
   structured data (ids, enums, numbers); `notify` rejects a payload
   carrying a `body`/`text`/`message`/`html`/`copy`/`content` key outright
   (see the "no generated prose" invariant above).
4. If this event should also go out over push/email/SMS (not just the
   in-app notification center), call
   `services/notifications/index.ts#enqueueNotification` too — that's the
   separate outbox-and-delivery-worker pipeline
   (`notificationDelivery.job.ts`), with its own preferences/quiet-hours/
   retry logic. `notify` alone only writes the in-app notification row.
5. Extend `tests/unit/notification.test.ts`'s registry-shape assertions
   (they iterate `NOTIFICATION_TEMPLATES`'s keys automatically, so a new
   entry is checked for free) and add a call-site test asserting the event
   fires when it should.

### Add a background job

Every job is a plain `(ctx: Ctx) => Promise<T>` function — no class, no
hidden state (`src/jobs/types.ts`). A job should be a thin wrapper around a
service function that already does the real work, never new domain logic
written directly in the job file:

```ts
// src/jobs/myNewSweep.job.ts
import type { Ctx } from '../lib/ctx.js';
import { runMyNewSweep } from '../services/mySweep.service.js';
import type { JobDefinition } from './types.js';

export async function runMyNewSweepJob(ctx: Ctx) {
  return runMyNewSweep(ctx);
}

export const myNewSweepJob: JobDefinition = {
  name: 'my_new_sweep',
  description: 'One line describing what it does and which spec section, if any.',
  intervalMs: 15 * 60 * 1000,
  run: runMyNewSweepJob,
};
```

Register it in `src/jobs/registry.ts`'s `ALL_JOBS` array (and the matching
named re-export). That's the only wiring needed — `JobScheduler#start`
picks up every entry in `ALL_JOBS` automatically, on its own
`setInterval`, wrapped in the advisory-lock skip-if-already-running guard,
and `jobs:run <name>`/`jobs:start` (the CLI) both resolve jobs from the
same registry. Make the underlying service function idempotent
(status-guarded `UPDATE`s, `WHERE status = 'x'`) — a skipped or
re-overlapping tick must be a safe no-op, not a double-application. Test it
by calling the job function directly against a `ManualClock`-driven `Ctx`
(see any file in `tests/jobs/`) — never by waiting on a real timer.

### Add a payment adapter

`src/services/payments/processor.port.ts#PaymentProcessor` is the
interface: `authorize`/`capture`/`cancel`/`refund`, each taking/returning a
small typed params/result pair. `stripe.processor.ts` is the reference
stub — every method's JSDoc is the exact contract ("real implementation:
`stripe.paymentIntents.create({...})`...") a real implementation must
satisfy, written specifically so implementing it is a matter of filling in
each method's body, not re-deriving the contract from the spec.

To wire in a *different* real processor (not Stripe): implement the port,
then extend `src/config/adapters.ts#selectPaymentProcessor`/`describePayments`
the same way the existing `stripe` branch works — add the new provider
name to `env.ts`'s `PAYMENT_PROCESSOR` enum, add a case to both the
`describe*`/`select*` switch statements (the `assertNever` default forces
you to handle it, it cannot silently fall through), and require whatever
secrets it needs in `describePayments`'s production branch. Never
construct a concrete adapter (`FakeProcessor`, `StripeProcessor`, or a new
one) anywhere outside `src/config/adapters.ts` and test harnesses —
everything else reaches it through `ctx.payments`.

Note the media-moderation port instead uses an open **registry**
(`registerMediaModerationProvider(name, factory)`) rather than a hardcoded
switch, specifically because no real adapter exists yet — a future adapter
module calls that registration function once at import time, and
`selectMediaModerationAdapter` picks it up by `MEDIA_MODERATION_PROVIDER`
with no change to `adapters.ts` itself. Either pattern (hardcoded switch
with `assertNever`, or open registry) is acceptable for a new capability;
match whichever one the capability already uses.
