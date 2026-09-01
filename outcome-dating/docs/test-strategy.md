# Test Strategy — Outcome-Aligned Dating App

Companion to `docs/conformance.md` (the full obligation checklist). This document says
*how* the suite is organized and *how* to get a deterministic oracle for each row, using
only what's already in the repo: `node:test`, `pg`, `FakeProcessor`, `StubMediaModerationAdapter`,
and `ManualClock`. No `fast-check`, no mocking framework, no Docker.

## 1. Test pyramid

```
        ▲  a few          end-to-end (2.1)          register → ... → established chat,
        │                                            drives the real HTTP layer (fastify)
        │  more            integration                one service fn (or a short chain,
        │                  (majority of the suite)     e.g. accept → capture → ticket)
        │                                              against a real, isolated Postgres
        │  most            unit / property             pure functions: compatibility.service,
        ▼                                              flags.service.bucketFor, refund math,
                                                        trust-level mapping, config registry
```

- **Unit** (`tests/unit/**`): pure functions with no `Ctx`, no DB. Compatibility formula
  (§16.2), refund arithmetic (§14.7), trust-level banding (§6.1), report-score threshold
  mapping (§18.5), feature-flag bucketing (§22), token TTL math (§28.2), reversed-polarity
  transform. These are the fastest and most numerous — every worked example in
  `conformance.md` §16.2/§6.1/§14.7/§18.5/§21.4 has a 1:1 unit test pinning the exact
  number computed there.
- **Integration** (`tests/integration/**`): one service function (`interest.service.ts`,
  `dateProposal` flow across `payment.service.ts`/`ledger.service.ts`, `conversation.service.ts`
  decay, moderation scoring, config service caching) exercised against a real, migrated,
  test-only Postgres database, with `FakeProcessor` + `StubMediaModerationAdapter` +
  `ManualClock` injected via `Ctx`. This is where state-machine legal/illegal transitions,
  DB constraint negative tests, and multi-row atomicity (interest-accept → conversation
  creation, capture → ticket issuance) live. This tier is the bulk of the suite because
  most of `conformance.md`'s rows are integration-shaped (they require a DB transaction
  and/or a port).
- **State-machine** tests are integration tests organized as one file per machine
  (`tests/integration/stateMachines/interest.test.ts`, `dateProposal.test.ts`,
  `paymentHold.test.ts`, `voucher.test.ts`, `conversation.test.ts`, `moderationAction.test.ts`),
  each driving EVERY legal transition row and EVERY illegal transition row from the
  corresponding table in `conformance.md`, asserting the illegal ones throw a typed
  `AppError` (`ConflictError`/`ValidationError`, per `src/lib/errors.ts`) rather than
  silently succeeding or crashing with an unhandled exception.
