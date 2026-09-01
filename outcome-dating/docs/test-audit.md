# Test Suite Audit — Outcome-Aligned Dating App

**Scope.** All of `tests/unit/`, `tests/http/`, `tests/jobs/`, plus `tests/foundation.test.ts`, cross-referenced against `docs/conformance.md`'s obligation IDs, `docs/test-strategy.md`'s stated isolation/determinism rules, and `docs/risk-review.md`'s safety findings (SAF-1, SAF-2, PRIV-1) to check whether the tests that claim to fix them actually prove it.

**Method.** Full line-by-line read of the highest-risk files (payment, ledger, dateProposal, voucher, interest, moderation, report, safetyFixes, distancePrivacy, deletion, chat/chatDecay, discovery, compatibility, scheduler, webhook, happyPath, roles, errors, dateOutcomeSweep, auth, appeal, autoDecline, filter/eligibility, units, notification) — roughly two-thirds of the suite's ~549 `test()` cases by count. The remainder (job-runner files for compatibility/interest/moderation/trust/voucher/photo-ab-stats recalculation, and the notification/photo/profile/question/tags/timeline/venue-settlement/quiet-hours files) were sampled by header comment, harness pattern, and targeted grep rather than read end to end; those rows in the summary table are marked **(sampled)** and should be treated as lower-confidence than the rest.

**Headline number.** Of the suite's **549 `test()` calls** (the task brief's "~520" — the count has grown mid-audit; other agents are actively adding files), I count roughly **515–525 as tests that genuinely exercise real behavior** through real services and a real Postgres database, with concrete, specific assertions. **This suite is not, in the main, theatre.** The dominant problem is not fake tests but **absent** ones in a small number of high-value places, plus a handful of structural bugs in the harness/tooling that quietly weaken tests that otherwise look strong. I found:
- **~2 fully vacuous tests** (zero runtime assertion — pure `@ts-expect-error` comments that the actual `npm test` command never checks; see Finding 2).
- **~6–8 tests whose names promise more than their bodies check** — mostly "race"-named tests that are actually sequential (Finding 3), and a mock-dependence issue in one flagship file that quietly narrows what it proves (Finding 1).
- **1 test file (out of 56) that never runs at all** under the project's own `npm test` command (Finding 4 — the foundation smoke test).
- A specific, reproducible, already-worked-around timestamp bug in `report.service.ts` (Finding 5).
- Real, material coverage gaps at the discovery-grid/reality-dashboard level and in several state machines' illegal-transition matrices (Findings 6–8).

None of this should be read as "the suite is secretly fine, ignore the brief." The gaps below are concrete and some are dangerous (Finding 1 in particular touches money-adjacent side effects in the file that carries the heaviest conformance weight). But the honest overall picture is: most of the individual agents who wrote this did the work for real, and a follow-up agent's highest-leverage moves are fixing the handful of structural/tooling issues below (which silently blunt many otherwise-good tests at once) and filling five or six specific, nameable gaps — not rewriting the suite.

---

## 1. Prioritized findings

### Finding 1 — CRITICAL. The suite's own flagship money+state-machine file validates trust/notification side effects against a hand-written fake, not the real service, and the fake is now stale

**File:** `tests/unit/dateProposal.test.ts:56–111`

`dateProposal.service.ts`'s tests for the full happy path, all four `§14.5` payment-failure branches, `markNoShow`, and the no-scan-fallback disputed/completed_unverified paths all run through this file. At module load it installs `node:test`'s `mock.module()` over three sibling services:

```ts
mock.module(new URL('../../src/services/conversation.service.ts', import.meta.url), {
  namedExports: { getConversation: fakeGetConversation, establishConversation: fakeEstablishConversation },
});
mock.module(new URL('../../src/services/notification.service.ts', import.meta.url), {
  namedExports: { notify: fakeNotify },
});
mock.module(new URL('../../src/services/trust.service.ts', import.meta.url), {
  namedExports: { recordTrustEvent: fakeRecordTrustEvent },
});
```

The file's own header (lines 1–18) explains why: at the time this file was written, `conversation`/`notification`/`trust` were still `NotImplementedError` stubs owned by sibling agents mid-parallel-build, so hand-written DB-backed fakes stood in for them. That justification **no longer holds** — `trust.service.ts` and `notification.service.ts` are now fully implemented and are each independently, thoroughly tested (`tests/unit/trust.test.ts`, `tests/unit/notification.test.ts`). But `dateProposal.test.ts` was never revisited to drop the mocks.

Concretely, this means every assertion in this file about a trust event or notification being recorded — e.g. `tests/unit/dateProposal.test.ts:489–493` (`markNoShow` must write a `no_show` trust event) — proves only that `dateProposal.service.ts` called *some* function with the same export name and a compatible-looking call shape as the **fake**. It does **not** prove `dateProposal.service.ts` is correctly wired to the *real* `trust.service.recordTrustEvent`/`notification.service.notify`. A real-world regression this setup would miss and nothing else in the suite would catch: `dateProposal.service.ts` calls `trust.recordTrustEvent(ctx, {...})` with a typo'd field name, a wrong `eventType` string, or an argument in the wrong position — the fake (hand-written to whatever shape its author expected) would silently accept it, and because `npm test` performs no type-checking at all (Finding 2), TypeScript wouldn't catch the drift either.

