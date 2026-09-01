# Scale and Sources of Truth

Analysis of `outcome-dating` as implemented (not as specified), answering three
questions from the product owner. Read-only review; no code was changed.

**Method.** Every claim about behavior cites a file and line. Every number is
either counted directly from the schema/code, or is an explicit estimate —
estimates are always labeled "estimate" and show the assumption behind them.
"Breaks" means: fails outright (timeout, OOM, storage exhaustion), or degrades
past the point of being a usable product, whichever comes first.

---

# Part 1 — Can the app scale?

## 1.0 Answer, up front

The app cannot scale to national size on its current architecture, and the
reason has almost nothing to do with the 8-billion-user framing in the
question. **It breaks at a few thousand to low tens-of-thousands of active
users in one metro area** — an order of magnitude below what a single
successful city launch would produce — because the discovery grid and the
"reality dashboard" evaluate every eligible user on the platform, one at a
time, over sequential database round trips, for every single request. The
pairwise compatibility-score table is a second, independent, more famous
kind of O(n²) problem, but it breaks later than discovery does and would
never be reached in practice because discovery falls over first.

Underneath both problems is the same root cause: **the app never narrows by
geography**. A dating app is local — two users 4,000km apart are not
candidates for each other — but nothing in the schema or the query layer
expresses that. Every query that should say "users near me" instead says
"users," full stop, and then filters down in application code, row by row,
after the fact. That is why global scale and national scale are not "the
same problem, bigger" here: national scale is already broken at the point
where a naive geo-sharded design would still be comfortable, because the
unbounded-scan problem exists per-city, not just in aggregate.

