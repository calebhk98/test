# Duplication and divergence audit

Scope: `/home/user/test/outcome-dating`, read-only audit. Method: grepped for
candidate duplication, then read both sides of every candidate and compared
behavior at boundaries (null, empty, zero, max) rather than trusting text
similarity. All line numbers below were verified against the tree as of this
audit; several agents are editing concurrently, so re-check line numbers
before acting on this document.

**Headline: 5 already-divergent duplicates found** (live behavioral
inconsistencies today, not just repetition risk), plus 5 at-risk duplicates
and a cluster of cosmetic repetition. The worst is the **trust-score
exposure gate** (finding 1): a documented "single source of truth" function
for a privacy-sensitive gate is never called by the one route that needs it,
which instead uses a completely separate, differently-keyed toggle — so the
"authoritative" gate is dead code and an admin operating the documented
control has no effect on what actually ships to the wire.

---

## Part 1 — Already divergent (live defects, ranked)

### 1. Trust-score exposure gate: two independent toggles, only one wired in [PRIVACY — HIGHEST]

- **Locations:**
  - `src/services/trust.service.ts:399-411` — `shouldExposeRawTrustScore(ctx)`, reads config key `trust.expose_raw_score` (boolean, default `false`, `src/config/config.service.ts:275`). Its doc comment (lines 399-408) states in-file: *"This is the single source of truth for the display gate: the HTTP layer should call this before deciding whether to serialize `trustScore`."*
  - `src/http/serializers/trust.ts:22,31-37` — `serializeTrustSummary` gates the same field via `flags.isEnabled('expose_trust_score_to_user', {userId})`, an **ad-hoc, per-user, unseeded feature flag** (not in `KNOWN_FLAGS`, `src/config/flags.service.ts:23-31`) that defaults off.
  - `src/http/routes/trust.routes.ts:24` — the only live `GET /me/trust` route calls `serializeTrustSummary(deps.flags, userId, summary)` directly. It **never calls `shouldExposeRawTrustScore`** anywhere in the codebase (confirmed by grep — its only other reference is a unit test, `tests/unit/decisionsConfig.test.ts:104-109`, which calls it directly and never through the route).
- **Do they agree today?** By coincidence, both default to "hidden" (`trust.expose_raw_score` defaults `false`; the flag is unseeded, which `flags.service.ts` also treats as off). So no numeric score currently leaks. But the two controls are **structurally decoupled**, contradicting the "single source of truth" comment.
- **Concrete divergent input:** An admin sets `trust.expose_raw_score = true` (the documented control, per its own doc comment and per `tests/unit/decisionsConfig.test.ts`), expecting `trustScore` to start appearing in `GET /me/trust` responses. **Nothing changes** — the field stays hidden for every user, because the actual route only consults the unrelated `expose_trust_score_to_user` flag, which the admin never touched. Conversely, someone could enable the per-user flag for a rollout segment via `flags.service.ts#setFlag`, and those users' raw scores would start being served even with `trust.expose_raw_score` left at its safe default `false` — the config-level "off" gives no actual protection against that path.
- **Consequence:** A privacy control that looks authoritative and is unit-tested (`decisionsConfig.test.ts`) has zero effect on production behavior. This is exactly the shape of the SAF-2 distance bug (two divergent authorities for one privacy decision) but for trust-score exposure instead of distance.
- **Canonical:** `serializeTrustSummary`'s flag-based gate is what's actually live — pick it, or wire `shouldExposeRawTrustScore` into it, but not both independently.
- **Consolidation step:** Either (a) delete `shouldExposeRawTrustScore` and its config key, keeping the flag as sole gate, or (b) have `serializeTrustSummary` call `shouldExposeRawTrustScore(ctx)` (needs a `Ctx`, not just `flags`, so its signature would need to change) and delete the ad-hoc flag. (a) is less invasive since the flag is what ships today. Either way, delete or update `tests/unit/decisionsConfig.test.ts:104-109`, which currently asserts behavior for a function nothing calls.

### 2. Per-hour clickable-link rate limit ignores the trust-tier boundary it's supposed to track [RATE LIMITING]