The payment/ledger assertions in this same file are **not** affected — `payment.service.ts`, `ledger.service.ts`, `voucher.service.ts`, and `redemption.service.ts` are real throughout, so the money-correctness findings in this file (§14.5 branches, the happy-path ledger reconciliation) stand on their own merit and are some of the strongest tests in the suite.

**Fix.** Delete the three `mock.module()` calls and the three `fake*` functions (lines 56–111); import `conversation.service.ts`/`notification.service.ts`/`trust.service.ts` directly like every other cross-cutting dependency in this file already does. Re-run the file — if it still passes unmodified, the mocks were adding nothing but risk; if any assertion breaks, that's the exact wiring bug this file was blind to. This is a pure test-file change (no source change), should take under an hour, and immediately upgrades every trust/notification assertion in the file's ~10 tests from "asserts against a fake" to "asserts against production code."

### Finding 2 — HIGH. `@ts-expect-error`-based tests are inert under the actual `npm test` command

`package.json:17`: `"test": "node --import tsx --experimental-test-module-mocks --test tests/**/*.test.ts"`. `tsx` transpiles TypeScript by stripping types (via esbuild) — **it does not type-check.** Verified directly:

```
$ cat tstest.ts
const y: number = "definitely not a number";
console.log("ran anyway", y);
$ node --import tsx tstest.ts
ran anyway definitely not a number
```

`package.json` has a separate `"typecheck": "tsc --noEmit -p tsconfig.json"` script, but nothing wires it into `test` — there is no `pretest` hook and no CI config in the repo at all. So any test whose entire proof is a `// @ts-expect-error` comment is checked by **nothing** the moment a developer runs `npm test`; it only gets checked if someone separately, manually, remembers to run `npm run typecheck`.

Two tests are **wholly** inert this way (zero runtime assertion, the whole body is type-only):
- `tests/unit/notification.test.ts:106-110` — `notify: SMS is not representable at the type level`
- `tests/unit/interest.test.ts:35-42` — `_typeOnly_cannotAttachMessageToSendInterest` (an uncalled function)