| Breaks first | Approx. scale (estimate) | Why | Category |
|---|---|---|---|
| Discovery grid (`GET` the swipe/browse feed) | ~2,000–20,000 active users in one pool (no geo narrowing, so this is closer to total active users than to a city's population) | Unbounded candidate scan + fully serial per-candidate DB round trips (§1.1) | **Needs a change now** |
| Reality dashboard (`GET /me/reality-dashboard`-shaped call) | Lower than discovery — scans literally every active user on the platform with no gating at all (§1.1.3) | Same pattern, weaker pre-filter | **Needs a change now** |
| Nightly compatibility refresh job | Somewhere between ~3,000 and ~10,000 total active users, the job stops finishing within its 24h window (§1.2.2) | O(n²) pairs, each pair costs 2 sequential writes | **Needs a change before growth** |
| `compatibility_scores` storage | ~100,000 users ≈ ~1.75TB (estimate); ~1,000,000 users ≈ ~175TB | O(n²) row count, no geographic partitioning | **Needs a change before growth** |
| Single Postgres write throughput / connection budget | High tens of thousands to low millions of users, depending on request mix | `max: 10` pool, single primary, no read replica, no partitioning (§1.5) | **Needs a change before growth** |
| In-process rate limiter / job scheduler / config cache | Breaks correctness (not availability) the moment there is more than one app instance | No shared state across instances (§1.6) | **Needs a change before growth** (as soon as you horizontally scale the app tier at all — plausibly before national scale, since it's what you'd reach for to fix the above) |
| Fundamental pairwise-materialization architecture | 100M–8B | No amount of tuning saves an O(n²) design at billions of rows; requires geographic sharding + on-demand scoring within a local candidate set, never global materialization | **Rearchitecture** |

The rest of Part 1 works through each row with the numbers behind it.

## 1.1 Discovery: the actual first bottleneck

### 1.1.1 The candidate pool has no upper bound and no geography

`loadCandidatePool` (`src/services/discovery.service.ts:146-177`) is the
query behind every discovery-grid request:

```sql
SELECT u.id, u.trust_score, ... FROM users u
JOIN profiles p ON p.user_id = u.id
LEFT JOIN user_photos ph ON ...
WHERE u.id <> $1
  AND u.status = 'active'
  AND p.profile_completeness >= $2       -- default 50, config-driven
  AND EXISTS (approved photo)
  AND NOT EXISTS (blocked either direction)
```

There is no `LIMIT`, no distance clause, no city/region predicate — nothing
that scopes the query to "people near the viewer." `profiles.latitude` /
`profiles.longitude` exist (`db/migrations/001_init.sql:86-87`) and
`profiles.city` has an index (`idx_profiles_city`,
`db/migrations/001_init.sql:97`), but neither is referenced by this query,
by `getRealityDashboard`, or by the nightly compatibility refresh. **This is
the single biggest scalability defect in the codebase**: on a platform of N
active users who mostly satisfy the weak completeness/photo/block gate
(which is most of them, by design — those are onboarding checks, not
matching checks), the candidate pool returned to `computeRankedCandidatePool`
is proportional to N, not to "people in this city."

A dating app with users in 50 different countries should have candidate
pools bounded by "this city" (thousands), not "this platform" (hundreds of
millions). Nothing in the code makes that distinction.

### 1.1.2 The pool is then walked one row at a time, over the network

`computeRankedCandidatePool` (`discovery.service.ts:256-331`) takes the
unbounded pool and, for **each** survivor, sequentially awaits (not
`Promise.all`'d across candidates — a single `for` loop, `discovery.service.ts:278-295`):

1. `isVisibleInDiscovery(ctx, row.id)` — 1 query (`moderation.service.ts:367-375`).
2. `passesMutualFilters(ctx, viewerId, row.id)` (`filter.service.ts:462-468`),
   which runs `subjectPassesFiltersOf` in both directions. Each direction
   issues 1 query for the filter owner's `hard_filters` rows
   (`filter.service.ts:442-445`), then **one further query per enabled
   filter**, sequentially, inside a `for` loop with `await`
   (`filter.service.ts:446-453`) — `resolveAttributeValue` re-queries
   `profiles` or joins `answers`↔`questions` by slug per filter key
   (`filter.service.ts:371-424`, `loadSelfAnswerBySlug` at `:358-368`).
3. `resolveVisibleTagsFor(ctx, viewerId, row.id)` for survivors only — 1-2
   more queries (`question.service.ts:363-394`).

None of this batches across candidates. A viewer with F enabled hard filters
costs roughly `2 + 2×(1+F)` sequential round trips **per candidate in the
pool**, and the whole discovery grid pays this cost even though only 20-100
results are ever returned (`DEFAULT_PAGE_LIMIT`/`MAX_PAGE_LIMIT`,
`discovery.service.ts:112-113`) — pagination slices the fully-computed,
fully-sorted array after the fact (`discovery.service.ts:360`), so it buys
nothing at the DB layer.

*(Note: the five aggregate lookups just before this loop — pending-interest
counts, active-conversation counts, response rates, viewer profile, viewer
tags — are properly batched with `= ANY($1::uuid[])`,
`discovery.service.ts:179-247`. That part of the file is written correctly;
it's the per-row gating loop that isn't.)*

**Estimate** (F = 3 filters, a realistic average; 1ms/round-trip, which is
optimistic even for a local, uncontended Postgres):

| Pool size (≈ eligible users, no geo bound) | Round trips per request (≈5×pool) | Wall time (estimate, 1ms/RT) |
|---|---|---|
| 500 | 2,500 | 2.5s |
| 2,000 | 10,000 | 10s |
| 10,000 | 50,000 | 50s — exceeds typical HTTP/gateway timeouts |
| 100,000 | 500,000 | ~8.3 min — request fails outright |

At 1ms/round-trip these numbers are already unusable past a couple thousand
candidates; real network/Postgres latency (even same-AZ) is commonly 2-5x
that, so in practice the failure point is likely lower, not higher, than
this table suggests. And because each in-flight discovery request holds
onto a connection from the pool (`max: 10`,
`src/db/pool.ts:12-16`) for its entire multi-second-to-minutes duration, **10
concurrent discovery requests exhaust the whole application's DB connection
budget** — every other endpoint (login, messaging, payments) queues behind
them. This is not a discovery-only outage; it's a whole-app outage caused by
one endpoint.

### 1.1.3 The reality dashboard is worse

`getRealityDashboard` (`discovery.service.ts:367-375`) additionally calls
`countUsersMatchingMyFilters` / `countUsersWhoseFiltersIMatch`
(`filter.service.ts:479-496`). Both start from `listOtherActiveUserIds`
(`filter.service.ts:470-476`) — **every active user on the entire platform,
with no completeness/photo/block/geo gate at all** — then loop, sequentially,
calling `subjectPassesFiltersOf` per user (same per-filter query cost as
above). `previewPoolSizeWithUnsetPolicy` (`filter.service.ts:518-532`) does
the identical unbounded full-platform scan every time a user previews a
filter-strictness toggle in the UI. These three entry points scan strictly
more rows than discovery does (no weak gate to shrink the pool at all), so
whatever user count breaks discovery breaks these sooner.

### 1.1.4 Fix, ranked by headroom-per-effort

1. **Add a geographic pre-filter to `loadCandidatePool`, `listOtherActiveUserIds`,
   and the compatibility refresh's user list** (a bounding box on
   `latitude`/`longitude`, or a `city`/region column, indexed). This alone
   turns an O(platform) scan into an O(city) scan and is the single highest-leverage
   change available — it fixes discovery, the dashboard, and shrinks the
   compatibility problem in Part 1.2 by the same factor, all from one change.
2. **Batch the per-candidate gating loop.** `isVisibleInDiscovery` and the
   hard-filter-owner lookups can be turned into `= ANY($1::uuid[])` batch
   queries exactly like the five aggregates already above them in the same
   file — this requires no schema change, just rewriting three functions to
   take a candidate-id array instead of being called in a loop.
3. **Cap the pool with `LIMIT` at the SQL level** (order by something
   indexed — e.g. `last_active_at DESC` — before doing any per-row work), so
   a request never evaluates more candidates than it could possibly need for
   one page, instead of computing and sorting the entire eligible population
   and discarding all but 20-100 of them.
4. Add an actual index usable for filter attribute resolution: today
   `resolveAttributeValue`'s default case joins `answers`↔`questions` by
   slug per filter, per candidate (`filter.service.ts:358-368`,
   `421-423`) — `idx_answers_question_id` exists
   (`db/migrations/001_init.sql:177`) but there's no `(user_id, question_id)`-shaped
   index serving this exact lookup pattern beyond the table's own PK, which
   does serve it — the real fix here is (2), batching, not indexing; the
   query plan per call is already fine, there are just too many calls.

## 1.2 Compatibility scoring: real, but not the first thing to break

### 1.2.1 The materialization is genuinely O(n²)

`compatibility_scores` (`db/migrations/001_init.sql:241-250`) has primary
key `(user_id, candidate_id)` and is populated, **for both directions of
every pair**, by `refreshAllScores`'s nested loop
(`compatibility.service.ts:344-374`): for `i < j` it computes one score and
calls `upsertScore` twice — once as `(idA, idB)`, once as `(idB, idA)`
(`compatibility.service.ts:368-369`). For N active users that is `N×(N-1)`
stored rows and the same number of sequential `INSERT ... ON CONFLICT`
round trips (each `upsertScore` call is awaited individually inside the
loop, not batched — `compatibility.service.ts:252-261`, `368-369`).

**Storage, estimate** (uuid PK ≈ 32 bytes + `score` float8 (8B) +
`computed_at` timestamptz (8B) + per-row heap overhead, plus the PK btree
and the `idx_compatibility_scores_user_score` secondary index — roughly
150-200 bytes of total on-disk footprint per stored pair, generously):

| Active users (N) | Ordered pairs `N(N-1)` | Storage (≈175B/row, estimate) |
|---|---|---|
| 10,000 | ~1.0×10⁸ | ~17.5 GB |
| 100,000 | ~1.0×10¹⁰ | ~1.75 TB |
| 1,000,000 | ~1.0×10¹² | ~175 TB |
| 100,000,000 | ~1.0×10¹⁶ | ~1.75 exabytes — not a storage problem anymore, a "this cannot exist" problem |
| 8,000,000,000 | ~6.4×10¹⁹ | meaningless at this point — more rows than exist in any production OLTP system on Earth |

**Refresh runtime, estimate** (1ms/round-trip, generous; two sequential
writes per pair, plus N sequential reads up front to load every user's
answers into memory — `compatibility.service.ts:351-354`):

| Active users (N) | Sequential write round trips (`2×pairs`) | Estimated wall time |
|---|---|---|
| 1,000 | ~999,000 | ~17 min — plausibly fits a nightly window |
| 3,000 | ~9.0×10⁶ | ~2.5 hours |
| 10,000 | ~1.0×10⁸ | ~27.8 hours — **already exceeds 24h; the "nightly" job cannot complete before the next one is due** |
| 100,000 | ~1.0×10¹⁰ | ~115 days |

The job is idempotent and lock-guarded (`src/jobs/scheduler.ts:37-41`,
`60-88`), so an overrun doesn't corrupt anything — it just means the
platform's compatibility scores get **permanently stale** somewhere between
3,000 and 10,000 active users, well before storage becomes the binding
constraint. The synchronous per-answer refresh path
(`question.service.ts` → `compatibility.refreshScoresForUser`,
noted in `compatibilityRefresh.job.ts`'s own doc comment) recomputes one
user against every other active user on every answer change
(`refreshScoresForUser`, `compatibility.service.ts:333-341` — same
unbounded, non-geo-scoped `SELECT id FROM users WHERE status='active'`) —
this is a second O(N) cost triggered synchronously inside a user-facing
write path, and it gets slower in lockstep with the nightly job as N grows.

`getScoresForCandidates` (`compatibility.service.ts:294-322`, the function
discovery actually calls per request) is properly batched for the *read*
(`= ANY($1::uuid[])`, `compatibility.service.ts:302-305`) but still issues
**one `upsertScore` write per candidate, sequentially, inside a `for` loop**
(`compatibility.service.ts:314-319`) as a side effect of every discovery
request — this rides along with, and adds to, the 1.1.2 per-candidate cost
already described.

### 1.2.2 Why this isn't actually the first thing to break

Because discovery's pool query (1.1.1) has no `LIMIT` and no geo bound
either, in practice you hit the discovery/dashboard wall (low thousands of
candidates, multi-second to multi-minute requests, connection-pool
exhaustion) well before the nightly compatibility job's 24-hour SLA breaks
(mid-single-digit-thousands to low tens-of-thousands of users). Fixing 1.1's
geographic narrowing also fixes this: if the refresh job is rewritten to
recompute scores only within a geographic neighborhood (see 1.4 fix #1
below), N in the formulas above becomes "active users in this metro," not
"active users on the planet," and the O(n²) cost becomes tractable again at
every scale that matters — this is the crux of "matching is local, not
global."

### 1.2.3 Fix, ranked

1. **Stop materializing all pairs.** The spec itself says "For MVP, compute
   score on demand for candidates" (§16.3, cited in
   `compatibility.service.ts:264-271`) — the nightly full materialization
   contradicts that MVP framing and is the part that doesn't scale. Compute
   on demand for the (already geo-narrowed, per fix 1.1.4-#1) candidate
   pool only, and drop the nightly all-pairs job entirely once discovery
   never needs it.
2. **If a precomputed table is kept**, key it by geography (partition
   `compatibility_scores` or shard by region) so a refresh only ever touches
   one metro's user count, not the whole platform's.
3. **Batch `upsertScore`** into a single multi-row `INSERT ... ON CONFLICT`
   per call to `getScoresForCandidates`/`refreshAllScores`, instead of one
   round trip per row — cuts the write cost by roughly the candidate-page
   size even before the architectural fix.

## 1.3 Geography is not exploited anywhere — the root cause

Confirmed absence, not inference: the only Postgres extension loaded is
`pgcrypto` (`db/migrations/001_init.sql:18`) — no PostGIS, no
`earthdistance`/`cube`, no `ll_to_earth`, no `ST_*` call anywhere in the
migrations or source tree. `profiles.latitude`/`longitude` are plain
`double precision` columns with **no index at all** — the only index touching
location-adjacent data is `idx_profiles_city` on the raw text `city` column
(`001_init.sql:97`), and even that index is never referenced by a `WHERE
city = ...` predicate anywhere in `discovery.service.ts` or
`filter.service.ts` — distance is only ever computed in application code,
after every candidate row has already been pulled across the network
(`haversineKm`, `filter.service.ts:347-356`; `haversineKmExact`,
`domain/units/distance.ts:162-169`).

This is the throughline for nearly every scale finding in this document:
**a dating app's core operation — "who is near me" — is implemented as "who
exists," filtered client-side-in-the-app-server, rather than as a bounded,
indexed spatial query.** A geographically-sharded or geo-indexed design
would make almost every number above dramatically better, because the
relevant N for any one query would be "people in commuting distance," which
does not grow no matter how large the platform gets globally — that's
exactly why "global scale" and "national scale" are different problems for
a local-matching product: a correct design's per-query cost is *flat* as
total users grow past the size of one metro area, and this codebase's
per-query cost is linear (or worse) in *total platform users* regardless of
where anyone lives.

## 1.4 Background jobs: full-table sweeps

| Job | Interval | What it scans | Growth |
|---|---|---|---|
| `compatibility_score_refresh` | 24h | Every active-user pair (§1.2) | O(N²) — breaks first among the jobs, ~3k-10k users |
| `trust_score_recalculation` | 15min | `SELECT DISTINCT user_id FROM trust_events`, then one `recalculateTrustScore` call per user, sequentially (`trustRecalculation.job.ts:29-34`) | O(N) sequential DB round trips every 15 minutes; at large N this simply can't finish inside its own interval, causing runs to pile up (each skipped by the advisory lock, so trust scores lag further and further behind) |
| `moderation_score_recalculation` | 15min | `SELECT DISTINCT user_id` over `automated_moderation_flags UNION reports.reported_id`, then one `applyThresholds` call per user, sequentially (`moderation.service.ts:376-389`) | Same shape and same eventual failure mode as trust recalculation |
| `chat_decay`, `interest_expiry`, `date_proposal_expiry`, `voucher_expiry` | 5-15min | Single indexed `UPDATE ... WHERE status = X AND <partial index predicate>` (e.g. `idx_interests_expiry_job`, `idx_date_proposals_expiry_job`, `db/migrations/001_init.sql:279,424`) | These are the well-designed jobs in the file — one indexed set-based UPDATE, no per-row loop. They scale fine. |
| `payment_reconciliation` | 30min | Delegates to `ledger.service#reconcileWithProcessor` — not walked in this review, but structurally reads recent ledger/hold rows, not all-time/all-user | Not flagged as a concern here |
| `photo_ab_stats` | 60min | Per-user recompute for users with ≥3 approved photos and the flag on — bounded by opted-in population, not total users | Lower risk; still worth batching if the opted-in population gets large |

The pattern to notice: jobs that were written as **one indexed, set-based SQL
statement** (expiry jobs) don't have a scaling problem at all. Jobs written
as **"select a list of ids, then loop calling a per-user service function"**
(trust/moderation recalculation, and compatibility refresh) all degrade the
same way — O(N) or O(N²) sequential round trips — and all three will
eventually stop completing inside their own scheduling interval as the user
base grows, silently making the state they maintain (trust scores,
moderation actions, compatibility scores) increasingly stale rather than
throwing an error anyone would notice. Since the advisory lock
(`src/jobs/scheduler.ts:37-41`) makes an overrunning job's next tick a
silent no-op skip (`scheduler.ts:60-64`), there is **no alarm** built into
this design for "the nightly job hasn't actually completed in three days" —
that would need to be added as monitoring, because the code will not surface
it on its own.

## 1.5 Single Postgres instance

`getPool()` (`src/db/pool.ts:9-19`) is a single hardcoded `pg.Pool` with
`max: 10` connections, built once per process, no read/write split, no
replica awareness. Concretely:

- **Connection budget.** 10 connections per app instance is fine for normal
  CRUD traffic but is trivially exhausted by the discovery pathology in
  §1.1 (one discovery request can occupy a connection for multi-second to
  multi-minute stretches). This is a config knob (raise `max`), but raising
  it just delays the same collapse — the actual fix is §1.1.4, not a bigger
  pool.
- **Write throughput.** Every write in this app (interests, messages,
  payments, trust events, moderation flags) goes to one primary. Nothing in
  the schema partitions any high-volume table (`messages`, `trust_events`,
  `discovery_events`, `notification_outbox`) by time or by user shard —
  these will need range/hash partitioning (e.g. `messages` by month,
  `discovery_events` by month — it is pure event/impression volume with no
  update path) well before a single Postgres primary's write IOPS becomes
  the binding constraint, likely in the high-tens-of-millions-of-users
  range for a chat-heavy product, though this review did not attempt to
  size that precisely (estimate, unmeasured).
- **Index size vs. memory.** Every table in `001_init.sql` gets several
  btree indexes (e.g. `messages` has two, `interests` has four,
  `date_proposals` has five). At the scales discussed here for the O(n²)
  tables (§1.2), the indexes on `compatibility_scores` alone would be
  hundreds of GB to low TB before the base table itself is even considered
  — well past what fits in RAM on any single instance, meaning index
  lookups that are currently cache-resident become disk-bound, silently
  multiplying every latency number in §1.1-1.2 by an unestimated but
  substantial factor. This reinforces §1.2's core point: the pairwise table
  must not be allowed to grow to platform-wide N in the first place.
- **Read replicas.** Nothing in the codebase issues a read against anything
  but the primary (`ctx.db` is always the same pool/client,
  `src/db/pool.ts:35`, `src/lib/ctx.ts`) — there is no read/write split to
  even offload the (already too expensive) discovery reads to a replica.
  This would help absolute throughput once §1.1's per-query cost is fixed,
  but would not fix the per-query cost itself — it is a multiplier on a
  currently-broken baseline, not a substitute for fixing §1.1.

**When this matters relative to §1.1/§1.2:** not first. The app will already
be unusable (§1.1) or silently stale (§1.2/§1.4) at a small fraction of the
user count where "one Postgres primary" itself becomes the bottleneck. Put
this in the "needs a change before growth" bucket, after the query-shape
fixes, not before them — buying more Postgres does not fix an O(pool-size)
sequential-round-trip request handler.

## 1.6 In-process / single-instance state (breaks horizontal scaling of the app tier itself)

Three pieces of process-local state are explicitly documented as an MVP
tradeoff ("no Redis") and are each a hard blocker the moment more than one
app instance runs, independent of user count:

1. **`InMemoryRateLimiter`** (`src/http/rateLimit.ts:39-65`) — a per-process
   `Map<string, Bucket>` (`:40`). With N app instances behind a load
   balancer, a client gets N independent rate-limit budgets instead of one
   — the limiter's entire purpose (stopping brute-force/enumeration abuse,
   per the file's own doc, `rateLimit.ts:11-22`) is defeated by horizontal
   scaling, not merely made less accurate. It is also unbounded: `buckets`
   is never evicted except by a key's own window rolling over
   (`rateLimit.ts:48-49`) — a flood of distinct IPs/keys grows this Map
   without limit, a slow memory leak under adversarial or just high-cardinality
   traffic. **This needs a shared store (Redis or equivalent) before running
   more than one instance, which will be needed for far lower user counts
   than anything in §1.1-1.2 — it's an availability/scaling-of-the-app-tier
   issue, not a data-scale issue.**
2. **`JobScheduler`** (`src/jobs/scheduler.ts:43-109`) — this one is
   actually **safe** for multiple instances: each tick takes a Postgres
   advisory lock (`pg_try_advisory_lock`, `scheduler.ts:37-41,60-64`), so
   running the scheduler on every instance is correct (only one instance's
   tick wins the lock and executes) — the bottleneck here is the job
   bodies themselves (§1.4), not the scheduling mechanism. Worth noting as
   a place the codebase got the multi-instance story right.
3. **`ConfigService`'s in-memory cache** (`src/config/config.service.ts:403,412-435`)
   — explicitly documented as out of scope for multi-instance coherency
   (`config.service.ts:459-462`): an admin's `PATCH /admin/config` change
   is invalidated on the instance that handled the write, but every other
   running instance keeps serving its stale cached value indefinitely (no
   TTL, no pub/sub invalidation) until that instance happens to restart or
   otherwise clears its cache. At small scale (one instance) this is a
   non-issue; the moment the app tier is horizontally scaled for the
   traffic reasons in §1.1/§1.5, this becomes a real correctness bug —
   different servers answering discovery requests under different
   effectively-active business rules (interest caps, escrow amounts, trust
   thresholds) at the same time.

## 1.7 Hot spots and skew

- **The incoming-interest cap as an accidental hot row/table.** Every
  discovery request computes, per candidate, `count(*) FROM interests WHERE
  recipient_id = X AND status = 'pending'` (batched correctly here via
  `loadPendingIncomingCounts`, `discovery.service.ts:179-189`, and again
  per-candidate inside `isProfileVisibleTo`, `discovery.service.ts:420-425`).
  For an unusually popular recipient (the classic dating-app power-law: a
  small number of profiles receive a hugely disproportionate share of
  interest), this is a `COUNT` against a growing slice of the `interests`
  table for that one `recipient_id`, re-run on every single other user's
  discovery/dashboard request that includes them in the candidate pool —
  i.e. popularity multiplies read load on that user's row set, not just
  write load. `idx_interests_recipient_status`
  (`db/migrations/001_init.sql:277`) keeps any *one* such count cheap, but
  the aggregate load from thousands of *other* users' requests all touching
  the same popular recipient's index range concurrently is a classic
  hot-partition pattern this schema has no mitigation for (no caching of
  the count, no denormalized counter column).
- **Dense cities.** Because nothing pre-filters by geography (§1.3), a
  dense city doesn't even get to be a "hot spot" in the usual sense — its
  users are simply indistinguishable, at the query layer, from the rest of
  the global user base. Every request pays the full-platform cost described
  in §1.1 regardless of how concentrated demand actually is; there's no
  per-city sharding to even observe a hot city separately from a quiet one.
- **`notification_outbox` coalescing.** A single very-active conversation
  or a broadcast-style event could grow `notification_outbox` rows for one
  `(user_id, coalescing_key, channel)` group quickly, but the schema does
  coalesce them (`coalesced_count`, `db/migrations/011_notifications.sql:143`)
  rather than fanning out one row per event — this one is handled
  correctly and isn't flagged as a risk.

## 1.8 Scale table: 10K / 1M / 100M / 8B

| Scale | Status | First failure |
|---|---|---|
| **10,000 users** | Already broken today for two independent reasons at this size: discovery requests taking seconds-to-tens-of-seconds and eating the entire connection pool (§1.1.2), and the nightly compatibility refresh no longer completing inside 24h (§1.2.1). A single Postgres primary itself is nowhere near its limits at this size — that is not what fails first. |
| **1,000,000 users** | Discovery/dashboard are unusable long before this point (already broken at 10K). If those were magically fixed with a geo-bound but the pairwise table were *not* also fixed, `compatibility_scores` storage alone reaches ~175TB (estimate, §1.2.1) — infeasible regardless of query performance. This is the scale at which "materialize every pair" must already be gone, replaced by geo-scoped on-demand scoring. |
| **100,000,000 users** | Meaningful only if geography is exploited (§1.3) — a global platform at this size is really "many independent metro-scale matching pools." If it is, the per-query cost for any one user is still bounded by their metro's population, and the remaining question is standard large-system engineering: partitioning `messages`/`trust_events`/`discovery_events` by time, sharding by region, read replicas per region (§1.5) — real work, but conventional, not a fundamental redesign. If geography is *not* exploited by then, none of this matters because the app already failed at 10,000-1,000,000 users. |
| **8,000,000,000 users (literally everyone)** | Not a "bigger version" of the 100M case — it requires the matching problem to be decomposed by geography from the start, because no plausible sharding-of-a-non-local-problem survives this size (§1.2.1's 8B row shows why: even a correctly-executed *global* pairwise approach is off the table by many orders of magnitude). At true planetary scale the only sane architecture is per-region (or per-city) independent deployments/shards of a *bounded-N* matching system, tied together only for account/auth/cross-region-move concerns — i.e. the product's own premise ("go on a real date nearby") is the thing that makes this tractable, if the implementation actually leaned on it. Today's implementation does not. |

## 1.9 Fixes, ranked by headroom bought per unit of engineering effort

1. **Geo-bound the three unbounded scans** (`loadCandidatePool`,
   `listOtherActiveUserIds`, the compatibility refresh's user list) —
   single highest-leverage change; turns three O(platform) problems into
   O(city) problems at once. *(Needs a change now.)*
2. **Batch the per-candidate discovery gating loop** (visibility check,
   hard-filter resolution) the same way the five aggregate lookups already
   above it are batched. *(Needs a change now.)*
3. **Stop materializing all-pairs compatibility scores; compute on demand
   for the (now geo-bound) candidate pool only**, per the spec's own MVP
   framing. Retire the nightly full-refresh job. *(Needs a change before
   growth — buys the headroom described in §1.2.3, and removes the largest
   storage/runtime risk in the codebase.)*
4. **Move the rate limiter to shared storage** before running more than one
   app instance — required for horizontal scaling of the app tier itself,
   independent of user count. *(Needs a change before growth.)*
5. **Partition high-volume append-only tables** (`messages`,
   `trust_events`, `discovery_events`, `notification_outbox`) by time once
   write volume approaches single-primary limits; add read replicas once
   the (by-then-fixed) discovery/dashboard queries need more read
   throughput than one primary provides. *(Needs a change before growth,
   later than the above.)*
6. **Give the trust/moderation recalculation jobs a bounded, indexed,
   set-based rewrite** (or at minimum batch their per-user work) so they
   stop degrading the same way the compatibility job does. *(Needs a change
   before growth.)*
7. **Region-shard the whole matching subsystem** once a single region's
   Postgres, even correctly geo-bound and partitioned, can no longer serve
   its own metro's write/connection load. *(Rearchitecture — this is what
   "8 billion users" actually requires, and it is a natural consequence of
   fix #1 done thoroughly, not a separate idea bolted on later.)*

---

# Part 2 — Is the demo data actually swappable for real data?

## 2.0 Answer, up front

Partially, and the parts that aren't are the parts that would embarrass
someone on launch day. Seed data itself (fake users, demo venues, the old
question bank) is cleanly isolated and swappable through existing admin
APIs or trivial deletion. **The payment processor and the photo/content
moderation system are a different story: one silently no-ops in production
if misconfigured, and the other has no real implementation or configuration
switch at all — it is not "demo data" that needs swapping, it is a stub
standing in for a feature that was never built.**

## 2.1 Seed data isolation — the good news

`src/seed.ts` is a standalone CLI command (`node dist/index.js seed`,
wired in `src/index.ts:20,60,118`), never imported by `src/services/**` or
`src/http/**` (confirmed by repo-wide search — the only importer is
`src/index.ts`). It writes directly via raw SQL rather than through the
service layer (`seed.ts:1-9`), so there is no service-layer code path that
depends on it existing or running. Seeded users use a single, greppable
domain, `@seed.outcome-dating.test`
(`seed.ts:1064`) — a clean, mechanical way to identify and delete every
seeded account (`DELETE FROM users WHERE email LIKE '%@seed.outcome-dating.test'`;
`ON DELETE CASCADE` from `users` cleans up profiles, photos, answers,
filters, tags, interests, etc. automatically per the FK definitions in
`001_init.sql`). No hardcoded seed IDs, secrets, or fixture values were
found reachable from any production code path — the only other place a
default secret lives is `src/config/env.ts` (§2.4 below), which is a
deployment-config issue, not a seed-data leak.

`tests/**` and `src/services/notifications/testSupport.ts` (the one
test-support module that lives outside `tests/`, by explicit design —
`testSupport.ts:1-12`) are likewise not imported by any server/job code
path (confirmed by repo-wide search for `testSupport`/`testHarness`/`testCtx`
outside the `tests/` directory and the one file itself). **No test-only
helper is reachable from the running server.**

## 2.2 The fake payment processor — the biggest launch-day risk

`buildDeps` (`src/http/deps.ts:59-60`) selects the payment adapter with:

```ts
const payments = overrides?.payments ??
  (env.PAYMENT_PROCESSOR === 'stripe' ? new StripeProcessor(env.STRIPE_SECRET_KEY) : new FakeProcessor());
```

`PAYMENT_PROCESSOR` (`src/config/env.ts:32`) **defaults to `'fake'`** if the
environment variable is absent, misspelled, or simply not set by whoever
provisions the production environment. There is no `NODE_ENV === 'production'`
guard anywhere that refuses to start, or even warns, if the fake processor
ends up selected outside development/test. Two concrete failure modes:

1. **`PAYMENT_PROCESSOR` unset or wrong in production** → the app runs
   normally, escrow holds "succeed," dates get "ticketed," venue payouts get
   computed and recorded in `payment_ledger` — and **no real money ever
   moves**, silently, with a fully green `payment_reconciliation` job
   (there's nothing to reconcile against because `FakeProcessor` never
   talks to a real processor and never contradicts its own ledger). This is
   the single worst outcome available: a financially-fabricated production
   system that looks correct in every log and every admin dashboard.
2. **`PAYMENT_PROCESSOR=stripe` set correctly** → every call throws.
   `StripeProcessor` (`src/services/payments/stripe.processor.ts:30-95`) is
   a **documented stub** — the `stripe` npm package is not even a dependency
   (`package.json` dependencies list: `bcryptjs`, `fastify`, `pg`, `zod` —
   no `stripe`) — every method (`authorize`, `capture`, `cancel`, `refund`)
   throws `NotImplementedError` unconditionally. The detailed JSDoc on each
   method (`stripe.processor.ts:35-51`, etc.) is a *spec for a future
   implementation*, not working code. Setting the "correct" production
   config crashes every date-proposal payment flow on first use.

There is no configuration value that produces working real payments today.
**This is not a "swap the demo data" task — it requires writing and testing
a real Stripe integration from the documented contract, which does not
currently exist in any form.**

## 2.3 The media/content moderation stub — not even config-gated

`buildDeps` (`deps.ts:58`) hands out `new StubMediaModerationAdapter()`
**unconditionally** — there is no environment variable, no config key, and
no alternate implementation anywhere in the tree (`grep` for `implements
ImageModerationPort` across `src/` returns exactly the one stub file). The
stub's entire "analysis" is a deterministic function of the **image URL
string** (`src/services/media/stub.adapter.ts:11-19`): it flags nudity only
if the URL literally contains the substring `"nsfw"`, weapons only if it
contains `"weapon"`, illegal content only if it contains `"illegal"`, a
missing face only if it contains `"noface"` — anything else, including any
real photo a real user uploads to a real CDN URL in production, **is
approved by default** (`stub.adapter.ts:49-56`). There is no ML model, no
third-party vision API call, no dependency capable of doing one
(`package.json` has no vision/moderation SDK either). This is not "demo
data that needs swapping" in the same sense as the seed users or venues —
**it is a load-bearing safety feature (§7.2's nudity/weapons/illegal-content
screening, and the primary-photo-face-detection gate that the spec treats
as a signup requirement) that does not exist yet, wearing the shape of a
config-swappable adapter but with no second adapter to swap to and no
switch to swap it with.** Running this in production means every photo
upload is, in effect, unmoderated.

## 2.4 Adjacent, same failure pattern: `AUTH_TOKEN_SECRET`

Not part of the "demo data" surface per se, but the same silent-default-in-production
pattern as §2.2: `AUTH_TOKEN_SECRET` defaults to the literal string
`'dev-insecure-secret-change-me'` (`src/config/env.ts:19`, echoed in
`.env`/`.env.example`) if not overridden, with only a code comment ("MUST be
overridden in real environments") enforcing that — no startup check refuses
to boot with the default value, in production or otherwise. Combined with
§2.2/§2.3's pattern (config that silently no-ops or stays on a stub instead
of failing loudly when misconfigured), this is a codebase-wide habit worth
naming once: **nothing in this app refuses to start when a production-critical
setting is left at its insecure/fake default.** A single boot-time check —
"if `NODE_ENV==='production'`, refuse to start unless `AUTH_TOKEN_SECRET`
is overridden and `PAYMENT_PROCESSOR` is explicitly set" — would convert
three of this section's silent failure modes into a loud one, which is a
strict improvement even before the Stripe/moderation implementations exist.

## 2.5 The demo content itself — questions, venues, users

| Content | Swappable without a code change? | How |
|---|---|---|
| Venues | **Yes.** `POST /admin/venues`, `PATCH /admin/venues/:id` exist (`admin.routes.ts:144-163`) and are backed by a real service, not a stub. | Deactivate/replace seeded venues via the admin API. |
| Old (live) question bank — `questions`/`answers` | **Yes**, for adding/editing questions. `POST /admin/questions`, `PATCH /admin/questions/:id` exist and are wired (`admin.routes.ts:124-139`, `questions.routes.ts:19-30`). There is no delete endpoint and no bulk-replace, so removing the ~28 seeded demo questions (`seed.ts:76-169`) means editing each to `active:false` one at a time, or a manual SQL cleanup — workable, not elegant. | Admin API, one question at a time. |
| **New typed question bank** — `question_bank`/`user_question_answers` | **No — not from the running server at all.** `adminListQuestionBank`, `adminCreateQuestionBankEntry`, `adminUpdateQuestionBankEntry`, `selectNextQuestionsForMe`, `getMyQuestionAnswers`, `putMyQuestionAnswer` all exist in `question.service.ts` (lines 537-1151) but **none of them are wired to any HTTP route** — confirmed by grepping every file in `src/http/routes/` and `routeTable.ts` for each function name: zero matches. Managing this bank's ~65 seeded demo questions (`seed.ts:170-990`) today requires either writing new routes (a code change) or raw SQL against `question_bank`. See Part 3.1 for why this bank also isn't reachable from real scoring yet. |
| Demo users | **Yes**, cleanly. Identifiable by `@seed.outcome-dating.test` email domain (§2.1); `DELETE FROM users WHERE email LIKE ...` cascades correctly. |

## 2.6 Swap-over checklist for launch

1. **Payments.** Implement `StripeProcessor` for real against the
   documented contract (`stripe.processor.ts`'s per-method JSDoc is
   effectively the spec), add the `stripe` dependency, wire
   `STRIPE_WEBHOOK_SECRET` verification (noted but not implemented —
   `stripe.processor.ts:97-106`), and add a startup check that refuses to
   run with `PAYMENT_PROCESSOR` unset/`fake` when `NODE_ENV==='production'`.
   **Do this first — it is both the most work and the most dangerous thing
   to get wrong silently.**
2. **Photo/content moderation.** Implement a real `ImageModerationPort`
   adapter (a vision API or hosted moderation service) and wire it through
   `buildDeps` the same way payments are wired — today there is nothing to
   flip a switch *to*. Until this exists, treat photo moderation as **off**
   in any environment reachable by real users.
3. **`AUTH_TOKEN_SECRET`.** Generate and set a real secret in every
   non-dev environment; add the same startup refusal-to-boot check as
   payments.
4. **New question bank.** Decide whether it ships at launch. If yes: wire
   admin CRUD routes for `question_bank` (the service functions already
   exist, only the HTTP layer is missing) and resolve the duplication in
   Part 3.1 before doing so — shipping it unwired-to-scoring, as it exists
   today, would ask users to answer the same questions again for no
   scoring benefit.
5. **Old question bank.** Replace or deactivate the ~28 seeded demo
   questions via the existing admin API; no code change required.
6. **Venues.** Replace seeded demo venues via the existing admin API; no
   code change required.
7. **Users.** `DELETE FROM users WHERE email LIKE '%@seed.outcome-dating.test'`
   against the production database before allowing signups, or simply never
   run `seed` against the production database at all (it is a separate CLI
   command, never invoked by `serve`).
8. **Config defaults.** Run `ConfigService#seedDefaults` (idempotent,
   `ON CONFLICT DO NOTHING` — `config.service.ts:496-507`) once against
   production so every `config_entries` row exists with its real default
   before an admin starts tuning values; this is safe to run any time and
   doesn't touch demo *content*, but is worth including in a go-live runbook.

## 2.7 What would embarrass someone on launch day, ranked

1. **Real users get charged nothing, ever, because `PAYMENT_PROCESSOR` was
   never set** — the app looks fully functional, venue partners eventually
   notice they were never paid. (§2.2)
2. **A user uploads a genuinely unsafe photo and it's approved automatically**
   because there is no real moderation behind the stub, and nobody
   configured one because there is no config to configure. (§2.3)
3. **Every environment shares the same auth-signing secret** because
   nobody overrode `AUTH_TOKEN_SECRET`, and it's the literal string printed
   in this repo's own `.env.example`. (§2.4)
4. **An admin tries to manage the "new" question bank in production and
   discovers there's no UI/API path to it at all** — it was built, seeded,
   and tested, but never connected to anything reachable from outside the
   codebase. (§2.5)

---

# Part 3 — Is there a single source of truth?

## 3.0 Answer, up front

No, not consistently — and the product owner's exact complaint ("we asked
about children and religion three or four times") is not a hypothetical
risk here, it is **already true in the codebase today**, just not yet
visible to users only because the newer of the two systems that causes it
happens not to be wired to any HTTP route yet (Part 2.5). Beyond that
headline issue, the codebase has a systemic, repeated pattern of declaring
the same enumerated concept independently in TypeScript and in a SQL
`CHECK` constraint, with no shared source and no mechanism preventing drift
— most instances currently agree by discipline, one has already drifted
on purpose (and is easy to mistake for an accident), and one is a genuinely
unused shadow constant that would silently go stale if anyone touched its
config counterpart.

## 3.1 The headline duplication: two parallel, independently-answered question banks

`db/migrations/008_questions.sql` adds `question_bank` /
`user_question_answers`, a typed, versioned redesign, **alongside** —
not replacing — the original `questions`/`answers` tables from
`001_init.sql`. The migration's own comment block explains this was a
deliberate "clean break" decision (`008_questions.sql:7-41`): old answers
weren't auto-migrated because they carry no type/importance information
worth fabricating. That reasoning is sound for *why not to auto-migrate
data*. It does not address the consequence that actually matters here: **the
same real-world concept now has two independent question definitions, in
two different tables, answered separately, by design:**

| Concept | Old bank (`questions.slug`, live, HTTP-wired) | New bank (`question_bank.slug`, seeded, not HTTP-wired) |
|---|---|---|
| Children (has) | `has_children` (`seed.ts:86`) | `children_intention` (`seed.ts:404`) |
| Children (timeline) | — | `children_timeline` (`seed.ts:420`) |
| Children (wants) | `wants_children` (`seed.ts:87`) | (folded into `children_intention` above) |
| Religion | `religion` (`seed.ts:91`) | `religious_practice` (`seed.ts:235`) |
| Family closeness | `family_closeness` (`seed.ts:88`) | **`family_closeness` — the identical slug string**, in a different table, as a fully separate question (`seed.ts:435`) |

These are not shared rows referenced from two places — they are
independent questions, independently answered, independently weighted, with
no FK or reference tying an old-bank question to its new-bank counterpart.
If both were live at once, a user would answer "do you want children" once
in one place and "how central is religion" once in another, and then be
asked the *same underlying concept again* under a different label the first
time they touch the newer bank — precisely the failure mode described in
the prompt.

**What keeps this from being visible to users today is an accident, not a
decision:** the new bank's routes were simply never wired
(`selectNextQuestionsForMe`, `getMyQuestionAnswers`, `putMyQuestionAnswer` —
all real, tested functions in `question.service.ts:718-870` — have zero
references in `src/http/routes/*.ts` or `routeTable.ts`). The moment someone
wires those routes to ship the redesign, the duplication becomes real and
user-facing, exactly as described, unless the old bank is retired in the
same change.

**It's worse for scoring, not just UX.** `compatibility.service.ts` is
explicitly documented as a **leaf module** that reads only the old
`answers`/`questions` tables (`compatibility.service.ts:21-35`) — it has no
dependency on `question_bank`. A separate, fully pure, fully tested scoring
function for the new bank already exists —
`scoreQuestionContribution`/`aggregateQuestionScores`
(`src/domain/questions/scoring.ts:104-179`) — with an explicit comment
calling itself "THE INTEGRATION SEAM" for "a later agent" to wire in
(`scoring.ts:6-42`). That wiring has not happened. **Today, any answer a
user gives in the new bank contributes to their compatibility score
precisely zero — even for a user who fully populates it**, because
`getScore`/`getScoresForCandidates` (what discovery actually calls) only
ever look at the old tables. This means the two banks aren't just
duplicated definitions; one of them is currently inert for the product's
core purpose, in a way that would not be obvious from the API surface or
the database alone — you have to read `compatibility.service.ts`'s own
file-level doc to learn it.

**Which should be canonical:** the new typed bank (importance levels,
typed value/preference pairs, deal-breaker-as-hard-filter rather than
overweighted-scoring-term) is the more principled design, per its own
domain-layer documentation (`domain/questions/importance.ts:1-30`). The fix
is not "pick one" in the abstract — it's: finish the integration seam that
already exists (wire `scoring.ts` into `compatibility.service.ts`), migrate
or retire the old bank's user-facing surface, and only then wire the new
bank's HTTP routes — in that order, so the duplication is never live to end
users at all, rather than shipping the new bank first and creating the
exact user-facing repeat-question experience the product owner is trying to
avoid.

## 3.2 Enumerations declared independently in TypeScript and SQL

This is systemic, not an isolated slip. Every status/enum column in this
schema is a `text` column with a `CHECK (... IN (...))` constraint
(a deliberate choice over native Postgres `ENUM`, per `001_init.sql:13-16`,
so values can be extended without `ALTER TYPE` ceremony) — and every one of
them is *also* declared, completely independently, as a TypeScript string
union in `src/domain/types.ts` (or a sibling domain file). Representative
pairs, all currently in agreement, all held together only by developer
discipline with **no shared source, no codegen, and no runtime check that
they match**:

| Concept | TypeScript | SQL |
|---|---|---|
| Trust level | `TrustLevel` (`domain/types.ts:27`) | `users.trust_level CHECK` (`001_init.sql:33`), repeated again in `config.service.ts:44` as `z.enum(...)` for config values |
| User status | `UserStatus` (`domain/types.ts:26`) | `users.status CHECK` (`001_init.sql:29`) |
| Photo moderation status | `PhotoModerationStatus` (`domain/types.ts:103`) | `user_photos.moderation_status CHECK` (`001_init.sql:109`) |
| Interest status | `InterestStatus` (`domain/types.ts:268`) | `interests.status CHECK` (`001_init.sql:260`) |
| Conversation status | `ConversationStatus` (`domain/types.ts:294`) | `conversations.status CHECK` (`001_init.sql:289`) |
| Ledger entry type | `LedgerEntryType` (`domain/types.ts:572`) | `payment_ledger.type CHECK`, extended in `007_decisions.sql:41-42` |
| Moderation action | `ModerationActionType` (`domain/types.ts:665`) | `moderation_actions.action CHECK` (`001_init.sql:613`) |
| Body type | `BODY_TYPES` (`domain/units/bodyType.ts:14-22`) | `profiles.body_type CHECK` (`009_units_attributes.sql:52-53`, comment literally says *"keep in sync"*) |
| Importance level | `IMPORTANCE_LEVELS` (`domain/questions/types.ts:128`) | `user_question_answers.importance CHECK` (`008_questions.sql:124`) |
| Tag intensity | `TAG_INTENSITY_LEVELS` (`domain/questions/tags.ts:18`) | `user_tag_intensity.intensity CHECK` (`008_questions.sql:155`) |

None of these have drifted *today* — but nothing prevents it, and the
`bodyType.ts` case is the tell: its own comment already flags "keep in
sync" as a manual obligation, which is another way of saying there is no
mechanism enforcing it. **One pair has already drifted, on purpose:**
`notification_preferences.category` allows `('match', 'message',
'date_request', 'account_activity', 'marketing')`
(`011_notifications.sql:63`), while `notification_outbox.category` allows
those same five **plus `'safety'`** (`011_notifications.sql:133`) — a
deliberate, commented design choice (`011_notifications.sql:59-60`: safety
notices aren't user-preference-configurable). That reasoning is defensible,
but it means "category" is now two different enums with two different
legal-value sets, both still called `category`, both still meaning "kind of
notification" — exactly the shape of duplication that's easy for a future
change to widen in one place and forget in the other, since nothing ties
them together beyond a comment on one side.

**Fix:** for a codebase already committed to `text` + `CHECK` (a reasonable
choice), generate the TypeScript union from the migration's `CHECK` clause
(or vice versa) at build time, or at minimum add a single test that
introspects `information_schema.check_constraints` for each of these
columns and asserts the constraint's value list equals the corresponding
TypeScript union — cheap to write once, and it converts "drift is possible
and only caught in production" into "drift fails CI."

## 3.3 Config defaults shadowed by code constants

`ConfigService` (`config.service.ts:55-368`) is otherwise a genuinely good
single source of truth — one typed registry, one default per key, callers
required to `await ctx.config.get(...)`. But three places keep a *second*,
independent copy of a value that's supposed to live only in that registry:

1. **`MIN_PROFILE_COMPLETENESS_FOR_DISCOVERY = 50`**
   (`discovery.service.ts:110`) shadows `discovery.min_profile_completeness`
   (default `50`, `config.service.ts:261-267`). The comment explains it's
   meant as "a fallback for any call site that can't await `ctx.config`"
   (`discovery.service.ts:102-109`) — but a repo-wide search finds it is
   **never actually referenced anywhere outside its own declaration**. It's
   a dead, publicly-exported constant that happens to agree with the config
   default today by coincidence of nobody having changed either value since
   it was written. If `discovery.min_profile_completeness`'s default is ever
   changed and someone later reaches for this exported constant (its
   entire reason for existing), they'll silently get the stale value.
2. **`DEFAULT_MIN_SHARED_QUESTIONS = 3`** and **`DEFAULT_NO_DATA_SCORE = 0`**
   (`compatibility.service.ts:125,128`) shadow `compatibility.min_shared_questions`
   (default `3`) and `compatibility.no_data_default_score` (default `0`)
   (`config.service.ts:247-260`). Lower risk than #1: these are actually
   used, but only as default parameter values for the pure, no-`ctx`
   function `computePairScore` (`compatibility.service.ts:197-202`) so it
   stays unit-testable without a database — every real call site
   (`getScore`, `getScoresForCandidates`, `refreshScoresForUser`,
   `refreshAllScores`) does load the live config value and pass it
   explicitly (`compatibility.service.ts:272-279` and call sites). Still a
   second declaration of the same number that a future edit to the config
   default could silently leave behind in test/pure-function behavior.
3. **`TRUST_SCORE_BASE = 50`** (`trust.service.ts:126`) shadows
   `users.trust_score DEFAULT 50` (`001_init.sql:30`) — the comment
   (`trust.service.ts:126`) explicitly says *"matches users.trust_score
   DEFAULT in 001_init.sql"*, i.e. the author already knew this was a
   duplicate and left a note instead of removing the duplication. If the
   column default is ever changed via a future migration, every
   `recalculateTrustScore` call keeps starting from the old base value
   until someone remembers this comment exists.

**Fix:** for #1, delete the dead constant. For #2, keep the pure-function
default (it's a legitimate, documented tradeoff for testability) but add a
one-line test asserting the constant equals `ConfigKeyRegistry[...].default`,
so a future edit to one is forced to touch the other. For #3, read the
starting value once at startup from `config`/schema introspection rather
than hardcoding it a second time, or apply the same drift-test fix as #2.

## 3.4 Distance: two implementations, currently reconciled

`filter.service.ts` has its own `haversineKm`
(`filter.service.ts:347-356`, used for exact hard-filter enforcement — "is
this candidate within 50km") and `domain/units/distance.ts` has its own,
separately-implemented `haversineKmExact`
(`domain/units/distance.ts:162-169`, used internally by the shared,
privacy-bucketed `approximateDistanceBetween` that every *display* surface
now calls per the SAF-2 fix — `distance.ts:217-234`, confirmed both
`discovery.service.ts:306-310` and `profile.service.ts:386` call the shared
function, not a local copy). Both implementations use the identical
great-circle formula and the identical Earth radius constant (`6371`,
`filter.service.ts:348` and `distance.ts:153`), and the split is explained
and deliberate (`distance.ts:161`: exact-distance-for-filtering is "a
materially different concern" from exact-distance-that-must-never-be-displayed,
and keeping the display path's internal exact calculation unexported
prevents it from ever accidentally becoming a second display path). This
is a genuine, defensible reason for two implementations rather than one
shared exported function — but it is still two independently maintained
copies of the same formula and the same magic-number Earth radius that a
future edit (e.g. switching to a more precise ellipsoidal model, or
changing the radius constant for unit-consistency reasons) could update in
one place and miss in the other, with no test tying them together today.
Lower severity than §3.1-3.3 — flagged for completeness since the prompt
asked specifically about distance, and because "each copy has a good reason
to exist" is exactly the kind of duplication most likely to be waved through
in review and then drift years later.

## 3.5 Minimum age: dual-enforced, currently consistent (lower risk)

The "at least 18" rule is implemented twice — once in application code
(`calculateAge` + `MIN_AGE_YEARS = 18`, `auth.service.ts:144-155,229-234`,
checked before any DB write) and once as a DB backstop
(`users_min_age CHECK (birthdate <= CURRENT_DATE - INTERVAL '18 years')`,
`001_init.sql:40`). This is explicitly documented as defense-in-depth
(`auth.service.ts:229-233`), which is a legitimate pattern for a rule this
safety-critical — a bug or a future direct-SQL insert (e.g. from a
migration or an admin tool) still can't create an under-18 account even if
the application-layer check is bypassed or has a bug. Flagged here only
because it is, mechanically, the same "same rule, two implementations"
shape as everything else in this section — the two definitions use
different date arithmetic (whole-years-elapsed in TypeScript vs. a fixed
interval subtraction in SQL) and, while they agree on every case checked
during this review, nobody has written a test asserting they agree on
every boundary case (leap-day birthdates, etc.). Worth a drift test; not
worth ranking alongside §3.1-3.3.

## 3.6 What's done right — keep this pattern

Two places in the codebase actively *prevent* the kind of duplication this
section is about, and are worth naming so they aren't lost in a future
refactor:

- **`eligibility.service.ts`** is a thin, explicit wrapper whose entire
  purpose is to guarantee discovery's mutual-filter gate and interest-send's
  mutual-filter gate can never diverge, because both call the *same*
  `filter.service#passesMutualFilters`, never a reimplementation
  (`eligibility.service.ts:1-60`). This is exactly the right answer to "the
  same business rule implemented in two services" — implement it once,
  have the second caller depend on the first, and document why (the file's
  own "TWO CALLERS, ONE IMPLEMENTATION" section, `eligibility.service.ts:29-42`).
- **`ConfigService`**'s typed key registry (`config.service.ts:55-368`) is
  a real single source of truth for every business-tunable value in the
  system — one schema, one default, one description per key, with `snapshotPolicy`
  explicitly solving the "existing objects must not observe a later config
  change" problem (§21.3) rather than letting each service invent its own
  answer. The shadow constants in §3.3 are a minor, fixable erosion of an
  otherwise well-designed system, not evidence the system itself is wrong.

## 3.7 Ranked: worst single-source-of-truth violations

1. **Two parallel question banks, one of them scoring-inert** (§3.1) — the
   exact failure mode the product owner named, already present in the
   codebase, currently invisible only because of an HTTP-wiring gap that
   looks likely to be closed at some point.
2. **The fake/real payment processor selection has no loud-failure path**
   (§2.2 — cross-referenced here because it's also, structurally, "the same
   decision — which payment backend is real — made in two disconnected
   places: an env var default and a stub implementation that throws") —
   included here because getting this wrong is silent, not because it's an
   enum-drift issue.
3. **`notification_outbox`/`notification_preferences` category enums have
   already diverged** (§3.2) — smaller blast radius than #1, but proof the
   "declared twice, no shared source" pattern isn't hypothetical.
4. **Config defaults shadowed by unused or test-only code constants** (§3.3)
   — currently harmless, but `MIN_PROFILE_COMPLETENESS_FOR_DISCOVERY`
   is a landmine with someone's name on it the day anyone "helpfully" starts
   using the exported constant instead of `await`ing config.
5. **Two independent haversine implementations** (§3.4) and **two
   independent 18-years-old checks** (§3.5) — both currently consistent,
   both worth a one-line regression test rather than a redesign.