- **Negative** tests are not a separate directory — they're the "MUST NOT" rows,
  interleaved into the unit/integration files for the feature they guard, since they need
  the exact same fixtures as the positive case right next to them (e.g. C-9.1.2 "no hard
  filter override" lives in the same file as C-9.1.1).
- **End-to-end** (`tests/e2e/**`, one or two files): C-2.1's full loop, plus maybe one
  "everything fails gracefully" run (§30 edge cases chained). Kept deliberately small —
  this tier is expensive (many DB round-trips, real HTTP layer) and its job is to catch
  wiring/integration mistakes between services, not to re-prove business rules already
  covered at the unit/integration tier.
- **Fixture-data** tests (schema/enum shape assertions) are cheap `node:test` cases with
  no DB — they typecheck a `CHECK (...)` constraint list against the corresponding
  TypeScript union type by literally listing both and asserting set-equality. These catch
  the specific class of bug where `domain/types.ts` and `db/migrations/001_init.sql`
  silently drift apart.

## 2. The fake payment processor

`src/services/payments/fake.processor.ts` is the payment tier's test double for every
integration test. Two rules matter:

1. **One `FakeProcessor` instance per test.** It holds mutable in-memory state (`intents`
   Map, `idempotency` Map) — construct a fresh instance per `test()` (or per test file's
   `beforeEach`), never share one across tests or the tests will observe each other's
   intents/idempotency keys. This is the payment-tier equivalent of DB isolation (§4
   below) and is *cheaper*, so prefer a fresh instance liberally.
2. **Failure injection is via magic substrings in the payment method token**, not
   mocking: a token containing `"fail_authorize"` makes `authorize()` return
   `status:'failed'`; a token containing `"fail_capture"` makes `authorize()` succeed but
   `capture()` fail. This is how every §14.5 failure-case row and the CC-2 fault-injection
   matrix in `conformance.md` are driven — e.g. to test "recipient authorization fails,
   proposer hold is released" (C-14.5.2), create the recipient's `payment_methods` row
   with token `pm_fail_authorize_<uuid>` and drive the normal accept flow; no special
   test-only branch in the service code is needed.
3. **Idempotency-key reuse is exercised deliberately**, not just as an accident of
   retries: call the same service operation twice with the same underlying
   `idempotencyKey` derivation (`hold:{dateProposalId}:{userId}` per the port's doc
   comment) and assert `FakeProcessor.memoize` returns the SAME result both times — this
   is the regression test for "a retried capture never double-charges."
4. Use `_debugGetIntent(processorIntentId)` as a second, independent oracle alongside the
   DB's `payment_holds`/`payment_ledger` rows — many CC-2/CC-4 assertions are strongest
   when they check BOTH ("the processor's own state" and "our ledger") agree, which is
   exactly what `payment.service.ts`'s reconciliation job (§25.9, C-25.9.1) does in
   production and what its test should do too.

When `PAYMENT_PROCESSOR=stripe` is configured, `stripe.processor.ts` implements the same
`PaymentProcessor` port against the real Stripe API — that adapter is explicitly **not**
exercised by this suite (see §6 below); only its port-contract shape is checked.

## 3. The controllable clock

`src/lib/time.ts`'s `ManualClock` is the only clock any service or background job may
read (cross-cutting invariant CC-12 in `conformance.md` — grep for stray `Date.now()`/
`new Date()` outside `src/lib/time.ts` as a lint-level regression check). Rules for using
it in tests:

- Construct one `ManualClock` per test (`new ManualClock(new Date('2026-01-01T00:00:00Z'))`
  or similar fixed epoch — never `new ManualClock()` defaulting to real "now," since that
  reintroduces non-determinism into boundary tests), thread it through `Ctx.clock`.
- Every time-boundary row in `conformance.md` (interest expiry at 48h, date-proposal
  accept-expiry at 48h, chat decay at 72h/14d/21d, refund cutoff at 24h, no-scan
  confirmation window at 72h, voucher expiry, age exactly 18) is tested as a PAIR: one
  assertion at `clock.advanceHours(X - epsilon)` (still in the "before" bucket) and one at
  `clock.advanceHours(X)` exactly (now in the "at/after" bucket) — see `hoursBetween` in
  `time.ts` for computing exact deltas. Never test only the "well past" case; the
  off-by-one at the exact boundary is where these bugs actually live.
- Background jobs (§25) are plain functions that take `Ctx` (with its `ManualClock`) as an
  argument — call the job function directly in the test rather than waiting on a real
  scheduler/cron. Advance the clock, call the job, assert the resulting state change,
  repeat. This is how e.g. the three-stage chat decay (72h prompt → 14d cooling → 21d
  archive) is tested as one continuous timeline in a single test rather than three
  disconnected ones — the same `ManualClock` instance is advanced in stages and the job is
  invoked after each stage.
- Age (§5.1, C-5.1.6) is the one boundary that is NOT driven by `ManualClock` but by
  comparing a fixed `birthdate` against `clock.now()` — same pairing discipline applies
  (birthdate exactly 18 years before the clock's "now" vs. one day short).

## 4. Database isolation per test

There is one Postgres 16 instance for the whole project (`scripts/pg-dev.sh`, database
`outcome_dating`, port 55433 — see `.env`/`env.ts`). Tests must not share mutable state
through it. Two isolation strategies, matched to test weight:

- **Preferred, for most integration tests: one Postgres *schema* per test file, applied
  fresh from `db/migrations/001_init.sql`.** At the top of each integration test file's
  `before()` hook: `CREATE SCHEMA test_<random suffix>`, `SET search_path TO
  test_<suffix>`, replay the migration SQL against that schema, run every `test()` in the
  file against a `pg.Pool`/`pg.Client` pinned to that `search_path`, then `DROP SCHEMA ...
  CASCADE` in `after()`. This gives full test-file isolation (no cross-file interference,
  no truncate/reset bookkeeping) while still exercising the REAL constraint set (all the
  `CHECK`/`UNIQUE` rows in `conformance.md` §23 need the real schema, not a mock).
- **Within one file, wrap each `test()` in `withTransaction` and roll back instead of
  committing** (`BEGIN` at test start, `ROLLBACK` — never `COMMIT` — at test end,
  regardless of pass/fail) wherever the test doesn't itself need to assert
  cross-transaction behavior (e.g. testing that a background job run in a SEPARATE
  transaction sees committed data — those specific tests fall back to real commits +
  explicit cleanup). This is fast (no schema-per-test overhead) and gives per-`test()`
  isolation inside a shared per-file schema.
- **Never** run the suite against the same schema/rows two test files touch concurrently
  without one of the two isolation layers above — `node --test` parallelizes test FILES by
  default, so two files sharing unscoped table rows is the single most likely source of
  flaky, hard-to-reproduce integration-test failures in this project.
- Seed data (`ConfigService.seedDefaults()`, `FlagsService.seedKnownFlags()`, base
  `questions`/`venues`/`interest_tags` fixture rows) is (re-)inserted per schema in the
  same `before()` hook, so every test starts from a known-good, spec-default config state
  — this is what makes the `conformance.md` §21.4 default-value assertions meaningful
  (they're checking the SEEDED default, not a value some earlier test happened to leave
  behind).

## 5. What "property test" means here (no fast-check)

The project has no property-based-testing library. "Property test" in `conformance.md`
means: **a hand-rolled loop over a small, deliberately-varied fixture table (5–20 cases),
each checked against the SAME general assertion**, rather than a single hard-coded
example. Two concrete patterns, both plain `node:test`:

1. **Table-driven property.** Build an array of fixture objects covering the interesting
   corners of the input space by hand (boundaries, both-extremes, a "typical" middle
   case, an adversarial case) and `for (const fixture of fixtures) { ... assert ... }`
   inside one `test()`, OR emit one `test()` per fixture via `test(name, ...)` in a loop
   so failures report which specific case broke. Example (CC-1, "no hard-filter override"):
   generate ~10 candidate/filter combinations by hand — some passing every filter, some
   failing exactly one, some failing all, one with a `null`/"prefer not to say" answer
   colliding with a filter (OQ-2/C-8.5.5) — and assert the discovery result set intersected
   with "fails a filter" is empty for every one of the 10, not just one lucky case.
2. **Deterministic pseudo-random sweep.** Where the input space is genuinely large (e.g.
   CC-2's fault-injection matrix, or C-16.2.W7's "score always in [0,1]"), use a small
   **seeded** linear-congruential or `crypto.createHash`-derived generator (a few lines,
   no dependency) to generate N (e.g. 200) fixture inputs deterministically — same seed
   every run, so a failure is always reproducible by re-running the suite, unlike `Math.random()`.
   Assert the invariant holds for all N. This is the "property" tier's substitute for
   `fast-check`'s shrinking: it doesn't shrink automatically, but seeded determinism means
   `git bisect`/rerun reproduces any failure exactly, which is the property that matters
   most for this test suite's size.
3. Fault-injection matrices (CC-2's 16-combination table) are enumerated EXPLICITLY (they're
   small and finite, 2⁴), not generated — exhaustive enumeration beats random sampling
   whenever the space is small enough to write out, which every state-machine's legal ×
   illegal transition table in `conformance.md` already does.

## 6. What is NOT automatically testable — port-contract tests instead

Some `conformance.md` rows name a REAL external capability (a real ML model, a real
payment network) that this test suite cannot and should not call. For each, the
obligation is downgraded to a **port-contract test**: assert the TypeScript interface
(the port) has the right shape and the STUB adapter behind it implements it deterministically
and per its documented contract — never assert anything about real-world model accuracy.

| Not testable here | Why | What we test instead |
|---|---|---|
| Real CV nudity/weapons/illegal-content detection, real face detection, real perceptual-hash duplicate matching | No ML model is vendored; `StubMediaModerationAdapter` is a URL-substring stand-in, not a classifier | **Port-contract test** on `ImageModerationPort`: `StubMediaModerationAdapter.analyzePhoto` returns the documented deterministic result for each documented trigger substring (`noface`, `nsfw`, `weapon`, `illegal`, `blurry`, `group`, `dup:<n>`) — this is C-7.2.2–C-7.2.4 exactly as written. A REAL adapter (Rekognition/Vision API) gets its own separate, real-model-accuracy evaluation OUTSIDE this repo's `node:test` suite (that's an ML-eval problem, not a unit/integration-test problem) — this suite only guarantees "whatever the port returns, the rest of the pipeline (rejection, discovery-eligibility, flagging) reacts correctly," which is `photo.service.ts`'s job, fully testable against the stub. |
| Real Stripe authorization/capture/webhooks | No live Stripe account/network access in CI; hitting real Stripe would be slow, flaky, cost money, and non-deterministic | **Port-contract test**: `stripe.processor.ts` and `fake.processor.ts` are asserted to implement the exact same `PaymentProcessor` interface (TypeScript already enforces this at compile time — `tsc --noEmit` is itself a contract test); a SHARED contract-test suite (`tests/contract/paymentProcessor.contract.test.ts`) runs the SAME behavioral assertions (authorize→capture ordering, idempotency-key reuse, cancel-releases, refund-caps-at-captured-amount) against `FakeProcessor` only, written generically enough that swapping in a real Stripe test-mode key later would need zero test-code changes — only a `PAYMENT_PROCESSOR=stripe` env flip. All of §14's business-logic rows in `conformance.md` (C-14.2.*–C-14.7.*) are proven against `FakeProcessor`; a real Stripe integration is a manual/staging verification step, not part of this suite. |
| Real device fingerprinting / IP reputation / VPN detection accuracy (§19.2) | Same class as CV — these are real external signal providers, not deterministic pure logic | Port-contract test on however `device_fingerprints`/IP-reputation is wired: the SIGNAL is treated as an opaque input (`reputation_score: 0-100`) to the trust/moderation pipeline; tests fix the input and assert the pipeline reacts correctly (feeds C-6.2.2, C-18.2.1), never assert real detection accuracy. |
| Real push/email delivery (§20.2) | No real APNs/FCM/SMTP in test | Notification tests assert a `Notification` row is QUEUED with the right `templateKey`/`payload`/`channel` (C-20.1.1) — actual delivery is a separate infra concern (retries, provider webhooks) outside this repo's scope. |
| TLS in transit, encryption at rest (§28.3) | Infrastructure/deployment-layer, not application code | Not tested by `node:test` at all — flagged explicitly in `conformance.md` (C-28.3.1/2) as a configuration-review item (reverse proxy TLS config, managed-Postgres encryption-at-rest setting), never an automated test gap to "fix" in this repo. |
| Cookie/tracking disclosure UI copy, privacy-policy acceptance UX (§29.5) | Client/legal-copy concern | Only the backend's `termsAccepted`-shaped required-field check (C-5.1.4/C-29.6) is tested here; the disclosure UI itself is out of this backend suite's scope. |

## 7. File layout

```
tests/
  unit/
    compatibility.test.ts        # §16.2 worked examples + property sweep
    trustLevel.test.ts           # §6.1 boundary table
    refund.test.ts               # §14.7 worked examples incl. rounding (OQ-6)
    reportScoring.test.ts        # §18.5 threshold table
    flags.test.ts                # §22, incl. bucketFor determinism (C-22.8)
    config.test.ts               # §21.2 cache/version/invalidate (no DB — mock DbClient)
  integration/
    stateMachines/
      interest.test.ts           # C-11.4.SM.*
      dateProposal.test.ts       # date-proposal SM + §14 flow + CC-2 fault matrix
      paymentHold.test.ts        # §23.18 hold SM
      voucher.test.ts            # C-15.SM.*
      conversation.test.ts       # §12.6/12.7 decay + established (CC-6)
      moderationAction.test.ts   # §18.4 + report-scoring integration (C-18.5.W*)
    discovery.test.ts            # §9, §10, CC-1
    profile.test.ts              # §7, §8
    chat.test.ts                 # §12.2-12.5
    trust.test.ts                # §6.2, §6.3, §6.4
    admin.test.ts                # §27, RBAC (C-4.RBAC.*)
    privacy.test.ts              # §29
    edgeCases.test.ts            # §30
  contract/
    paymentProcessor.contract.test.ts   # §6 above, run against FakeProcessor
    imageModeration.contract.test.ts    # §6 above, run against StubMediaModerationAdapter
  e2e/
    fullLoop.test.ts             # C-2.1
  helpers/
    testDb.ts                    # per-file schema create/migrate/drop
    fixtures.ts                  # user/profile/question/venue builders
    seededRandom.ts              # small deterministic generator for §5 pattern 2
```

Every `conformance.md` ID should be traceable to exactly one `test()` name (or one row of
a table-driven `test()`) — the recommended convention is naming the `node:test` `test()`
string with the ID as a prefix, e.g. `test('C-14.5.3 capture fails after both
authorized — releases/refunds both, no voucher', async () => { ... })`, so
`grep -r "C-14.5.3" tests/` finds the implementation instantly and a future spec change's
blast radius is `grep`-able in one command.