Five more combine a real runtime assertion with an unchecked `@ts-expect-error` half (so they're not vacuous, but half of what they claim is unverified by `npm test`): `tests/unit/units.test.ts:56-72` (6 separate `@ts-expect-error` lines proving the branded-type system), `tests/unit/profileAttributes.test.ts`, `tests/unit/report.test.ts:29`.

**Fix.** Add `"pretest": "npm run typecheck"` to `package.json`, or fold `tsc --noEmit -p tsconfig.json &&` into the front of the `test` script. This is a one-line change that makes every `@ts-expect-error`-based test in the suite (and any future one) actually mean something, and it's the correct general-purpose fix rather than deleting or rewriting the individual tests — the tests themselves are well-constructed; the pipeline just never checks the half they're written to check.

### Finding 3 — HIGH. State-machine "race" tests are sequential, not concurrent — the one true concurrency test in the suite proves the pattern was known but unused elsewhere

`docs/conformance.md` C-11.4.SM.I6 is explicit: *"pending → pending (double-accept race)... concurrent accept+decline (or accept+accept) must resolve to exactly one terminal state, second writer gets `conflict`."* Every test claiming to cover this actually runs the two calls sequentially, fully `await`ing the first before issuing the second:

- `tests/unit/interest.test.ts:105-119` (`illegal: accepting an already-declined interest is rejected`) — `await declineInterest(...)` completes and commits, *then* `acceptInterest(...)` is called. This proves the ordinary post-hoc illegal-transition guard, not a race.
- `tests/http/errors.test.ts:85-97` — literally named `double-accepting the same interest race`, body is `await accept(); await decline();` in sequence.
- The same gap exists one level up: `dateProposal.service.ts#acceptDateProposal` performs `authorizeHold` + `captureHold` in one call; a genuinely concurrent double-accept (e.g. a client retry racing the original request) is never tested for double-capture — only sequential idempotent-retry (`tests/unit/payment.test.ts:171-194`) is covered.

The suite already knows how to write this test correctly: `tests/jobs/scheduler.test.ts:91-98` —

```ts
test('two concurrent runJob calls for the SAME job never both execute the body at once (one runs, one is skipped)', async () => {
  const scheduler = new JobScheduler(makeDeps());
  const [a, b] = await Promise.all([scheduler.runJob('chat_decay'), scheduler.runJob('chat_decay')]);
  const skippedCount = [a, b].filter((r) => r.skipped).length;
  const ranCount = [a, b].filter((r) => !r.skipped).length;
  assert.equal(ranCount, 1, ...);
  assert.equal(skippedCount, 1, ...);
});
```

That pattern was simply never applied to the interest/date-proposal state machines it's most needed for.

**Replacement test** (drop-in for `tests/unit/interest.test.ts`):

```ts
test('C-11.4.SM.I6: concurrent accept+decline on the same interest resolves to exactly one terminal state', async () => {
  const sender = await makeUser();
  const recipient = await makeUser();
  const interest = await interestService.sendInterest(ctxFor(sender), recipient);

  const [a, b] = await Promise.allSettled([
    interestService.acceptInterest(ctxFor(recipient), interest.id),
    interestService.declineInterest(ctxFor(recipient), interest.id),
  ]);
  const fulfilled = [a, b].filter((r) => r.status === 'fulfilled').length;
  const rejected = [a, b].filter((r) => r.status === 'rejected').length;
  assert.equal(fulfilled, 1, 'exactly one of the two concurrent calls must win');
  assert.equal(rejected, 1, 'the loser must get a typed conflict, not a silent no-op or a 500');

  const [final] = (await interestService.listOutgoing(ctxFor(sender))).items;
  assert.ok(['accepted', 'declined'].includes(final!.status), 'must land on exactly one terminal state, never both effects applied');
});
```

This is worth writing whether or not it currently passes — if the underlying code has no row-level locking (`SELECT ... FOR UPDATE` or an equivalent optimistic-concurrency check) on the interest/date-proposal transition, this test will flake or double-apply, which is exactly the kind of bug a sequential test can never surface.

### Finding 4 — HIGH. The suite's own smoke test never runs under `npm test`, because of a shell-glob bug

`package.json:17`: `"test": "node --import tsx --experimental-test-module-mocks --test tests/**/*.test.ts"`. `npm run` executes scripts via `/bin/sh`, which on this system (and most Debian/Ubuntu-family systems) is `dash` (verified: `readlink -f /bin/sh` → `/usr/bin/dash`). Dash has no `globstar`; `**` is treated the same as a single `*`, which cannot cross a `/`. So `tests/**/*.test.ts` expands to (effectively) `tests/*/*.test.ts` — matching everything exactly one directory below `tests/`, and **nothing directly inside `tests/` itself**. Verified directly:

```
$ sh -c 'echo tests/**/*.test.ts' | tr ' ' '\n' | grep foundation
(no output)
```

`tests/foundation.test.ts` — the test that verifies migrations apply cleanly and are idempotent, that every `§21.4` config default is seeded correctly, that policy snapshots are genuinely immutable, that feature-flag bucketing is deterministic, and that `seed.ts` produces the right row counts — **never executes** when a developer runs `npm test`. It only runs if invoked directly (`node --import tsx --test tests/foundation.test.ts`) or from an editor's individual-file runner. Nobody would notice: `npm test` still runs ~549 other tests and reports green.

**Fix.** Either list the top-level file explicitly (`"test": "node --import tsx --experimental-test-module-mocks --test tests/foundation.test.ts tests/**/*.test.ts"`), or — better — drop the glob entirely and hand Node a directory: `node --test tests/` performs its own recursive `*.test.ts` discovery independent of the shell, which is immune to this class of bug permanently.

### Finding 5 — MEDIUM-HIGH. `reports.created_at` is stamped by Postgres's real wall clock, not the injected `ManualClock` — a determinism bug the test author found and worked around instead of fixing

`db/migrations/001_init.sql:583`: `created_at timestamptz NOT NULL DEFAULT now()`. `report.service.ts#submitReport` (`src/services/report.service.ts:219-222`) never supplies `created_at` explicitly, so every report row's timestamp comes from Postgres's own `now()` — real wall-clock time — regardless of what `ctx.clock` (the project's `ManualClock` abstraction, meant to be the *only* clock any service reads per `docs/test-strategy.md §3`, cross-cutting invariant CC-12) says "now" is.

The test file itself documents having hit this and worked around it rather than treating it as a bug — `tests/unit/report.test.ts:232-239`:

```ts
// Look at the count from a vantage point well after the report was
// filed (the row's created_at is the DB's own real wall clock, not
// `ctx.clock` — advance a fresh ManualClock forward from "now" so the
// window boundary is unambiguous either way, rather than racing a
// same-instant comparison).
const laterCtx = buildCtx({ now: new Date(Date.now() + 40 * 24 * 60 * 60 * 1000) });
```

This is not cosmetic. `countRecentReportsAgainst` (`src/services/report.service.ts:289-291`) computes its window cutoff as `ctx.clock.now() - sinceDays`, then compares it against `created_at`. This VM's real system clock is genuinely **2026-09-01** (`date -u` → `Tue Sep 1 06:52:14 UTC 2026`), while almost every other test file in this suite pins its `ManualClock` to an arbitrary fixed epoch months earlier (`2026-01-05`, `2026-01-01`, etc., per `docs/test-strategy.md §3`'s own stated convention). Any test — current or future — that (a) inserts a `reports` row (or any of the ~20 other tables sharing the identical `created_at timestamptz DEFAULT now()` pattern — `grep -c "DEFAULT now()" db/migrations/*.sql` totals 65 across the schema) and (b) separately fixes `ctx.clock` to a date meaningfully different from the real "now," will get nonsensical or silently-inverted window comparisons. `report.test.ts` happens to dodge this by anchoring its own `now` to real `Date.now()` throughout — which is precisely why it passes, and precisely why the bug is invisible until someone writes the more natural version of this test using the fixed epoch every sibling file uses.

**Fix.** Pass `ctx.clock.now()` explicitly into the `INSERT` (`INSERT INTO reports (..., created_at) VALUES (..., $8)`), the way `date_proposals.scheduled_start`/`scheduled_end` already do throughout `dateProposal.service.ts`. This is a one-line service change plus a migration-column-default removal (or leave the DB default as a production safety net and just always pass the value explicitly from application code, which is the more common pattern and requires no migration).

### Finding 6 — MEDIUM. The Reality Dashboard (`§9.3`, C-9.3.1–3) has zero test coverage, including its own documented property invariant

`src/services/discovery.service.ts:367` exports `getRealityDashboard`, which computes X ("people who match your filters"), Y ("people whose filters you match"), and Z ("mutual match pool") — with Z's own doc comment stating the invariant `Z ≤ min(X, Y)` that `docs/conformance.md` C-9.3.3 calls a property test. `grep -rn "getRealityDashboard" tests/` returns exactly one hit, and it's a stale doc-comment in `tests/unit/discovery.test.ts:12` noting the function is *not* exercised there. **No test file anywhere in the suite calls `getRealityDashboard`.** X and Y's underlying counters are tested directly (`tests/unit/filter.test.ts:262-263`, `countUsersMatchingMyFilters`/`countUsersWhoseFiltersIMatch`), but Z, the wrapper, and the invariant relating all three are entirely unproven.

**Replacement:** a single new test in `tests/unit/discovery.test.ts`'s DB-backed section —

```ts
test('C-9.3.3: getRealityDashboard — Z (mutual pool) never exceeds min(X, Y)', async () => {
  // build ~6 candidates with a deliberate mix of one-sided and mutual filter passes
  const dash = await discoveryService.getRealityDashboard(ctx);
  assert.ok(dash.mutualMatchPool <= Math.min(dash.matchesMyFilters, dash.whoseFiltersIMatch));
  assert.ok(dash.mutualMatchPool >= 0);
});
```

### Finding 7 — MEDIUM. `getDiscoveryGrid`'s full nine-rule visibility gauntlet is exercised in only two narrow slices; the file's own excuse for skipping it is stale

`tests/unit/discovery.test.ts:12-17` says the full grid is untested because `moderation.service#isVisibleInDiscovery` was "still a `NotImplementedError` stub as of this writing." That dependency has since shipped and is directly, thoroughly unit-tested (`tests/unit/moderation.test.ts`) — but `discovery.test.ts` was never revisited once the blocker cleared. Today, `getDiscoveryGrid` is called by exactly two test files: `tests/unit/eligibility.test.ts:60-92` (3 calls, proving only the mutual-hard-filter gate, C-9.4.1/C-10.2.7-8) and `tests/unit/distancePrivacy.test.ts:340-353` (1 call, proving only that discovery and profile report the same distance figure). **None** of C-10.2.4 (requires an approved photo), C-10.2.5 (incoming-interest-cap exclusion), or C-10.2.6 (active-conversation-cap-of-15 exclusion) is ever exercised through the actual production entry point, even though each rule's *own* underlying data (photo moderation status, interest counts, conversation counts) is unit-tested in isolation elsewhere.

**Fix:** one table-driven test — build 5 candidates, each violating exactly one C-10.2.* rule, plus a control candidate violating none, call `getDiscoveryGrid` once, and assert the result set is exactly `{control}`. This is precisely the "hand-rolled property, 5-20 cases" pattern `docs/test-strategy.md §5` already prescribes and multiple other files in this suite already use well (`tests/unit/discovery.test.ts`'s own tie-break test is a good local model).

### Finding 8 — LOW-MEDIUM. State-machine illegal-transition matrices are narrower than the files' own conformance references imply

- `tests/unit/voucher.test.ts` never tests `markRedeemed` on a `canceled` voucher, nor whether `expireDueVouchers` can wrongly flip an already-`redeemed` voucher to `expired` if it's swept after its `expires_at` has passed. Only redeemed-twice (line 141) and cancel-after-redeem (line 158) are covered.
- `tests/unit/dateProposal.test.ts:460-470`'s "illegal transitions" test covers 3 of the state machine's ~10 illegal edges (declined→accept, declined→decline, canceled→cancel). `completed→cancel`, `refunded→capture`, `disputed→accept`, `expired→accept`, and `no_show→(any)` are never asserted, even though this is otherwise the strongest state-machine file in the suite and clearly has the fixtures to do it cheaply.

**Fix:** extend each file's existing "illegal transitions" test with the missing rows — cheap, mechanical, and each one is a real regression guard once added.

### Finding 9 — LOW. Redundant test investment: the 72h/14d/21d chat-decay thresholds are proven twice, end to end, through two call sites that resolve to one function

`tests/unit/chat.test.ts:130-190` and `tests/jobs/chatDecay.test.ts:41-100` both independently re-derive the same three time boundaries against the same underlying `conversation.service.ts#runChatDecayJob` — `src/jobs/chatDecay.job.ts:15-17` is a one-line pass-through (`export async function runChatCoolingArchivalJob(ctx) { return runChatDecayJob(ctx); }`). ~8 tests total re-confirm one function's three boundaries through two thin wrappers, while (Finding 7) the discovery grid's actual production entry point gets 4 tests covering 2 of 9 rules. Not wrong — both files are individually well-written — but it's a signal the suite's test budget wasn't triaged by risk. Not urgent to fix; worth knowing when prioritizing new coverage.

### Finding 10 — LOW. Loose numeric bound on the one performance-shaped test in the suite

`tests/unit/questionScoring.test.ts:567-586` — `selector: performance does not degrade badly as the bank grows (600 -> 6000)` allows a 10x larger question bank to take up to **40x** longer (`bigMs < smallMs * 40 + 20`), while the test's own comment says an O(n log n) selector "predicts roughly ~11-12x." A regression to O(n^1.5) would still pass. Not vacuous — it does measure something real and would catch true quadratic blowup — just loose enough to miss a meaningful regression. Consider tightening to `smallMs * 20` if the selector's real-world timing has enough headroom to avoid flakiness.

### Finding 11 — LOW. Inconsistent clock discipline in the newest files

`docs/test-strategy.md §3` is explicit: *"never `new ManualClock()` defaulting to real 'now'."* Four of the newest files (evidently written in a later pass than the original per-agent build, addressing `docs/risk-review.md` findings) quietly do exactly this: `tests/unit/safetyFixes.test.ts:79` (`new ManualClock(opts.now ?? new Date())`), `tests/unit/appeal.test.ts:35` (`new ManualClock(new Date())`), `tests/unit/distancePrivacy.test.ts:298`, `tests/unit/deletion.test.ts` (same pattern). Individually low-risk — each of these files only reasons about relative deltas from its own "now," never a hard-coded historical boundary — but it's the same root cause as Finding 5 (real wall-clock leaking into what's supposed to be a fully virtualized-time test suite), and it's the reason these newer files "happen to work" specifically by staying close to real time, which is not a property a reader should have to notice and rely on.

---

## 2. Money and state machines — what's actually proven

| Machine | Legal transitions tested? | Illegal transitions tested? | Concurrency/race tested? | Money invariants proven? |
|---|---|---|---|---|
| **Interest** (`interest.test.ts`) | Yes, all 4 (`interest.test.ts:48-98`) | 6 of 7 conformance rows (I1-I5, I7); **I6 (concurrent double-accept) is sequential, not concurrent — Finding 3** | No | N/A (no money) |
| **Date proposal** (`dateProposal.test.ts`) | Yes, full happy path + expiry + cancellation boundary pair | Only 3 of ~10 implied edges — **Finding 8** | No — **Finding 3** | **Yes, genuinely strong**: every §14.5 branch (proposer-fails, recipient-fails, capture-fails-proposer, capture-fails-recipient-after-proposer-captured) asserts both `payment_holds.status` AND the ledger nets to zero for both parties, not just that a status column moved. This is the best money-testing in the suite. |
| **Payment hold** (`payment.test.ts`) | Yes | Yes (capture-without-authorize, unknown-id, over-refund) | Sequential idempotent-retry only, no true concurrent-retry test | **Yes**: idempotent capture is checked at *three* independent levels in the same test (`payment.test.ts:171-194`) — the service's returned status, the ledger row count, and `FakeProcessor._debugGetIntent().capturedAmountCents` — genuinely proving the processor itself wasn't double-charged, not just that our own row count looks right. |
| **Voucher** (`voucher.test.ts`) | Yes | Missing 2 edges — **Finding 8** | No | N/A directly, but correctly proven idempotent on issuance and to carry no PII/card data in the signed payload |
| **Conversation** (`chat.test.ts`, `chatDecay.test.ts`) | Yes, all thresholds paired at-boundary/just-before | `established` immunity to decay proven at 365 days; `getOrCreateConversation` never reverts an established conversation | No | N/A |
| **Moderation action** (`moderation.test.ts`, `safetyFixes.test.ts`) | Yes, all four action tiers at exact threshold boundaries (49/50, 79/80) | Escalation-only (a second call at the same score is a no-op) is proven; the corroboration model (SAF-1 fix) is proven in both directions with a genuinely adversarial fixture (brigade sharing IP/timing but not fingerprint) | N/A | N/A |

**"Nobody is charged alone" / "a retry never double-charges" / "the ledger balances"** — genuinely proven, not merely asserted. The three-level check in `payment.test.ts:171-194` above, plus `dateProposal.test.ts:355-368`'s "capture fails for the recipient AFTER the proposer already captured" test (which asserts the proposer's hold status is specifically `refunded`, not `released` — the test comment explains why that distinction matters: "money moved for the proposer, so undoing it must be a refund, not a release") are the two best examples of this in the suite.