- **Locations:**
  - `src/services/trust.service.ts:547-552` — `linksPerHourLimitFor(ctx, trustLevel)`, buckets via `levelMeetsLinkMinimum` against the **configurable** `trust.link_min_level` key. Its doc comment (`trust.service.ts:483-499`, the `can()` function's "§6.4 vs §12.3 PRECEDENCE" note) explicitly predicts this exact bug: *"If an admin retunes `trust.link_min_level`... §12.3's bucket assignment would silently stay pinned to the literal 'limited' level unless it is ALSO derived from `trust.link_min_level`... `linksPerHourLimitFor` below is the function `message.service.ts` should call... instead of re-deriving its own trust-tier comparison."*
  - `src/services/message.service.ts:97-102` — `linkLimitForCaller(ctx)` does exactly the re-derivation the comment above warns against: `if (trustLevel === 'limited') return ...low_trust; if (trustLevel === 'standard') return ...standard_trust;` — a **hardcoded** boundary at `'limited'` vs everything else, independent of `trust.link_min_level`.
  - Confirmed via import check: `message.service.ts:8` does import `trustService` and does call `trustService.canSendClickableLinks` (line 136, the *render-time* clickability gate) — but for the *send-time* per-hour cap (line 144, `linkLimitForCaller`) it does not call `trustService.linksPerHourLimitFor` at all.
- **Do they agree today?** Only while `trust.link_min_level` is left at its shipped default (`'standard'`, presumably — the boundary the hardcoded check also assumes). They diverge the moment an admin changes that config value.
- **Concrete divergent input:** Admin sets `trust.link_min_level = 'trusted'` (tightening the bar). For a `'standard'`-trust user sending a message with a link:
  - `canSendClickableLinks` (via `can()`/render-time gate): `standard` rank < `trusted` rank → link renders as **blocked**, reason `links_disabled_low_trust`.
  - `linkLimitForCaller` (send-time cap, actually used by `message.service.ts`): trustLevel is literally `'standard'` → returns `chat.max_links_per_hour_standard_trust` (a positive number, e.g. 5/hr) — the user can still **send** several links per hour; they just won't render clickable. The intended design (per the doc comment) was for both gates to move together when the config is retuned, bucketing a demoted `'standard'` user into the low-trust send cap too.
- **Consequence:** Retuning the trust threshold for links only half-applies — the visible/clickability behavior changes, the actual send-volume rate limit does not. Not a catastrophic leak, but a real, silently-broken admin control, self-documented as the exact failure mode to avoid.
- **Canonical:** `trust.service.ts#linksPerHourLimitFor` (already written, already exported for this purpose).
- **Consolidation step:** In `message.service.ts`, replace the body of `linkLimitForCaller` with `return trustService.linksPerHourLimitFor(ctx, trustLevel);` and delete the local hardcoded version. Low-risk, single-file change, already has an existing test target (extend `tests/unit/chat.test.ts`/`tests/unit/trust.test.ts` with a case that retunes `trust.link_min_level` and asserts the per-hour cap moves with it — no such test currently exists).

### 3. Cursor pagination: three sibling list endpoints skip the malformed-cursor validation two others have [ROBUSTNESS / INCONSISTENT ERROR CONTRACT]

- **Locations (`decodeCursor` implementations, all encoding `(timestamp, id)` as `base64url("iso|id")`):**
  - **Missing `Invalid Date` check:** `src/services/notification.service.ts:122-126`, `src/services/message.service.ts:90-94`, `src/services/interest.service.ts:287-291` — each does `new Date(iso)` and returns it unchecked.
  - **Has the check:** `src/services/timeline.service.ts:228-235` and `src/services/matches.service.ts:112-118` both explicitly `if (Number.isNaN(occurredAt.getTime())) throw new ValidationError(...)` (or the `activityAt` equivalent) right after parsing.
  - A sixth, structurally different implementation: `src/services/ledger.service.ts:180-190` encodes as `base64url(JSON.stringify([iso, id]))` (a JSON array, not pipe-delimited) — a different wire format from the other five, and also performs no date-validity check (only a `try/catch` around `JSON.parse` itself).
- **Do they agree today?** No — this is already-inconsistent code, not merely "could" diverge. `GET /me/notifications`, `GET /conversations/:id/messages`, and `GET /interests/...` (paginated) currently accept a cursor with a corrupted-but-parseable date differently from `GET /matches` and `GET /conversations/:id/timeline`.
- **Concrete divergent input:** cursor `=` `base64url("not-a-date|11111111-1111-1111-1111-111111111111")`.
  - Against `GET /matches` or the timeline endpoint: `Number.isNaN(new Date('not-a-date').getTime())` is `true` → clean `ValidationError` → HTTP 400 `{error:{code:'validation_error',...}}` (per `src/http/errors.ts:35-39`).
  - Against `GET /me/notifications`, the messages list, or the interests list: the invalid `Date` object is threaded straight into a parameterized SQL query (e.g. `message.service.ts:213-221`). `node-postgres` serializing an `Invalid Date` throws synchronously (`RangeError: Invalid time value`), which is not an `AppError`/`ZodError`/Fastify request error, so it falls through to the generic handler (`src/http/errors.ts:66-69`) → **HTTP 500** `internal_error`, plus a `console.error` write, for what is really client-supplied bad input.
- **Consequence:** Same failure class (garbage cursor), different status code and different log noise depending on which list endpoint receives it — an availability/observability inconsistency an attacker or a buggy client can trivially trigger, and it pollutes error-rate alerting with "unhandled_error" for ordinary bad input on 3 of 6 endpoints. No test in the repo exercises an invalid cursor on any of these six functions (confirmed: no test file matches `Invalid cursor`/`invalid.*cursor`).
- **Canonical:** the `timeline.service.ts`/`matches.service.ts` pattern (validate immediately, throw `ValidationError`).
- **Consolidation step:** extract one shared `decodeTimestampIdCursor(cursor): {ts: Date; id: string}` (or similar) into e.g. `src/lib/cursor.ts` that both encodes and validates, and have all five pipe-delimited call sites (notification/message/matches/timeline/interest) use it; decide separately whether to also fold `ledger.service.ts`'s JSON-array variant into the same format (its own consolidation, see finding 8) or just add the same NaN check to it in place. Low-risk: pure internal refactor, same external cursor semantics for the two already-correct services, and it *fixes* observable behavior (500→400) for the other three, which is worth flagging to route owners since it changes a status code.

### 4. Two incompatible pagination strategies for what is otherwise the same "paged list" contract [ROBUSTNESS]

- **Keyset (stable under concurrent inserts):** ledger, notification, timeline, message, matches, interest (all six from finding 3).
- **Offset (`OFFSET $n`, encoded as the literal decimal offset string) — NOT stable under concurrent inserts at the head of the `ORDER BY ... DESC` list:**
  - `src/services/discovery.service.ts:120-124` (`parseCursorOffset`) — used for the discovery grid.
  - `src/services/trust.service.ts:290-315` (`listMyTrustEvents`) — `offset = params?.cursor ? Number(params.cursor) : 0`, `LIMIT $2 OFFSET $3`.
  - `src/services/moderation.service.ts:341-362` (`listModerationActions`) — same pattern.
  - `src/services/venueSettlement.service.ts:265-286` (`listVenueSettlements`) — same pattern.
  - **A fourth, distinct scheme:** `src/services/question.service.ts:537-563` (`listActiveQuestionBank`) uses the **raw row id itself, unencoded**, as the cursor (`WHERE id > $cursor ORDER BY id`) — single-column ascending keyset, no base64, no timestamp.
- **Do they agree today?** They already behave differently by construction — this isn't hypothetical. `trust_events` rows are inserted continuously by `trustRecalculation.job.ts` (`trust.service.ts:356` `INSERT INTO trust_events`) and `moderation_actions` rows by moderation flows (`moderation.service.ts:280`), i.e. exactly the kind of "list that keeps growing while someone pages through it" scenario offset pagination gets wrong.
- **Concrete divergent input:** A user fetches page 1 of `GET /me/trust/events` (limit 5, newest-first) → items `[e5,e4,e3,e2,e1]`, `nextCursor: "5"`. Before they fetch page 2, `trustRecalculation.job.ts` inserts a new event `e6` for that user (background job, runs on its own schedule, not synchronized with the user's request). Page 2 (`offset=5`) now reads against `[e6,e5,e4,e3,e2,e1,...]` and returns `e1` shifted correctly only if nothing else changed — but critically it also just as easily **re-shows `e5`** (already seen on page 1) or **skips an item**, depending on exactly how many rows were inserted between the two requests. The keyset-paginated endpoints (ledger, notifications, matches, etc.) do not have this failure mode — a `(created_at, id) < (cursor)` WHERE clause is correct regardless of what got inserted after the cursor's row.
- **Consequence:** Silent gaps or duplicates in an audit-trail-shaped list (trust events, moderation actions, venue settlements) precisely when a background job is actively writing to it — which for trust events and moderation actions is normal, expected, ongoing activity, not an edge case.
- **Canonical:** the keyset `(created_at, id) <` pattern already used by 6 other services.
- **Consolidation step:** convert `listMyTrustEvents`, `listModerationActions`, `listVenueSettlements` to keyset pagination using the same shared cursor helper proposed in finding 3. `discovery.service.ts`'s offset cursor is lower priority to convert — its "list" is a freshly-ranked candidate pool each call, not a stable audit trail, so skip/dup on it is a materially smaller product concern (arguably even acceptable) — deprioritize it under this item. `question.service.ts`'s raw-id cursor is a defensible, intentionally different design for a small admin-managed content table (question bank), not a user-facing paginated feed; leave it as reasoned intentional difference, not a target for this consolidation.

### 5. Expiry/cutoff boundary operator disagrees across three "has this timed out" checks [DATE/TIME ARITHMETIC — minor]

- **Locations:**
  - `src/services/interest.service.ts:583` — `WHERE status = 'pending' AND expires_at <= $1` (inclusive: expires exactly *at* `now` counts as expired).
  - `src/services/dateProposal.service.ts:694-695` — `if (now.getTime() < deadline.getTime()) continue;` i.e. proceeds (expires) when `now >= deadline` — also inclusive.
  - `src/services/voucher.service.ts:181` — `WHERE status = 'issued' AND expires_at < $1` — **exclusive** (a voucher expiring at exactly `now` is *not yet* expired this tick).
- **Do they agree today?** No — code already uses `<=`/`>=` in two places and strict `<`/`>` in a third for the same underlying "is `expires_at` in the past" question.
- **Concrete divergent input:** an interest and a voucher both configured to expire at exactly `T`, and an expiry job runs with `ctx.clock.now() === T` (reachable deterministically in a `ManualClock`-driven test, vanishingly unlikely but not impossible in production given job-tick granularity): the interest expires this run; the voucher does not, and waits for the next tick.
- **Consequence:** low real-world impact (the window is one instant), but it is an inconsistency a test author could trip on if they assume one convention while writing a boundary test against the other service, and it's exactly the category of arithmetic the task brief calls out as historically dangerous.
- **Canonical:** inclusive (`<=`/`>=`) matches the interest/date-proposal reading of "at or past the cutoff, treat as expired" and is the majority convention (2 of 3).
- **Consolidation step:** change `voucher.service.ts:181` to `expires_at <= $1` for consistency. Trivial, single-line, but touches a job path — coordinate with whoever owns `voucher.service.ts`/`voucherExpiry.job.ts` before merging concurrently with other edits there.

---

## Part 2 — At risk (not yet producing different output, but positioned to)

### 6. Two full compatibility-scoring implementations; only one is wired to the API [SCORING — the exact scenario the task brief predicted]

- **Locations:**
  - **Live:** `src/services/compatibility.service.ts:197-273` (`computePairScore`), called from `getScore` (line 288), `getScoresForCandidates` (line 316), `refreshAllScores`/`refreshScoresForUser` (line 361) — the only compatibility-score path actually reachable from the HTTP API (`matches`/`discovery` consume these). Operates against the **old** schema: `questions`/`answers` tables.
  - **Built, tested, not wired in:** `src/domain/questions/scoring.ts:104-176` (`scoreQuestionContribution` + `aggregateQuestionScores`), operating against the **new** typed bank: `question_bank`/`user_question_answers` (migration `db/migrations/008_questions.sql`). Confirmed via grep: its only callers anywhere in the repo are `tests/unit/questionScoring.test.ts`; no `src/services/**` file calls it. `scoring.ts:6-16`'s own doc comment says so explicitly: *"`compatibility.service.ts`... still computes its own score against the OLD `questions`/`answers` schema for now... A later agent should call [this] ONCE PER QUESTION."* `aggregateQuestionScores`'s doc (`scoring.ts:141-147`) goes further: *"`compatibility.service.ts` is free to inline this shape itself instead of importing it."*
  - Notably, the **rest** of the new typed-bank machinery is *not* all dormant — its deal-breaker derivation is live in `eligibility.service.ts`'s hard-filter path (`question.service.ts:861-897`, `WHERE importance = 'deal_breaker'`) and its tag resolution is live in `discovery.service.ts:8` (`resolveVisibleTagsFor`). Only the **scoring** half of the new system is unwired — so this isn't dead code in general, just this one function.
- **Why this is "at risk" rather than "already divergent":** since nothing in production calls `scoreQuestionContribution`/`aggregateQuestionScores` today, there is no live request that gets two different numbers. The risk is what happens on the very next integration step, which the code's own comments actively invite a "later agent" to take.
- **The two algorithms are NOT drop-in equivalent — if wired in naively, results WILL diverge:**
  - **Satisfaction:** old (`computePairScore`, `compatibility.service.ts:203-217`) is a fixed formula on the raw 1-5 scale — `1 - abs(partnerAnswer - otherSelf)/4`, averaged both directions — for *every* question regardless of type. New (`scoreQuestionContribution`, `scoring.ts:127-130`) delegates to a **type-specific handler** (`getTypeHandler(question.typeDef.type)`, `src/domain/questions/typeHandlers.ts`), so a numeric, boolean, and enum question can each compute "satisfaction" by a different rule.
  - **Importance/weight:** old derives weight purely from *how extreme the numeric partner-answer is* (`1 + abs(partnerAnswer-3)*0.25`, `compatibility.service.ts:213-216`) — there is no separate importance field in the old schema at all. New reads an explicit, separately-captured categorical `importance` (`irrelevant`/`slight`/`important`/`critical`/`deal_breaker`, via `importanceMultiplier`, `scoring.ts:118-125`).
  - **Exclusion semantics:** old has none beyond "both sides answered" — no concept of a question being excluded for being a deal-breaker (deal-breakers aren't representable in the old schema). New explicitly excludes `irrelevant` and `deal_breaker` questions from the weighted sum (`scoring.ts:82-85,120-125`) — by design, the new deal-breaker exclusion already double-covers what the old system doesn't cover at all (deal-breakers are separately enforced as a hard filter, not scored, in *both* systems' intended design — but only the new one actually implements skipping them in the weighted sum; the old one has no such row to skip in the first place).
  - **No-data threshold:** old gates the whole score to `noDataDefaultScore` when `sharedAnsweredQuestionCount < minSharedQuestions` (config-driven, `compatibility.service.ts:227-229`). New's `aggregateQuestionScores` has no equivalent minimum-count gate — `score = weightTotal > 0 ? weightedSum/weightTotal : noDataDefaultScore` (`scoring.ts:174-175`) fires on just one contributing question.
- **Consequence if wired in incorrectly:** either (a) both systems get summed/blended, silently double-weighting users who've answered both banks, or (b) the new system replaces the old one and every existing match's compatibility score jumps for reasons that have nothing to do with the user's actual answers changing — because the *scoring model itself* changed shape (categorical importance vs numeric-extremity, per-type satisfaction vs one fixed formula, no minimum-shared-questions floor). This is precisely the class of bug the task brief's "typed question bank added alongside an older one" warning describes, still unresolved.
- **Canonical:** neither is unconditionally "right" — this needs a product decision (migrate users' answers, or run both banks in parallel and decide how to combine), not a mechanical merge. Flag this to whoever picks up the integration rather than treating it as a simple duplicate-removal.
- **Consolidation step:** before wiring `scoreQuestionContribution` into `compatibility.service.ts` (or anywhere reachable from the API), add a test that runs *both* systems against the same synthetic answer set and documents the expected score delta — right now there is no test proving how far apart they'd land, which is exactly the blind spot that let the SAF-2 distance bug ship in the first place.

### 7. Exact-distance haversine duplicated (by design) between the privacy layer and the hard-filter layer

- **Locations:** `src/domain/units/distance.ts:162-169` (`haversineKmExact`, deliberately unexported — internal to the approximate/bucketed/jittered display path) and `src/services/filter.service.ts:362-372` (`haversineKm`, exported, used only for exact `distance_km` hard-filter comparisons, never displayed).
- **Do they agree today?** Yes — both use `R = 6371`, the identical spherical-law-of-cosines/haversine formula, byte-for-byte equivalent math. Verified by reading both function bodies side by side.
- **Why this is flagged despite agreeing:** `distance.ts:161`'s own comment explicitly calls out this exact pair as **not** the SAF-2 duplication ("this is not the duplication SAF-2 is about") and justifies keeping them separate because filter enforcement is a different concern from privacy display. That's a reasonable position, but it is still two independently-maintained copies of the same 8-line formula with the same magic constant (`6371`) — if someone later tunes the earth-radius constant or switches to a more precise ellipsoid model in one file (e.g. for filter accuracy near the poles) without the other, hard-filter "within 50km" enforcement and the *displayed* approximate distance would start disagreeing about what's "close," which is a much more subtle and harder-to-notice bug than the original SAF-2 one because neither function is wrong in isolation.
- **Canonical:** N/A — not recommending a merge (the file-ownership/concern-separation reasoning in `distance.ts`'s own comment is sound), but recommend adding a direct test asserting the two formulas produce the same output for a shared set of coordinate pairs, so any future edit to either one trips a test rather than silently drifting. No such test currently exists (`tests/unit/filter.test.ts:101-104` tests `haversineKm` alone; `distance.ts`'s internal-only formula is exercised indirectly via `__internal.haversineKmExact`, `tests/unit/units.test.ts`, but nothing cross-checks the two against each other).
- **Consolidation step:** add a small cross-check test; do not merge the implementations.

### 8. Cursor encoding: 4 distinct wire formats across the pagination sprawl (finding 3/4's format fragmentation, restated as its own item)

- Pipe-delimited `base64url("iso|id")`: notification/message/matches/timeline/interest.
- JSON-array `base64url(JSON.stringify([iso,id]))`: `ledger.service.ts:180-190` — behaviorally equivalent but wire-incompatible with the pipe format (a cursor from one endpoint would fail to decode against another, which is fine since they're never cross-used, but it means there's no single "the cursor format" a client or a future shared middleware could assume).
- Raw decimal offset string: discovery/trust/moderation/venueSettlement.
- Raw unencoded id: `question.service.ts`.
- **Consequence:** none today (no cross-endpoint cursor reuse happens), but every new paginated endpoint an agent adds has 4 existing precedents to copy from with no obviously-correct default, which is how the sprawl grew to 4 variants in the first place.
- **Consolidation step:** same shared `src/lib/cursor.ts` helper proposed in finding 3, offered as the one new-endpoint default; leave `question.service.ts`'s raw-id scheme as a documented, intentional exception (small admin content table, not a growing user feed).

### 9. Money rounding helper duplicated verbatim (currently in agreement)

- **Locations:** `src/services/dateProposal.service.ts:283-285` (`percentOfCents`, `Math.floor((amountCents*percent)/100)`) and `src/services/venueSettlement.service.ts:109-118` (`computeVenuePayout`, same `Math.floor` rule, plus deriving the platform's share by subtraction so the two parts always sum exactly to the gross).
- **Do they agree?** Yes, and unusually well cross-documented — `venueSettlement.service.ts:46` explicitly says *"the same 'round down, in the platform's favor' rule `payment.service.ts` uses"*, and `dateProposal.service.ts:280` cross-references `payment.service.ts#refundHold`'s doc. Checked all three (`payment.service.ts:418-423` documents the same rule for its callers) — all consistently round down. No divergence found.
- **Consequence if it drifts:** money — the highest-severity category per the task brief — so despite agreeing today this is worth deduplicating pre-emptively rather than waiting for a third or fourth copy (payments-adjacent code is exactly where new agents are likely to add a fifth percent-of-cents call site).
- **Canonical:** either one; trivial to extract.
- **Consolidation step:** move `percentOfCents` to a shared module (e.g. `src/lib/money.ts`) and have `venueSettlement.service.ts#computeVenuePayout` call it for the `venuePayoutCents` half (keeping the subtraction-not-second-floor construction for `platformCents`, which is itself important and already correctly done in exactly one place).

### 10. TypeScript enum unions vs SQL `CHECK` constraints — spot-checked, currently in sync

Explicitly checked (per the task's "or a statement that you verified they agree"):

- `DateProposalStatus` (14 values) — `src/domain/types.ts:472-486` vs `db/migrations/001_init.sql:401-405`: **identical set**, same order.
- `PaymentHoldStatus` / `payment_holds.status` — `src/domain/types.ts:542-...` vs `db/migrations/001_init.sql:452-455`: **agree**.
- `LedgerEntryType` (7 values, including `'venue_payout'`) vs `payment_ledger.type` — initially looked like a mismatch (`001_init.sql:482` only lists 6 values, missing `venue_payout`), but `db/migrations/007_decisions.sql:40-42` correctly `ALTER`s the constraint to add it, matching the TS union exactly, and adds a companion `CHECK` (`007_decisions.sql:46-47`) enforcing the `venue_payout ⇒ venue_id set, user_id null` / else-branch invariant. **Verified in sync**, well-executed migration.
- `TrustLevel` (4 values) — consistent across `domain/types.ts`, `config.service.ts`'s zod enum (`config.service.ts:44`), and the SQL `CHECK` (`001_init.sql:33`).

No drift found in the samples checked. This remains a standing, general-pattern risk (every new status value requires remembering to update both the TS union and the SQL constraint, with nothing mechanically tying them together) — flagged as at-risk process debt, not a current bug. If a consolidation budget exists, a small script asserting the TS union values equal the live `pg_get_constraintdef` output per enum-like column would catch the next drift automatically; no such check exists today.

---

## Part 3 — Cosmetic repetition (true duplication, low/no divergence risk)

### 11. Test harness sprawl — 9 near-identical DB-bootstrap files, ~1391 lines total

| File | Lines | DB prefix | Ctx-building shape |
|---|---|---|---|
| `tests/unit/testCtx.ts` | 102 | `odate_agent_a_*` | module-singleton `buildCtx(opts)` (no db param) |
| `tests/unit/testCtxAgentC.ts` | 112 | `odate_agent_c_*` | module-singleton |
| `tests/unit/testCtxAgentE.ts` | 176 | `odate_agent_e_*` | module-singleton |
| `tests/unit/testCtxEligibility.ts` | 187 | `odate_elig_*` | module-singleton |
| `tests/unit/testCtxDecisions.ts` | 152 | `odate_decisions_*` | explicit `TestDb` object + `makeCtx(db, actor, opts)` |
| `tests/unit/testHarness.ts` | 141 | `odate_agent_d_*` | explicit `TestDb` + `makeCtx` |
| `tests/unit/testHarnessMatch.ts` | 169 | `odate_match_*` | explicit `TestDb` + `makeCtx` |
| `tests/jobs/testHarness.ts` | 135 | `odate_jobs_*` | explicit `TestDb`-like + `makeCtx` |
| `tests/http/testServer.ts` | 217 | `odate_http_*` | explicit `TestDb`-like, also boots a Fastify instance |
| (inline, not a shared file) `tests/unit/safetyFixes.test.ts` | — | `odate_safety_*` | deliberately self-contained, explicitly documented as *not* sharing `testCtxAgentE.ts` "so it never races another suite for a DROP/CREATE DATABASE lock" |

- **Shared connection-state race — how each harness actually manages it (the task specifically asks about this):** every harness mutates the **process-wide** `process.env.DATABASE_URL` and calls the **module-level singleton** pool in `src/db/pool.ts` (`getPool()`/`closePool()`). That is only safe because every one of these files' own doc comments correctly rely on the same assumption: *"Node's test runner runs separate `*.test.ts` files concurrently in separate processes by default"* (verbatim or near-verbatim in `testCtx.ts:25`, `testCtxAgentC.ts:11`, `testCtxAgentE.ts:30`, `testCtxEligibility.ts:11-12`, `testHarness.ts:6`, `testHarnessMatch.ts:9-10`) — i.e. each test *file* gets a fresh Node process, so the shared singleton and the shared env var are never actually contended across files. **Verified this assumption holds in practice for this repo**: `package.json`'s `test` script is `node --import tsx --experimental-test-module-mocks --test tests/**/*.test.ts` with no `--test-isolation=none` override (which would break the assumption), and every test file that imports a given harness (checked by grep across all `tests/unit/*.test.ts`) imports **exactly one** harness module — no file mixes two harnesses, which would have shared one process's singleton pool between two different DB-bootstrap strategies and genuinely raced. Within-file DB-name collisions were also checked: every `suite`/`suffix` string passed to `setupTestDatabase`/`setupTestDb` is unique within its harness's prefix namespace (no two files under the same prefix pass the same suite name). **Conclusion: the race the harnesses are defending against is real and correctly defended against by all 9, consistently** — this is disciplined, not sloppy, duplication.
- **What differs and whether it's load-bearing:**
  - **API shape** (module-singleton `buildCtx()` vs explicit `TestDb`+`makeCtx(db,...)`) — load-bearing for anyone trying to share a helper *across* these files (you can't), but not a correctness risk within any one file.
  - **`config.seedDefaults()`/`flags.seedKnownFlags()`** — called in some harnesses (`testHarness.ts:55-56`, `testHarnessMatch.ts`, `tests/http/testServer.ts`), not in others (`testCtx.ts` never calls it). **Checked whether this is load-bearing:** it is not — `ConfigService.get()` (`src/config/config.service.ts:411-431`) falls back to the same in-code registry default whether or not a row has been seeded, and `ConfigService.set()` (`config.service.ts:461-478`) uses `ON CONFLICT DO UPDATE`, so it doesn't depend on a pre-existing row either. Seeding only pre-populates rows that would otherwise be filled lazily with identical values. **Accidental, not load-bearing**, difference.
  - **Fake adapter wiring** — checked all 9: every harness that builds a `Ctx` wires the same pair, `FakeProcessor` (`src/services/payments/fake.processor.ts`) and `StubMediaModerationAdapter` (`src/services/media/stub.adapter.js`), with no substitutions. **Consistent.**
- **Consolidation step (LOW PRIORITY, and explicitly flagged as risky to do right now):** these files are actively owned by different in-flight agent workstreams per their own doc comments ("Agent A's unit tests", "Agent D's", etc.) — the file-ownership boundaries that produced this sprawl are, per the task's framing, likely still the active editing boundaries of the concurrent agents working on this tree right now. **Do not merge or delete any of these 9 files while other agents may be mid-edit on their corresponding `*.test.ts` suites** — collapsing them into one shared `tests/support/dbHarness.ts` is a good idea in isolation (it would cut ~1400 lines to maybe 250 plus 9 one-line `db-prefix` configs) but is exactly the kind of cross-cutting change that will conflict with whoever is actively adding a 10th test file against one of the existing 9 patterns today. Recommend queuing this for a dedicated, coordinated pass once the parallel build settles, not as an incremental patch.

### 12. Inline millisecond arithmetic instead of `src/lib/time.ts`'s helpers

`addHours`/`addDays`/`hoursBetween` (`src/lib/time.ts:52-62`) exist and are used correctly in several places (`dateProposal.service.ts:526`, `conversation.service.ts:281`), but the following re-derive the same arithmetic inline instead of calling them — mathematically identical (plain UTC millisecond math, no DST/timezone subtlety to get wrong), so **not a divergence risk**, just avoidable repetition:

- `src/services/report.service.ts:289,546`
- `src/services/message.service.ts:251,262`
- `src/services/trust.service.ts:206,274` (same `CLEAN_RECORD_LOOKBACK_DAYS` computation, copy-pasted twice in the *same file*)
- `src/services/interest.service.ts:342`
- `src/services/auth.service.ts:454,505`
- `src/http/routes/dates.routes.ts:40`

Consolidation step: swap each for the equivalent `addHours(date, -n)`/`addDays`/`hoursBetween` call. Trivial, no behavior change; do file-by-file as those files are touched for other reasons rather than as a standalone sweep across many owners' files.

### 13. Checked and found clean — no action needed

- **Id generation:** `src/lib/ids.ts#newId()` is the sole `randomUUID()` wrapper; no `src/**` file calls `randomUUID()` directly, bypassing it.
- **Error hierarchy:** single `AppError` class tree in `src/lib/errors.ts`; no parallel ad-hoc error-shaping found elsewhere.
- **Eligibility/filter evaluation:** genuinely single-sourced. `discovery.service.ts:5,286,434` and `eligibility.service.ts` both call `filter.service.ts#passesMutualFilters` directly (confirmed by import); `interest.service.ts:66` explicitly documents wrapping it "never a second, divergent" copy.
- **Privacy serializers:** `profile.ts`, `discovery.ts`, `matches.ts`, `timeline.ts`, `venue.ts`, `user.ts` all use an explicit-allowlist pattern (never `{...spread}`), consistently, and all routes that return these types go through the corresponding serializer (checked every `reply.send(...)` call site in `src/http/routes/*.ts`). The trust-score gate (finding 1) is the one exception to this otherwise-clean picture.

---

## Consolidation worklist, ordered by risk reduced per unit of effort

1. **Fix `message.service.ts#linkLimitForCaller` to call `trust.service.ts#linksPerHourLimitFor`** (finding 2). One line changed, one file, fixes a self-documented known-bad pattern, add one test. **Safe to do now** — single-file, no cross-agent surface.
2. **Fix trust-score exposure gate** (finding 1): delete the unused `shouldExposeRawTrustScore`/`trust.expose_raw_score` config key (or wire it in — pick one), update `decisionsConfig.test.ts`. Small, contained to `trust.service.ts` + `config.service.ts` + one test file. **Safe to do now.**
3. **Fix `voucher.service.ts`'s expiry boundary operator** (finding 5) to match the inclusive convention used elsewhere. One line. **Coordinate with the voucher-expiry owner** since it touches a job path someone may be actively testing.
4. **Extract shared cursor encode/decode + validation helper** (findings 3+4+8) and point notification/message/interest at it (fixes the 500-vs-400 gap immediately), then migrate matches/timeline (behavior-preserving), then evaluate converting trust/moderation/venueSettlement from offset to keyset. Medium effort, high payoff (closes an availability inconsistency and a correctness inconsistency in one extraction). **Do the validation-only part now** (low risk); treat the offset→keyset conversions as a separate, larger follow-up since they change response semantics for those three endpoints' `nextCursor` values (opaque cursor vs a client-visible integer today) — check no client/test currently parses those cursors as integers before changing the format.
5. **Add a cross-check test between `filter.service.ts#haversineKm` and `distance.ts`'s internal exact formula** (finding 7). Pure test addition, zero production risk, cheap insurance against a repeat of the original SAF-2 failure mode.
6. **Extract `percentOfCents` to a shared money module** (finding 9). Small, safe, pre-emptive.
7. **Add the "run both compatibility-scoring systems side by side, document the delta" test** (finding 6). This is *not* a fix — do not wire `scoreQuestionContribution` into `compatibility.service.ts` as part of this pass. It's scoped here only as the safety net that should exist *before* whichever future agent does that integration, since the two algorithms are not equivalent and that integration is explicitly invited by existing code comments.
8. **Test harness consolidation** (finding 11) and **inline time-arithmetic cleanup** (finding 12): lowest priority, **defer** — both are real but low-severity DRY issues, and 11 in particular touches files that are, per their own doc comments, live per-agent editing territory right now. Revisit once the parallel build phase ends.

**Explicitly unsafe to attempt while other agents are still editing:** the test-harness merge (11) and the offset→keyset pagination conversions for `trust.service.ts`/`moderation.service.ts`/`venueSettlement.service.ts` (part of 4) — both touch files with active, wide blast radius across many other in-flight test/route changes. Everything else in the worklist above is scoped to one or two files each and should be safe to land independently.
