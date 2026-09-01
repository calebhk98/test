# Test strategy

Companion to `docs/conformance.md` (the full obligation checklist): how the suite gets a deterministic oracle for each row, using only what's in the repo (`node:test`, `pg`, `FakeProcessor`, `StubMediaModerationAdapter`, `ManualClock`). No `fast-check`, no mocking framework, no Docker. Written early, before the file layout below settled into its current shape; read it for the method, and see the actual `tests/` tree for the real map.

## The fake payment processor

`src/services/payments/fake.processor.ts` is the payment tier's test double for every test that needs one. Construct a fresh instance per test (it holds mutable in-memory state). Failure injection is by magic substring in the payment method token, not mocking: a token containing `fail_authorize` makes `authorize()` fail; `fail_capture` makes `authorize()` succeed but `capture()` fail. This drives every §14.5 failure branch without a test-only code path in the service itself. `_debugGetIntent()` is a second, independent oracle alongside the DB's own `payment_holds`/`payment_ledger` rows; the strongest assertions check that both agree, the same thing `payment.service.ts`'s reconciliation job does in production.

`stripe.processor.ts` implements the same `PaymentProcessor` port for real Stripe calls and is explicitly not exercised by this suite; only its port-contract shape is checked (TypeScript already enforces the interface match at compile time).

## The controllable clock

`src/lib/time.ts#ManualClock` is the only clock any service or job may read: no service calls `Date.now()`/`new Date()` directly. Construct one per test, pinned to a fixed epoch, never defaulting to real "now" (that reintroduces non-determinism into boundary tests). Every time-boundary case (interest expiry, chat decay's three stages, refund cutoff, no-scan confirmation window, age exactly 18) is tested as a pair: one assertion just before the cutoff, one exactly at it. The off-by-one at the boundary is where these bugs actually live. Background jobs are plain functions that take `Ctx`; call them directly in the test rather than waiting on a real scheduler.

## Database isolation per test

Each test file that needs a database creates its own dedicated Postgres database (not just a schema), migrates it fresh, and drops it in an `after()` hook, with a random per-process suffix in the name. That suffix exists specifically so two overlapping `npm test` runs against the same shared cluster (this repo is routinely worked on by more than one agent at once) don't `DROP DATABASE` out from under each other. `node --test` parallelizes test files by default, so this per-file isolation is what keeps the suite safe to run concurrently.

## What "property test" means here, no fast-check

The project has no property-testing library. In practice this means one of two things, both plain `node:test`:

1. **Table-driven property.** Build an array of fixture objects covering the interesting corners of the input space by hand (boundaries, both extremes, a typical middle case, an adversarial case) and assert the same general property holds for every one, not just one hard-coded example.
2. **Deterministic pseudo-random sweep**, for a genuinely large input space: a small seeded generator produces N fixture inputs deterministically, so a failure is always reproducible by re-running the suite. `tests/perf/` and `tests/unit/questionScoring.test.ts` both use this pattern.

Small, finite spaces (a fault-injection matrix with a handful of combinations) are enumerated explicitly rather than sampled; exhaustive enumeration beats random sampling whenever the space is small enough to write out.

## What is not automatically testable, port-contract tests instead

Some obligations name a real external capability this suite cannot and should not call. For each, the obligation is downgraded to a port-contract test: assert the port interface has the right shape and the stub adapter behind it implements it deterministically, never assert anything about real-world accuracy.

| Not testable here | What's tested instead |
|---|---|
| Real CV nudity/weapons/illegal-content detection, real face detection | `StubMediaModerationAdapter.analyzePhoto` returns the documented deterministic result for each documented trigger substring; the rest of the pipeline (rejection, discovery-eligibility, flagging) reacting correctly to whatever the port returns is fully tested against the stub. |
| Real Stripe authorization/capture/webhooks | `FakeProcessor` and `stripe.processor.ts` implement the same `PaymentProcessor` interface (compile-time contract test); all business-logic rows are proven against `FakeProcessor`. A real Stripe integration is a manual/staging verification step, not part of this suite. |
| Real device fingerprinting / IP reputation accuracy | The signal is treated as an opaque input (a 0 to 100 reputation score) to the trust/moderation pipeline; tests fix the input and assert the pipeline reacts correctly. |
| Real push/email delivery | A `Notification` row is asserted to be queued with the right template key/payload/channel; actual delivery is a separate infra concern. |
| TLS in transit, encryption at rest | Not tested by `node:test` at all; a configuration-review item, not an automated test gap. |

## The actual file layout

```
tests/
  unit/         pure functions and single-service-plus-DB tests (the large majority)
  http/         routes through a real Fastify instance via app.inject, no real socket
  jobs/         each job function run directly against a ManualClock
  concurrency/  true Promise.all-driven races (interest accept/decline, date-proposal
                accept, voucher redemption), not just sequentially-named "race" tests
  perf/         two seeded-at-scale suites proving discovery and compatibility refresh
                don't regress to their old O(platform) query patterns
  foundation.test.ts   standalone smoke test: migrations apply cleanly and idempotently,
                       every config default seeds correctly, policy snapshots are
                       genuinely immutable, flag bucketing is deterministic
```

There are roughly nine near-identical DB-bootstrap helpers under `tests/unit/testCtx*.ts`, `tests/jobs/testHarness.ts`, and `tests/http/testServer.ts`, real duplication, tracked and deliberately not consolidated yet. See `docs/duplication.md` for why.

Every `conformance.md` ID should be traceable to a `test()` name; the convention is naming the string with the ID as a prefix (e.g. `test('C-14.5.3 capture fails after both authorized...', ...)`), so `grep -r "C-14.5.3" tests/` finds the implementation instantly.