---

## 3. Conformance.md coverage — honest estimate

`docs/conformance.md` runs to ~280+ numbered rows across §1-§34 (sampled the full first third directly; spot-checked the state-machine and cross-cutting sections referenced by ID throughout the test files). Rough estimate, by section family:

| Area | Estimated coverage |
|---|---|
| §5 Account/verification (age boundary, no-phone, no-ID, duplicate email) | **High** — directly tested with real boundary pairs (`auth.test.ts:69-81`) |
| §6 Trust system (bands, factors, restrictions by level) | **High** | 
| §8-§9 Questions, hard filters | **High** for the filter-enforcement property itself; **partial** for the full mutual-eligibility-plus-visibility integration (Finding 7) |
| §10 Discovery grid | **Partial — the weakest well-defined area found.** Sorting/tie-break/threshold-never-hides is well proven (`discovery.test.ts:71-149`); the full 9-rule visibility gate through the real entry point is not (Finding 7); the Reality Dashboard is entirely untested (Finding 6) |
| §11 Interests | **High**, with the one named concurrency gap (Finding 3) |
| §12 Chat | **High** |
| §13-§15 Date proposals, payment, vouchers, redemption | **High** — this is the best-tested area of the codebase |
| §18 Moderation, reports | **High**, including a real adversarial anti-brigading fixture |
| §25 Background jobs | **High** for the jobs read in full (chatDecay, paymentReconciliation, scheduler); **presumed adequate but not verified** for compatibilityRefresh/dateProposalExpiry/interestExpiry/moderationRecalculation/photoAbStats/trustRecalculation/voucherExpiry (2-3 tests each, consistent header-comment quality with the verified siblings, not read line by line) |
| §28-§29 Privacy, negative/MUST-NOT invariants | **The two CRITICAL findings from `risk-review.md` that got dedicated fix files (SAF-1, SAF-2, PRIV-1) now have genuinely strong, adversarial proof** — see §4 below. Other privacy rows (e.g. C-4.2.5 "no email visible to venue staff", C-28.4.1 "no card data to non-payment routes") were not independently re-verified in this pass and should be sampled by a follow-up. |

