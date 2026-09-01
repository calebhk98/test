# Test suite audit

A line-by-line read of roughly two-thirds of the suite by count (payment, ledger, dateProposal, voucher, interest, moderation, report, discovery, and related state-machine files), cross-checked against `docs/conformance.md` and the safety fixes in `docs/risk-review.md`. The headline finding still holds: this suite is not, in the main, theatre. Most agents who wrote it did the work for real; the value here is the handful of structural issues that quietly narrowed what an otherwise-solid test actually proved.

## Fixed since the original audit

- **The suite's own smoke test now runs.** `package.json`'s `test` script uses `bash -c 'shopt -s globstar; ...'`, so `tests/foundation.test.ts` (migrations, config defaults, policy-snapshot immutability, flag bucketing) is no longer silently skipped by a shell-glob limitation.
- **`pretest` now type-checks.** `npm test` runs `tsc --noEmit` before any test executes, so every `@ts-expect-error`-based test (previously checked by nothing) is now real.
- **The flagship money file's stale mocks are gone.** `tests/unit/dateProposal.test.ts` no longer substitutes hand-written fakes for `conversation`/`notification`/`trust.service.ts`; it imports the real, independently-tested implementations, so its trust/notification assertions now prove real wiring, not agreement with a hand-written fake.
- **True concurrency tests exist.** `tests/concurrency/` (`interestRace.test.ts`, `dateProposalRace.test.ts`, `voucherRedemptionRace.test.ts`) drives genuine `Promise.all` races on the state machines the original audit flagged as only sequentially tested, following the pattern `tests/jobs/scheduler.test.ts` already used for job-overlap safety. This is the fix that catches a real concurrent-money bug class the sequential "race"-named tests could never find.
- **The discovery-grid gauntlet and Reality Dashboard invariant are both tested.** `tests/unit/discovery.test.ts` now exercises all nine §10.2 visibility rules through the real batched pipeline and asserts `getRealityDashboard`'s `Z ≤ min(X, Y)` property end to end.

## Still open

- **`report.service.ts`'s `created_at` still comes from Postgres's real wall clock, not `ctx.clock`.** The `INSERT INTO reports` statement has no explicit `created_at` column, so it falls back to the schema's `DEFAULT now()`, the one place in the file that doesn't honor the project's "only `ManualClock` is real time" discipline. `tests/unit/report.test.ts` works around this by anchoring its own clock to real time instead of a fixed epoch, which is why the bug hasn't surfaced: any test using the project's normal fixed-epoch convention against this table would get a wrong window comparison. Fix: pass `ctx.clock.now()` explicitly into the insert, the way `dateProposal.service.ts` already does for its own timestamp columns.
- **Real-clock construction in four newer safety-fix test files.** `tests/unit/safetyFixes.test.ts`, `appeal.test.ts`, `distancePrivacy.test.ts`, and `deletion.test.ts` all construct `new ManualClock(new Date())` (real "now") rather than a fixed historical epoch. Low risk individually (each only reasons about relative deltas), but it's the same root cause as the `report.service.ts` bug above and is worth normalizing to the project's fixed-epoch convention.
- **Illegal-transition matrices are narrower than their own conformance references imply.** `voucher.test.ts` never tests `markRedeemed` on a `canceled` voucher or a late expiry sweep against an already-redeemed one; `dateProposal.test.ts`'s illegal-transition test covers 3 of roughly 10 implied edges. Cheap, mechanical fix once picked up.
- **One loosely-bounded perf assertion.** `questionScoring.test.ts`'s bank-growth test allows a 10x larger bank to take up to 40x longer, while the selector's own claimed complexity predicts about 11 to 12x. Not vacuous, just loose enough to miss a real regression to worse-than-log-linear.
- **Redundant test investment, not a correctness bug.** Chat decay's three time boundaries are proven twice, end to end, through two call sites that resolve to one function, while some other areas (illegal-transition coverage above) are thinner. Worth knowing when prioritizing new coverage, not urgent to fix.

## What good looks like here, copy these

- **`tests/unit/distancePrivacy.test.ts`.** Implements the actual multilateration attack the SAF-2 finding describes, runs a control pass against unmitigated exact distances to prove the attack methodology works, then runs it against the real fixed function and asserts the recovered position misses by an order of magnitude worse. This is what "prove the mitigation defeats the documented attack" looks like.
- **`tests/unit/payment.test.ts`'s idempotent-capture test and `dateProposal.test.ts`'s refund-vs-release distinction.** Money assertions checked at three independent levels at once: the ledger row count, the hold status, and the fake processor's own internal state, with comments explaining why a given status is the correct one.
- **`tests/unit/compatibility.test.ts`.** The worked example computes the expected score by hand, term by term, in a comment, rather than re-deriving it with the same formula the implementation uses.
- **`tests/unit/safetyFixes.test.ts`.** The anti-brigading test builds a genuinely adversarial fixture (reporters sharing IP and creation-time proximity but distinct device fingerprints) and asserts the fix still collapses them to one corroborator.
- **`tests/unit/deletion.test.ts`.** Reads the actual rows left behind in every affected table after deletion, never just a status column.

## Ranked worklist

1. Fix `report.service.ts`'s `created_at` to use `ctx.clock.now()` explicitly, and audit `disputeResolution.service.ts` for the same pattern while in the area.
2. Fill the voucher/date-proposal illegal-transition gaps.
3. Normalize clock construction in the four newer safety-fix test files to the project's fixed-epoch convention.
4. Tighten the loose perf bound if it's not causing flakiness at the tighter threshold.
