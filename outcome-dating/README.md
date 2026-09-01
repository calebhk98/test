# Outcome-Aligned Dating App — Backend

A TypeScript/Fastify/Postgres backend for a dating app built around one idea:
**the product it sells is a completed real-world date, not attention inside
the app.** Matching is filter-then-sort, never swipe-then-addict. A match
does not end the funnel — it starts a structured date proposal that puts
real money in escrow on both sides, so a date happening (or not) has a
consequence for the app and for both users, not just a chat log. There is no
generative AI anywhere in the user-facing product: notification copy,
decline messages, and safety banners are static templates, and message
scanning is regex/keyword-based, not a model. The full product rationale is
in [`SPEC.md`](./SPEC.md); this document is about the system that implements it.

For a deeper, change-oriented companion to this document — the module
dependency graph, the invariants that must never be broken, and how to
extend the system — see [`docs/architecture.md`](./docs/architecture.md).

## Contents

- [Quickstart](#quickstart)
- [Architecture](#architecture)
- [Domain model and state machines](#domain-model-and-state-machines)
- [The money flow](#the-money-flow)
- [Configuration and feature flags](#configuration-and-feature-flags)
- [Background jobs](#background-jobs)
- [Testing](#testing)
- [Guide to `docs/`](#guide-to-docs)
- [Known limitations](#known-limitations)

## Quickstart

Every command below was run against this repository to confirm it works as
written (Node 22, Postgres 16 server binaries at `/usr/lib/postgresql/16/bin`,
root shell). If your environment doesn't have a system Postgres 16 install
in that location, adapt `scripts/pg-dev.sh` or point `DATABASE_URL` at your
own Postgres instance instead of using `pg:start`.

```bash
npm install

# 1. Start a local Postgres 16 cluster (idempotent; must run as root — it
#    chowns db/.pgdata to the `postgres` OS user and runs `su postgres`).
#    Creates the `outcome_dating` role and database on first run, listening
#    on 127.0.0.1:55433.
npm run pg:start

# 2. Copy the example env (defaults already match pg:start's port/db name).
cp .env.example .env

# 3. Apply every migration in db/migrations/, in filename order.
npm run migrate

# 4. Seed deterministic dev data: config defaults, feature flags, the
#    65-question typed question bank, 15 interest tags, 8 venues, 20 users
#    (all emailed @seed.outcome-dating.test, safe to bulk-delete later).
npm run seed

# 5. Run the API + background job scheduler.
npm run dev -- serve
```

`GET http://localhost:3000/healthz` returns `{"status":"ok"}` once it's up.
The full readiness report (which adapter is live for each external
integration) is logged at startup and also served at
`GET /admin/system-readiness` (admin-only).

Run the test suite:

```bash
npm test
```

**A gap you should know about before you rely on `package.json`'s scripts
literally:** `npm run dev` is defined as `tsx watch src/index.ts` with **no
subcommand** — `src/index.ts` is a CLI (`serve` / `migrate` / `seed` /
`jobs:run <name>` / `jobs:start`) that prints a usage message and exits when
called with no argument, so `npm run dev` alone starts nothing. Verified
directly: running it prints `Unknown command ""` and the CLI's own usage
text. Similarly, `npm start` (`node dist/index.js`) is broken as written —
`tsconfig.json`'s `rootDir` is `.` (it compiles `src/**` *and* `tests/**`),
so `npm run build`'s actual output entrypoint is `dist/src/index.js`, not
`dist/index.js`; running `npm start` fails with `MODULE_NOT_FOUND`. Use
`npm run dev -- serve` for local development (confirmed above — the `--`
forwards `serve` to `tsx watch`) or `node dist/src/index.js serve` after a
build, until someone fixes these two script entries.

### Other useful commands (all verified against this repo)

| Command | What it does |
|---|---|
| `npm run pg:stop` / `npm run pg:reset` | Stop the local cluster / wipe `.pgdata` and start fresh. |
| `npm run typecheck` | `tsc --noEmit`. Also runs automatically before `npm test` (`pretest`). |
| `npm run build` | Compiles to `dist/` (see the entrypoint-path caveat above). |
| `node --import tsx src/index.ts jobs:run <name>` | Runs one background job once and prints its result. Job names: see [Background jobs](#background-jobs). |
| `node --import tsx src/index.ts jobs:start` | Runs only the job scheduler, no HTTP server. |

## Architecture

```
HTTP request
   │
   ▼
src/http/routes/*.routes.ts     — Fastify handlers: parse/validate input,
   │                                call one service function, serialize
   │                                the result. No business logic here.
   ▼
src/services/*.service.ts       — business logic, one file per bounded
   │                                concern (auth, interest, dateProposal,
   │                                payment, trust, moderation, ...).
   │                                Every exported function's first
   │                                parameter is `Ctx`.
   ▼
src/db (via Ctx.db)             — parameterized SQL against Postgres.
                                    No ORM.
```

Background jobs (`src/jobs/*.job.ts`) call the same service functions the
HTTP routes call, with a `system`-actor `Ctx` instead of a request-scoped
one — there is no separate "job logic" layer, jobs are thin, named wrappers
around service functions (see [Background jobs](#background-jobs)).

### The `Ctx` pattern

Almost every service function takes one object, `Ctx` (`src/lib/ctx.ts`), as
its first argument:

```ts
export interface Ctx {
  db: DbClient;
  clock: Clock;
  config: ConfigService;
  flags: FlagsService;
  logger: Logger;
  actor: Actor;               // who is calling — user / venue_staff / admin / system
  payments: PaymentProcessor; // port
  media: ImageModerationPort; // port
}
```

Why one bundled object instead of each function taking its own subset of
parameters:

- **Composable transactions.** `withTransaction(db => fn(withDb(ctx, db)))`
  hands every nested service call the *same* Postgres transaction by
  swapping only `db` on an otherwise-identical `Ctx`. This is how e.g.
  "accept a date proposal" composes payment capture + voucher issuance +
  status transition in one atomic unit without each service knowing about
  the others' transaction handling.
- **`actor`, not a bare `userId`.** Several rules depend on *what kind* of
  caller this is, not just which id — venue staff cannot see chats or
  emails; only an `admin` actor can bypass a participant check when
  cancelling a date on a venue's behalf. `ctx.actor.type` is the guard,
  checked with `requireUserActor(ctx)` / `requireRole(...)` helpers, never
  inferred from a parameter a caller could spoof.
- **Fakes flow through `Ctx`, never a global.** `ctx.payments` and
  `ctx.media` are the two ports the spec calls out by name (§14 payment
  processor, §7.2 image moderation). No service file imports a concrete
  `StripeProcessor` or `FakeProcessor` directly — every call goes through
  `ctx.payments.authorize(...)` etc., so a test can substitute
  `FakeProcessor` per-call with zero module-level mocking, and production
  code can never accidentally end up wired to the wrong adapter for one
  call and the right one for another.

### Ports and adapters

Five external integrations are modeled as small `*.port.ts` interfaces,
each with a fake/stub implementation used everywhere outside production,
and a real adapter that exists but is **not implemented**:

| Capability | Port | Fake/stub (dev, test) | Real adapter | Real adapter status |
|---|---|---|---|---|
| Payments | `services/payments/processor.port.ts` | `fake.processor.ts` | `stripe.processor.ts` | Every method throws `NotImplementedError`; the `stripe` npm package isn't even a dependency. JSDoc on each method is the contract a real implementation must satisfy. |
| Photo/content moderation | `services/media/moderation.port.ts` | `stub.adapter.ts` (deterministic on URL substrings: `nsfw`, `weapon`, `illegal`, `noface`, ...) | *(none registered)* | No real implementation exists at all — see `src/config/adapters.ts`'s registry, which starts empty. |
| Push | `services/notifications/ports/push.port.ts` | `fake.push.ts` | `fcm.push.ts`, `apns.push.ts` | Stubs, `NotImplementedError`. |
| Email | `services/notifications/ports/email.port.ts` | `fake.email.ts` | `ses.email.ts` | Stub, `NotImplementedError`. |
| SMS | `services/notifications/ports/sms.port.ts` | `fake.sms.ts` | `twilio.sms.ts` | Stub, `NotImplementedError`. |

**A production startup guard makes this safe rather than silent.**
`src/config/adapters.ts#runProductionGuard`, called first thing in
`src/index.ts`'s `serve`/`jobs:start`, selects every adapter as an explicit
function of `NODE_ENV`: outside production the fake/stub is always used, no
configuration required or possible; in production, selecting a fake, an
unset provider, or a provider with missing secrets is a **hard startup
failure**, not a warning — see [Configuration](#configuration-and-feature-flags).

### The service layer's own internal boundary

`INTERFACES.md` (written before the first parallel build pass) is the
frozen contract for which service module may import functions from which
other one — deliberately acyclic, so e.g. `notification.service.ts` never
depends on anything and can be safely imported by everyone. The codebase
has grown well past that document's original ~24-file module list (there
are over 60 files under `src/services/` today: `stats`, `timeline`,
`matches`, `venueSettlement`, `disputeResolution`, `retention`,
`photoAltText`, `postDateFeedback`, an entire `notifications/` subsystem,
and the typed question bank under `src/domain/questions/`), but the
acyclic-dependency discipline it set is still the working rule — see
[`docs/architecture.md`](./docs/architecture.md) for the current, fuller
graph and the reasoning for each edge.

### Localization and accessibility

`src/domain/i18n/` provides a static translation catalogue (`en` base,
`es` as a worked second locale — no generative text, per the product's
no-LLM-copy rule), Accept-Language negotiation with a fallback chain, and
Intl-backed money/number/date formatting. `docs/localization.md` documents
this in depth. `src/services/photoAltText.service.ts` lets a user attach
alt text to their own photos; `docs/accessibility.md` documents what the
backend guarantees for a client versus what remains the client's job (most
of it — a backend can make accessibility *impossible* by shipping the wrong
data shape, but can't make a client accessible by itself).

## Domain model and state machines

The core loop (SPEC.md §2): **account → questions/filters → discovery grid
→ limited interests → mutual match → chat → date proposal → both payment
holds authorized → both captured → ticket issued → venue redemption or
mutual attendance confirmation → completed → established chat.**

### Interest — `src/services/interest.service.ts`

An interest is a request to start a chat (not a date, no payment). States:
`pending → accepted | declined | expired | canceled`. All are terminal
except `pending`.

- `pending → accepted`: recipient accepts → `conversation.getOrCreateConversation`
  runs in the same transaction, conversation becomes `active`.
- `pending → declined` / `pending → canceled` (by sender) / `pending → expired`
  (past `policySnapshot['interest.expiry_hours']`, default 48h, swept by
  `interest_expiry` job): all release the sender's outgoing-interest slot.
- Any transition out of a non-`pending` state is rejected with a typed
  `ConflictError`, never a silent no-op.

### Conversation — `src/services/conversation.service.ts`

States: `active → cooling → archived`, or `active → established` (once a
date completes; established conversations never decay). Cooling/archival
thresholds (72h no-proposal → prompt, 14 days → cooling, 21 days →
archive) come from the `chat.*` config keys and are enforced by the
`chat_decay` job. A fresh mutual interest between the same two users can
reactivate an `archived` conversation back to `active`.

### Date proposal — `src/services/dateProposal.service.ts`

The richest state machine, 14 states:

```
draft → pending_acceptance → accepted → charged → ticketed
                                                      ├─→ completed (venue redemption)
                                                      ├─→ completed_unverified (both users self-confirm attendance)
                                                      ├─→ no_show (neither confirms in the window)
                                                      └─→ disputed (exactly one confirms) → resolved automatically

pending_acceptance → declined | expired | canceled | payment_failed
accepted            → canceled | refunded | payment_failed
charged/ticketed     → canceled | refunded  (cancellation after acceptance)
```

- **`proposeDate`**: creates the row as `draft`, authorizes the proposer's
  hold, moves to `pending_acceptance` on success or `payment_failed` on
  failure. A policy snapshot (escrow amount, accept-expiry hours,
  refund-cutoff hours, late-cancel percent, no-show percent, no-scan
  confirmation hours) is captured once here and never re-read from live
  config for this row again.
- **`acceptDateProposal`**: see [The money flow](#the-money-flow) — this is
  where both holds get captured and the voucher gets issued, all inside one
  advisory-locked, idempotent function.
- **`declineDateProposal`**: releases the proposer's hold (if still
  authorized), `→ declined`.
- **`cancelDateProposal`**: either participant (or an admin, on a venue's
  behalf) may cancel. Before acceptance: release the proposer's hold,
  `→ canceled`. After acceptance: if `hoursUntilDate >= full_refund_cutoff_hours`,
  refund both captured holds in full and the voucher is cancelled,
  `→ refunded`; inside the cutoff, refund only
  `late_cancel_refund_percent` (default 0%) and `→ canceled`.
- **`confirmAttendance`** (no-scan fallback, spec §15.4): each participant
  can self-confirm after `scheduledEnd`. Both within the window →
  `completed_unverified` (conversation established, **venue payment is not
  auto-settled**); only one confirms by the time the window sweeps → 
  `disputed`, later auto-resolved by the `dispute_auto_resolution` job.
- **`markCompletedByRedemption`**: called by `redemption.service.ts` inside
  the same transaction as the voucher's `markRedeemed`, not by
  `dateProposal.service.ts` itself — see
  [`docs/architecture.md`](./docs/architecture.md) for why the two files
  never call each other directly.

### Payment hold — `src/services/payment.service.ts`

States: `pending → authorized → capture_pending → captured → refunded`, or
`authorized → released`, or `pending/authorized → failed`. One row per
`(dateProposal, user)`. `authorizeHold`/`captureHold`/`releaseHold`/
`refundHold` are the only mutators; every one records a
`payment_ledger` entry via `ledger.service.ts`.

### Voucher — `src/services/voucher.service.ts`

States: `issued → redeemed`, or `issued → expired | canceled`. Issued only
by `dateProposal.acceptDateProposal` after both holds capture. The QR
payload is an HMAC-signed token (`src/lib/signing.ts`, keyed by
`VOUCHER_QR_SECRET` in production — a secret deliberately distinct from
`AUTH_TOKEN_SECRET`, see [Configuration](#configuration-and-feature-flags))
containing only the voucher id, venue id, date-proposal id, and expiry —
never payment or chat data.

### Moderation action — `src/services/moderation.service.ts`

`none → warning → restriction → shadowban → suspension`, escalation-only
via automated recalculation (`applyThresholds` never *lowers* the level; a
lower level only comes from a resolved appeal). A `minor_suspected` report
runs through a separate corroboration model
(`report.service.ts#assessMinorSuspected`) rather than the raw score
threshold — see `docs/risk-review.md` finding SAF-1 for why that model
exists and what it replaced.

## The money flow

This is the part most likely to be misunderstood by someone changing the
code, so it's worth stating precisely, with file references.

```
proposeDate(proposer)
  └─ payment.authorizeHold(proposer)         → payment_holds[proposer] = authorized
     (fails)  → date_proposals.status = payment_failed  (nothing else to undo)
     (ok)     → date_proposals.status = pending_acceptance

acceptDateProposal(recipient)
  ├─ payment.authorizeHold(recipient)        → payment_holds[recipient] = authorized
  │    (fails) → release proposer's hold (if authorized)
  │              date_proposals.status = payment_failed
  │
  ├─ date_proposals.status = accepted        (only once, on the pending_acceptance → accepted edge)
  │
  ├─ payment.captureHold(proposer)           → payment_holds[proposer] = captured
  │    (fails) → release recipient's hold (never captured, so release not refund)
  │              date_proposals.status = payment_failed
  │
  ├─ payment.captureHold(recipient)          → payment_holds[recipient] = captured
  │    (fails) → REFUND proposer's hold (money already moved — undo with a
  │              refund, never a release; date_proposals.status = payment_failed
  │
  ├─ date_proposals.status = charged          (both captured)
  │
  └─ voucher.issueVoucher(dateProposalId)     ← only reachable after both captures
       └─ date_proposals.status = ticketed
```

Invariants this code enforces (see `docs/architecture.md` for where each is
tested):

- **Nobody is charged unless both holds authorize.** `captureHold` is only
  ever called for either side after both `payment_holds` rows reached
  `authorized`. There is no "capture both" convenience function that could
  skip that check.
- **A ticket exists only after capture.** `issueVoucher` is called exactly
  once, inside `acceptDateProposal`, immediately after both captures
  succeed, in the same logical flow as the `charged → ticketed` transition.
- **The distinction between "release" and "refund" is deliberate, not
  cosmetic.** A hold that never moved money is *released* (voided). A hold
  whose money already moved (captured) can only be undone with a *refund*.
  Getting this backwards would either fail to return money that was
  actually taken, or attempt to refund a hold nothing was ever captured
  from.
- **`acceptDateProposal` is advisory-locked and idempotent.** A retried or
  concurrently-racing call for the same `dateProposalId` either no-ops (if
  the flow already reached `charged`/`ticketed`) or is serialized by a
  Postgres advisory lock — it never double-captures.
- **The ledger (`payment_ledger`, `ledger.service.ts`) is insert-only.**
  There is no update/delete function; a correction is always a new,
  offsetting row. Every `authorize`/`capture`/`release`/`refund`/`dispute`/
  `chargeback` call writes one.
- **A Stripe webhook never changes `date_proposals.status`.**
  `payment.service.ts#handleProcessorWebhook` deliberately leaves proposal
  status alone on `dispute`/`dispute_closed` events — the ledger records
  the chargeback type, but nothing currently reads it back into trust
  scoring automatically (see [Known limitations](#known-limitations)).

Refunds on cancellation (`cancelDateProposal`) use the same "round down, in
the platform's favor" percentage rule (`percentOfCents`) in both
`dateProposal.service.ts` and `venueSettlement.service.ts`, so the two
halves of a payout always sum exactly to the gross captured amount.

## Configuration and feature flags

Two separate systems, deliberately:

- **`src/config/env.ts`** — deployment/infrastructure settings, read once
  from `process.env` at process start (`DATABASE_URL`, `HTTP_PORT`,
  `AUTH_TOKEN_SECRET`, which adapter to use for each external integration,
  etc.). See `.env.example` for the full list.
- **`src/config/config.service.ts`** — *business* variables (spec §21):
  interest/chat/date/moderation/trust thresholds, stored in the
  `config_entries` table, changeable by an admin at runtime with no
  redeploy. Every key is declared once in `ConfigKeyRegistry` with a Zod
  schema, a default, and a `scope`:
  - `scope: 'live'` — callers always read the current value (e.g.
    `chat.active_limit`).
  - `scope: 'snapshot'` — the value is captured once, at creation, into the
    object's own `policy_snapshot` jsonb column (interests, date
    proposals), and never re-read from live config again for that row.
    This is what makes "existing objects keep their original terms" (spec
    §21.3/§21.4) true with no extra bookkeeping — a config change never
    retroactively changes the rules of an already-made commitment.

Feature flags (`src/config/flags.service.ts`, spec §22) support a hard
on/off, a percentage rollout with **deterministic per-user bucketing**
(`sha256(flagKey:userId)`, so a user's bucket never flickers between
calls), and segment targeting.

### The production startup guard

`src/config/adapters.ts#runProductionGuard(env)` runs before anything else
in `serve`/`jobs:start`. Outside production it never throws (the fake/stub
adapter is always used automatically). In `NODE_ENV=production`, it builds
a full readiness report across every capability and — if any entry is not
`ok` — throws one aggregated `ProductionConfigError` naming *every* problem
found in a single pass (not just the first), before a DB pool, an HTTP
listener, or the job scheduler is created. It refuses to start on:

- `PAYMENT_PROCESSOR` not set to `stripe`, or set to `stripe` without
  `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET`.
- `MEDIA_MODERATION_PROVIDER` unset or `"stub"` — the stub adapter approves
  virtually any photo by URL heuristic and must never run in production.
  (No real provider is registered today, so production media moderation
  cannot currently start at all — see [Known limitations](#known-limitations).)
- `PUSH_PROVIDER`/`EMAIL_PROVIDER`/`SMS_PROVIDER` left at `fake`, or set to
  a real provider missing its required secrets.
- `AUTH_TOKEN_SECRET` still equal to the shipped dev default, or shorter
  than 32 characters.
- `VOUCHER_QR_SECRET` unset, too short, or identical to `AUTH_TOKEN_SECRET`
  (these must be independent keys — a leaked venue-facing QR secret must
  never be usable to mint auth tokens).
- `DATABASE_URL` still equal to the local dev default, invalid, or not a
  `postgres://`/`postgresql://` URL.

No check ever logs or throws a secret *value* — only booleans, lengths, and
provider names (`tests/unit/productionGuard.test.ts` asserts this
explicitly). The same report is servable live at
`GET /admin/system-readiness` (admin-only) so an operator can confirm
what's actually running without a redeploy or a log search.

## Background jobs

`src/jobs/scheduler.ts` runs every registered job (`src/jobs/registry.ts`)
on its own `setInterval`, each run wrapped in a Postgres advisory lock
(`pg_try_advisory_lock`, keyed by a hash of the job name) so a run that's
still in flight — or a second process running the same job — is skipped,
never queued or double-executed. Every job body is itself idempotent
(status-guarded `UPDATE`s), so a skipped tick just picks up whatever's due
on the next one. Run any job once by hand with
`node --import tsx src/index.ts jobs:run <name>`.

| Job | Interval | What it does |
|---|---:|---|
| `interest_expiry` | 5 min | Expires pending interests past `interest.expiry_hours`; frees the sender's outgoing slot. |
| `date_proposal_expiry` | 5 min | Expires pending date proposals past `date.accept_expiry_hours`; releases the proposer's hold. |
| `chat_decay` | 15 min | Runs the 72h-prompt / 14d-cooling / 21d-archive sweep; never touches `established` conversations. |
| `compatibility_score_refresh` | nightly | Full recompute of the `compatibility_scores` materialized pair table (the answer-change path also runs synchronously inside `putMyAnswers`). |
| `photo_ab_stats` | hourly | Aggregates impressions/accepted-interests per photo (users with ≥3 approved photos, flag-gated) into a significance-guarded recommendation. |
| `trust_score_recalculation` | 15 min | Recalculates trust for users with a queued major event (some triggers, like moderation actions, also recalculate synchronously). |
| `moderation_score_recalculation` | 15 min | Aggregates reports/automated flags, applies restriction/shadowban/suspension thresholds (escalation-only). |
| `voucher_expiry` | 15 min | Expires issued vouchers past their configured window. |
| `payment_reconciliation` | 30 min | Compares the ledger against the processor's own state; flags mismatches, **never auto-corrects**. |
| `venue_payout_settlement` | 30 min | Settles the venue's share for every completed, redeemed date proposal exactly once. |
| `dispute_auto_resolution` | 15 min | Resolves `disputed` date proposals past `date.dispute_auto_resolve_hours`. |
| `ticketed_completion_sweep` | 15 min | Moves a `ticketed` proposal past its no-scan confirmation window to `no_show` (zero confirmations) or `disputed` (exactly one). |
| `check_in_prompt_sweep` | 30 min | Prompts both participants of a date past `scheduledEnd` for a post-date check-in; reminds if unanswered. |
| `matching_signal_sweep` | 60 min | Generates a behavioral-question suggestion for a user with enough `happened_good` check-ins. |
| `notification_delivery` | 30 sec | Drains the notification outbox — preferences, quiet hours, retry/backoff, per-channel send. |
| `stats_aggregation` | 15 min | Rolls up platform/cohort/gauge stats so the stats pages never scan raw event history live. |
| `retention_sweep` | hourly | Runs every registered retention policy — see `docs/retention.md`. |

## Testing

```bash
npm test
```

runs `pretest` (`tsc --noEmit`, so a type error fails the run before any
test executes) and then `node --import tsx --test tests/**/*.test.ts`
against **a real, locally-migrated Postgres** — there is no mocked
database layer.

- **Database isolation.** Each test file that needs a database creates its
  own dedicated Postgres database (not just a schema), migrates it fresh,
  and drops it in an `after()` hook — e.g.
  `odate_agent_a_<suffix>_<random-run-id>`. The random per-process suffix
  exists specifically so two overlapping `npm test` invocations against the
  same shared Postgres cluster (this repo is routinely worked on by more
  than one agent at once) don't `DROP DATABASE` out from under each other.
  There are ~9 near-identical bootstrap helpers under `tests/unit/testCtx*.ts`,
  `tests/jobs/testHarness.ts`, and `tests/http/testServer.ts` — real
  duplication, tracked and deliberately not consolidated yet in
  `docs/duplication.md` (see that document for why).
- **The fake payment processor** (`src/services/payments/fake.processor.ts`)
  drives every payment-related test. Construct a fresh instance per test —
  it holds mutable in-memory state. Failure injection is by magic substring
  in the payment method token: a token containing `fail_authorize` makes
  `authorize()` fail; `fail_capture` makes `authorize()` succeed but
  `capture()` fail. This is how every §14.5 failure branch is driven
  without a test-only code path in the service itself.
- **The controllable clock** (`src/lib/time.ts#ManualClock`) is the only
  clock any service or job reads — no service calls `Date.now()`/`new
  Date()` directly. Tests construct one pinned to a fixed epoch and
  `advanceHours`/`advanceDays` it to drive expiry/decay boundaries. Every
  time-boundary case in the suite is tested as a pair: one assertion just
  before the cutoff, one exactly at it — the off-by-one at the boundary is
  where these bugs actually live.
- **Perf suites cost real time and rows.** `tests/perf/discovery.perf.test.ts`
  and `tests/perf/compatRefresh.perf.test.ts` match `npm test`'s own glob
  (they end in `.test.ts`), so a full `npm test` run seeds **~24,000** and
  **~20,000** synthetic users respectively (six cities, bulk `unnest`
  inserts, not one-row-at-a-time) to prove the discovery grid and
  compatibility refresh don't regress to their old O(platform) query
  patterns. Shrink them for a quick local run with
  `DISCOVERY_PERF_USER_COUNT=500 COMPAT_PERF_USER_COUNT=500 npm test`, or
  run a narrower slice directly, e.g.
  `node --import tsx --test tests/unit/*.test.ts` to skip perf/http/jobs/concurrency
  entirely.
- **Directories:** `tests/unit/` (the large majority — pure functions and
  single-service-plus-DB tests), `tests/http/` (routes through a real
  Fastify instance via `app.inject`, no real socket), `tests/jobs/` (each
  job function run directly against a `ManualClock`), `tests/concurrency/`
  (true `Promise.all`-driven races — interest accept/decline, date-proposal
  accept, voucher redemption — not just sequential "race"-named tests),
  `tests/perf/` (the two suites above), plus `tests/foundation.test.ts` (a
  standalone smoke test: migrations apply cleanly and idempotently, every
  §21.4 config default seeds correctly, policy snapshots are genuinely
  immutable, flag bucketing is deterministic).

`docs/test-strategy.md` describes the *intended* test pyramid and isolation
strategy in more depth (written early, before the file layout above
settled — read it for the reasoning, not as a literal map of `tests/`).
`docs/test-audit.md` is a line-by-line audit of the suite as it stood at
one point, with concrete findings — several (the `npm test` glob silently
skipping `tests/foundation.test.ts`; a flagship file's stale
`mock.module()` fakes; no `pretest` typecheck) were already fixed by the
time this document was written: `package.json`'s `test` script now uses
`bash -c 'shopt -s globstar; ...'` so `tests/foundation.test.ts` runs, and
`pretest` now runs `typecheck`. Treat that audit as a still-useful method
and a partially-historical result, not a live defect list — see
[Guide to docs/](#guide-to-docs).

## Guide to `docs/`

| Document | What it's for | Read it if you're |
|---|---|---|
| [`SPEC.md`](./SPEC.md) | The original product specification (34 sections) — the ground truth for *why* a rule exists. | Anyone deciding whether a change matches product intent. |
| [`INTERFACES.md`](./INTERFACES.md) | The frozen module-boundary contract from the first parallel build pass (`Ctx`, the "may call" graph, the money/ticket invariants). Predates ~40 files added since. | Anyone about to add a new service module or cross-service call. |
| [`docs/conformance.md`](./docs/conformance.md) | A ~280-row, spec-section-by-spec-section obligation checklist (`C-<section>.<n>` IDs) with the exact oracle each row should be tested against. | Writing a new test and want to know what "done" looks like; checking whether a spec rule has a test at all. |
| [`docs/test-strategy.md`](./docs/test-strategy.md) | How the suite is organized, the fake processor's failure-injection contract, the controllable-clock discipline, what's downgraded to a port-contract test instead of a real integration test. | Writing new tests. |
| [`docs/test-audit.md`](./docs/test-audit.md) | A line-by-line read of ~two-thirds of the suite by count, with concrete findings ranked by severity (some already fixed — see [Testing](#testing)) and a per-file verdict table. | Deciding where the suite is weakest before you build on it. |
| [`docs/risk-review.md`](./docs/risk-review.md) | An adversarial safety/legal/product review, 48 findings (11 critical), cross-checked against actual code, not just the spec. Several have since been fixed in code — this document is being kept as the record of the review process, and as the checklist for what to re-verify. | Anyone touching moderation, trust, safety, payments, or privacy; anyone doing legal/compliance review before a real-money launch. |
| [`docs/review-open.md`](./docs/review-open.md) | An independent, spec-only (not code-grounded) review — money-in-dispute vagueness, the zero-human-moderation bet, the "algorithm never hides" claim's tension with capacity-based invisibility. | Product/strategy discussion about the spec itself, separate from implementation quality. |
| [`docs/duplication.md`](./docs/duplication.md) | An audit of duplicated/divergent logic — already-divergent bugs (ranked), at-risk duplication, and a large cosmetic-repetition section explicitly marked safe to defer. | Before touching trust-score exposure, cursor pagination, distance calculation, or the two compatibility-scoring code paths. |
| [`docs/scale-and-sources.md`](./docs/scale-and-sources.md) | Three questions answered against the code, not the spec: can it scale, is demo data swappable for real data, is there one source of truth per concept. Some of Part 1's discovery-scan findings and Part 3's question-bank-duplication finding have since been fixed in code (verify against `src/services/discovery.service.ts` and `db/migrations/022_drop_old_question_bank.sql` before assuming either is still open). | Capacity planning; launch-readiness review; understanding what's stub vs. real. |
| [`docs/retention.md`](./docs/retention.md) | The privacy-review-facing data-retention table: every accumulating data class, its window, delete-vs-anonymize, and why. Implemented by `src/services/retention.service.ts`, run by the `retention_sweep` job. | Privacy/legal review; anyone adding a new table that will grow unboundedly. |
| [`docs/accessibility.md`](./docs/accessibility.md) | What the backend guarantees for an accessible client (alt text, non-color-only status) versus what's entirely the client's job. | Building or reviewing a client against this API. |
| [`docs/localization.md`](./docs/localization.md) | The `src/domain/i18n/` architecture — static catalogue, fallback chain, Intl-backed formatting — and how the no-generative-copy rule is kept. | Adding a locale or a user-facing string. |
| [`docs/ux-api-review.md`](./docs/ux-api-review.md) | Whether a good mobile client can actually be built on the current route surface — wiring gaps (built-but-unrouted services), N+1s in list responses. Several items (notification/device routes, `/me/photos`) have since been wired — check `src/http/routeTable.ts` before assuming a gap is still open. | Building a client; deciding what to route next. |
| [`docs/ux-product-review.md`](./docs/ux-product-review.md) | A product walkthrough of the app as a first-time user would experience it. **Its own headline finding — two parallel question systems, with the better one unreachable — has since been resolved**: the old `questions`/`answers` bank was fully cut over and dropped (`db/migrations/019_question_cutover.sql`, `022_drop_old_question_bank.sql`); `GET /questions`/`PUT /me/answers` now serve the typed bank. Read the rest of the document for still-relevant product observations, but not that framing. | Product review of the actual user experience. |

## Known limitations

Things verified directly against the current code (not just inherited from
a review document) that a team should know before treating this as launch-ready:

- **No real payment processor.** `StripeProcessor` throws
  `NotImplementedError` on every method; the `stripe` package isn't a
  dependency. The production guard refuses to boot with anything else, so
  this cannot silently ship — but real payments require writing this
  adapter from scratch against its own documented JSDoc contract.
- **No real photo/content moderation.** `StubMediaModerationAdapter`
  approves any photo whose URL doesn't contain one of a handful of magic
  substrings — i.e. it approves virtually everything, including real
  nudity/weapons/illegal imagery a real user might upload. No real
  `ImageModerationPort` implementation exists, and the registry a real one
  would plug into (`src/config/adapters.ts`) is empty. The production
  guard refuses to boot without one.
- **No real push, email, or SMS provider.** `FcmPushSender`, `ApnsPushSender`,
  `SesEmailSender`, and `TwilioSmsSender` are all documented stubs
  (`NotImplementedError`). The delivery pipeline itself (outbox, retry/backoff,
  quiet hours, preferences) is fully built and tested against the fakes.
- **Two `package.json` scripts are broken as written**: `npm run dev`
  (missing the `serve` subcommand) and `npm start` (wrong compiled entry
  path). See [Quickstart](#quickstart) for the working equivalents.
- **The scaling ceiling is real but partially already addressed.**
  `docs/scale-and-sources.md` found the discovery grid and reality
  dashboard scanning every active user platform-wide with no geographic
  bound — that specific defect has since been fixed
  (`discovery.service.ts` now geo-bounds and batches its candidate-pool
  query, proven at ~24,000 seeded users by `tests/perf/discovery.perf.test.ts`).
  What has **not** been re-verified against current code: the O(n²)
  pairwise `compatibility_scores` materialization (storage estimated at
  ~1.75TB at 100,000 users), the single-Postgres-instance ceiling, and the
  in-process (non-shared) rate limiter and job scheduler, which break
  correctness the moment the app tier is scaled to more than one instance.
  Read `docs/scale-and-sources.md` Part 1 for the full reasoning before
  planning capacity.
- **Legal/safety findings in `docs/risk-review.md`: some fixed, most not
  re-verified in this pass.** Confirmed fixed in current code: the SAF-1
  single-report instant-suspension gap (a corroboration model now gates
  it), the SAF-2 inconsistent/unjittered distance calculation (both
  discovery and profile now share one bucketed-and-jittered function), the
  PRIV-1 account-deletion gap (deletion now clears sensitive answers,
  tags, and other previously-untouched tables), and the trust-score
  exposure double-gate (`docs/duplication.md` finding 1). **Not
  re-verified**, and should be treated as still open until checked: the
  money-transmission licensing question for the venue-payout split
  (PAY-1), age assurance beyond a self-declared birthdate (PAY-2), the
  zero-human-moderation architecture's tension with automated-decision-review
  regulations in some jurisdictions (MOD-5/6), and most of the remaining
  ~40 findings in that document. Do not treat "not mentioned here" as
  "fixed" — it means "not re-checked for this pass."
- **The compatibility-scoring duplication `docs/duplication.md` flagged is
  resolved.** There is now exactly one scoring path
  (`compatibility.service.ts`, reading `question_bank`/
  `user_question_answers` directly), confirmed by reading the current file
  and by the successful `022_drop_old_question_bank.sql` migration having
  already run.