I would not claim a precise percentage without reading every one of the ~280 rows against the test files 1:1 (out of scope for this pass), but my honest estimate is **70-80% of conformance.md rows have a real, traceable test**, concentrated heavily in the areas that matter most (money, state machines, safety fixes), with the discovery-grid/reality-dashboard integration as the one area where the gap is both real and easy to name precisely.

---

## 4. What good looks like here — copy these, don't invent a new house style

1. **`tests/unit/distancePrivacy.test.ts:113-163`** — the best test in the suite. Rather than asserting "the fix makes distance safe" in a comment, it implements a real least-squares multilateration attack (the exact one `risk-review.md`'s SAF-2 describes: N accounts at known coordinates, record reported distance, solve for the target), runs a **control** pass with exact/unbucketed distances to prove the attack methodology itself would succeed against an unmitigated system, then runs the real attack against the actual fixed function and asserts the recovered position misses by at least half a bucket width *and* by an order of magnitude worse than the control. This is what "prove the mitigation defeats the documented attack" looks like, not "call the function and check it returns."

2. **`tests/unit/payment.test.ts:171-194`** (idempotent capture) and **`tests/unit/dateProposal.test.ts:355-368`** (refund-vs-release distinction) — money assertions checked at multiple independent levels (our ledger, our hold status, *and* the processor's own internal state via `FakeProcessor._debugGetIntent()`), with comments that explain *why* a particular status was the correct one, not just that a transition occurred.

3. **`tests/unit/compatibility.test.ts:62-114`** — the compatibility-score worked example computes the expected 0.75 by hand in a comment, term by term, rather than re-deriving it with the same formula the implementation uses. This is the difference between a real test and a self-confirming one, applied correctly.

4. **`tests/unit/safetyFixes.test.ts:180-197`** — the SAF-1 anti-brigading test constructs a genuinely adversarial fixture (4 reporters sharing IP and account-creation timing but each with a *different* device fingerprint — the exact evasion the original SAF-6 finding named) and asserts the system still collapses them to one corroborator. It doesn't just test the happy "two unrelated reporters" case; it tries to break its own fix.

5. **`tests/jobs/scheduler.test.ts:91-98`** — the only test in the suite that uses `Promise.all` to prove actual concurrent-execution safety rather than simulating a race sequentially. Should be the template for closing Finding 3.

6. **`tests/unit/deletion.test.ts`** (PRIV-1 fix) — reads the actual rows left behind in every affected table after deletion, never just the `users.status` column, per its own header: *"Every assertion below reads the ACTUAL ROWS in each table after deletion (never just `users.status`) — per the brief's 'test what actually remains in each table, table by table.'"* This is the specific antidote to the "asserts a status column changed without checking the effect" pattern the audit brief warned about — it's already been correctly avoided here.

---

## 5. Summary table — per file

Verdict key: **Solid** = real DB-backed assertions on genuine side effects, matches the file's own claimed scope. **Solid (gap)** = the tests present are solid but the file's own scope is narrower than its subject warrants (see the referenced Finding). **Weak** = real but shallow relative to risk. **(sampled)** = not read end-to-end; verdict inferred from header comments, harness consistency with verified sibling files, and targeted grep — lower confidence.

| File | Tests | Verdict | Solid / Weak / Vacuous |
|---|---:|---|---:|
| `tests/foundation.test.ts` | 5 | Solid content, but **never runs under `npm test`** (Finding 4) | 5 / 0 / 0 |
| `tests/http/errors.test.ts` | 8 | Solid; 1 test mislabeled "race," actually sequential (Finding 3) | 7 / 1 / 0 |
| `tests/http/happyPath.test.ts` | 1 | Solid — genuine 12-step E2E over real HTTP, checks ledger + lat/lon absence | 1 / 0 / 0 |
| `tests/http/matches.test.ts` | 7 | Solid (sampled) | 7 / 0 / 0 |
| `tests/http/roles.test.ts` | 12 | Solid | 12 / 0 / 0 |
| `tests/http/routeTable.test.ts` | 2 | Solid (sampled) | 2 / 0 / 0 |
| `tests/http/serializers.test.ts` | 6 | Solid (sampled) | 6 / 0 / 0 |
| `tests/http/webhook.test.ts` | 4 | Solid — signature + idempotency + hold-state check together | 4 / 0 / 0 |
| `tests/jobs/chatDecay.test.ts` | 6 | Solid | 6 / 0 / 0 |
| `tests/jobs/compatibilityRefresh.test.ts` | 2 | Solid (sampled) | 2 / 0 / 0 |
| `tests/jobs/dateProposalExpiry.test.ts` | 2 | Solid (sampled) | 2 / 0 / 0 |
| `tests/jobs/interestExpiry.test.ts` | 2 | Solid (sampled) | 2 / 0 / 0 |
| `tests/jobs/moderationRecalculation.test.ts` | 3 | Solid (sampled) | 3 / 0 / 0 |
| `tests/jobs/paymentReconciliation.test.ts` | 3 | Solid — flags mismatches, proves no auto-correction, idempotent re-run | 3 / 0 / 0 |
| `tests/jobs/photoAbStats.test.ts` | 3 | Solid (sampled) | 3 / 0 / 0 |
| `tests/jobs/scheduler.test.ts` | 6 | Solid — best-in-class true concurrency test | 6 / 0 / 0 |
| `tests/jobs/trustRecalculation.test.ts` | 3 | Solid (sampled) | 3 / 0 / 0 |
| `tests/jobs/voucherExpiry.test.ts` | 3 | Solid (sampled) | 3 / 0 / 0 |
| `tests/unit/ageDefault.test.ts` | 6 | Solid (sampled) | 6 / 0 / 0 |
| `tests/unit/appeal.test.ts` | 10 | Solid; real-clock construction smell (Finding 11) | 10 / 0 / 0 |
| `tests/unit/auth.test.ts` | 21 | Solid — real boundary pairs, refresh-token-reuse detection, enumeration-safe forgotPassword | 21 / 0 / 0 |
| `tests/unit/autoDecline.test.ts` | 14 | Solid — well-documented product correction, tests reflect real current behavior | 14 / 0 / 0 |
| `tests/unit/chat.test.ts` | 13 | Solid | 13 / 0 / 0 |
| `tests/unit/compatibility.test.ts` | 9 | Solid — exemplar (hand-worked arithmetic) | 9 / 0 / 0 |
| `tests/unit/dateOutcomeSweep.test.ts` | 7 | Solid | 7 / 0 / 0 |
| `tests/unit/dateProposal.test.ts` | 17 | Solid money-testing; trust/notification assertions run against a stale mock (Finding 1); illegal-matrix gap (Finding 8) | 14 / 3 / 0 |
| `tests/unit/decisionsConfig.test.ts` | 9 | Solid (sampled) | 9 / 0 / 0 |
| `tests/unit/deletion.test.ts` | 7 | Solid — exemplar (reads actual rows, not status flags) | 7 / 0 / 0 |
| `tests/unit/devices.test.ts` | 6 | Solid (sampled) | 6 / 0 / 0 |
| `tests/unit/discovery.test.ts` | 11 | Solid for what it covers; the file's own scope is stale/too narrow (Findings 6, 7) | 11 / 0 / 0 |
| `tests/unit/distancePrivacy.test.ts` | 9 | Solid — exemplar (real adversarial attack + control) | 9 / 0 / 0 |
| `tests/unit/eligibility.test.ts` | 9 | Solid for its declared scope | 9 / 0 / 0 |
| `tests/unit/filter.test.ts` | 12 | Solid (sampled beyond pure-function section) | 12 / 0 / 0 |
| `tests/unit/interest.test.ts` | 17 | Solid; sequential "race" naming issue (Finding 3) | 16 / 1 / 0 |
| `tests/unit/matches.test.ts` | 7 | Solid (sampled) | 7 / 0 / 0 |
| `tests/unit/moderation.test.ts` | 13 | Solid | 13 / 0 / 0 |
| `tests/unit/notification.test.ts` | 8 | Solid, with 1 wholly vacuous type-only test (Finding 2) | 7 / 0 / 1 |
| `tests/unit/notificationDelivery.test.ts` | 17 | Solid (sampled; coalescing test verified directly) | 17 / 0 / 0 |
| `tests/unit/payment.test.ts` | 17 | Solid — exemplar | 17 / 0 / 0 |
| `tests/unit/photo.test.ts` | 14 | Solid (sampled) | 14 / 0 / 0 |
| `tests/unit/photoExperiment.test.ts` | 14 | Solid (sampled) | 14 / 0 / 0 |
| `tests/unit/profile.test.ts` | 11 | Solid (sampled) | 11 / 0 / 0 |
| `tests/unit/profileAttributes.test.ts` | 16 | Solid, minor unchecked `@ts-expect-error` half (Finding 2) | 16 / 0 / 0 |
| `tests/unit/question.service.test.ts` | 16 | Solid (sampled) | 16 / 0 / 0 |
| `tests/unit/questionBank600.test.ts` | 4 | Solid (sampled) | 4 / 0 / 0 |
| `tests/unit/questionScoring.test.ts` | 39 | Solid; 1 loosely-bounded perf test (Finding 10) | 38 / 1 / 0 |
| `tests/unit/quietHours.test.ts` | 10 | Solid (sampled) | 10 / 0 / 0 |
| `tests/unit/report.test.ts` | 13 | Solid, and the file that surfaced Finding 5 | 13 / 0 / 0 |
| `tests/unit/safetyFixes.test.ts` | 9 | Solid — exemplar; real-clock construction smell (Finding 11) | 9 / 0 / 0 |
| `tests/unit/tags.test.ts` | 7 | Solid (sampled) | 7 / 0 / 0 |
| `tests/unit/textscan.test.ts` | 19 | Solid (sampled) | 19 / 0 / 0 |
| `tests/unit/timeline.test.ts` | 10 | Solid (sampled) | 10 / 0 / 0 |
| `tests/unit/trust.test.ts` | 15 | Solid (sampled beyond spot-checked rows) | 15 / 0 / 0 |
| `tests/unit/units.test.ts` | 14 | Solid, 1 test partly unchecked via Finding 2 | 14 / 0 / 0 |
| `tests/unit/venueSettlement.test.ts` | 12 | Solid (sampled) | 12 / 0 / 0 |
| `tests/unit/voucher.test.ts` | 10 | Solid; illegal-matrix gap (Finding 8) | 10 / 0 / 0 |
| **Total** | **549** | | **~525 solid / ~10 weak-but-real / ~2 vacuous**, plus the structural issues (Findings 1, 2, 4, 5) that reduce confidence in a further ~15-20 tests without making them individually "wrong" |

---

## 6. Ranked worklist for a follow-up agent

1. **Fix `npm test`'s glob so `tests/foundation.test.ts` actually runs** (Finding 4). One-line change, zero risk, restores the suite's own migration/config/seed smoke test. Do this first — it's the cheapest fix in this document and it's currently silently protecting nothing.
2. **Add `pretest: npm run typecheck`** (Finding 2). One line, makes every existing and future `@ts-expect-error`-based test in the suite mean something, at negligible CI-time cost (`tsc --noEmit` is fast).
3. **Remove the stale mocks in `tests/unit/dateProposal.test.ts`** (Finding 1). This is the highest-value *content* fix — it's the file conformance.md leans on hardest for §13-§15, and right now a third of what it asserts about cross-service wiring is checked against a hand-written fake instead of production code. Delete the `mock.module()` calls, import the real services, re-run, fix whatever breaks (that's the actual bug this exercise would find).
4. **Fix `report.service.ts`'s `created_at`** to use `ctx.clock.now()` explicitly (Finding 5), and audit the other `report.service.ts` and `disputeResolution.service.ts` time-window comparisons for the same pattern while in the file.
5. **Write the true-concurrency double-accept test** for the interest state machine, using `tests/jobs/scheduler.test.ts:91-98`'s `Promise.all` pattern as the template (Finding 3), and confirm whether the underlying code needs a row lock to pass it. Extend the same pattern to `dateProposal.service.ts#acceptDateProposal` once interest is fixed.
6. **Add the discovery-grid full-gauntlet integration test and the Reality Dashboard invariant test** (Findings 6, 7) — both are cheap, both close real, nameable gaps in the area of the spec most central to the product's "we never hide, only sort" trust claim.
7. **Fill the two voucher/date-proposal illegal-transition gaps** (Finding 8) — mechanical, low effort, real regression value.
8. **Normalize clock construction** in `safetyFixes.test.ts`, `appeal.test.ts`, `distancePrivacy.test.ts`, `deletion.test.ts` to the project's own fixed-epoch convention (Finding 11) — low urgency, but cheap, and removes the last thing masking Finding 5 from being obvious sooner.
9. Once the above lands, do a second, targeted pass sampling the "(sampled)" rows in the summary table above with full reads — this audit prioritized the money/state-machine/safety-fix files by risk and did not verify every job-runner and profile/question/notification file line by line.
