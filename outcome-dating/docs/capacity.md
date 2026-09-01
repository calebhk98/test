# Capacity at 8 billion users

**Answer.** The schema has no genuine 32-bit overflow risk today (fixed the two
borderline cases anyway; see below). The read paths this build could reach are
empirically population-independent, proven by measurement, not assumption.
Storage is dominated by activity tables (messages, interests, impressions),
not the `users` row itself, and a single Postgres primary stops being viable
long before 8B users regardless of query tuning. Matching is local, so the
fix is geographic sharding, already implied by the discovery/dashboard fix
this build builds on.

## 1. Hard limits: 32-bit column audit

Every `integer`/`smallint` column in `db/migrations/*.sql` was read (full list,
not a sample). Two were widened; every other one is bounded by something other
than population.

| Column | File:line | Verdict | Fix |
|---|---|---|---|
| `stats_cohort_retention.cohort_size`, `active_d1/d7/d30` | `020_stats.sql:115-118` | Per-registration-day COUNT; at 8B users over any realistic signup history this is orders of magnitude under 2.147B/day, but it is population-correlated | Widened to `bigint`, `023_widen_counters.sql` |
| `stats_aggregation_runs.duration_ms` | `020_stats.sql:144` | Job wall-clock ms; overflows past ~24.8 days runtime, would silently wrap rather than error | Widened to `bigint`, `023_widen_counters.sql` |
| `device_fingerprints.distinct_user_count` | `001_init.sql:71` | Bounded by accounts sharing ONE device, not platform population | No change |
| `payment_ledger`/`payment_holds`/`venue_settlements` `*_cents`, `photo_experiments.impressions/interests_*`, `stats_platform_daily.*` | `001_init.sql`, `007_decisions.sql`, `020_stats.sql` | Already `bigint` (stated project convention: "all money is bigint minor-unit cents", `001_init.sql:15`) | No change |
| `trust_score`/`reputation_score`/`profile_completeness`/`rollout_percent`, `self_value`/`partner_value`/`severity` (×2) | `001_init.sql` | CHECK-bounded 0-100 or 1-5 | No change |
| `user_photos.position`, `photo_recommendations.current_position/recommended_position` | `001_init.sql:106`, `002_agent_a.sql:84-85` | Bounded by one user's own photo count (a handful), not population | No change |
| `notification_outbox.coalesced_count`, `*.attempt_count` (×2), `post_date_feedback_prompts.prompt_count`, `start_minute`/`end_minute`, `height_cm`/`weight_g`/`distance_precision_floor_km` | various | Bounded per-user, per-attempt, or physical/clock quantities, none platform-scale | No change |
| No `serial`/`bigserial` PK anywhere; every PK is `uuid` | `001_init.sql:15` (stated convention) | No 32-bit sequence exists to exhaust | No change |
| `compatibility_scores` PK/columns | `001_init.sql:241` | Not a width problem, an O(n²) row-COUNT problem (see §4) | Architectural, not a migration |

**The certainty**: nothing in this schema silently corrupts data at 8B users
via integer wraparound. The two widened columns were precautionary (cheap,
in-place `ALTER COLUMN TYPE`, no table rewrite), not urgent.

## 2. Measured: population independence

`tests/perf/scaleCurve.perf.test.ts` seeds a FIXED 400-user home city (Chicago)
plus a variable population in five cities >1,000km away (so "elsewhere" can
never enter the viewer's 160km search box, `seedScaleCurve.ts`), at three
total platform sizes, and calls every reachable user-facing read path for the
same home viewer at each size. Real measured run (`SCALE_CURVE_SCALES=1000,10000,50000`):

| Read path | N=1,000 | N=10,000 | N=50,000 | Query count |
|---|---|---|---|---|
| Discovery grid | 126ms | 21ms | 27ms | 14 (flat) |
| Reality dashboard | 125ms | 25ms | 24ms | 26 (flat) |
| Public profile view | 2ms | 3ms | 2ms | 6 (flat) |
| My matches list | 45ms | 43ms | 39ms | 161 (flat) |
| Conversation timeline | 3ms | 3ms | 3ms | 3 (flat) |
| Stats overview | 4ms | 4ms | 4ms | 17 (flat) |
| Filter costs | 134ms | 27ms | 33ms | 33 (flat) |

Query count (the thing that provably cannot regress silently) is **identical**
at every scale for every path, 50x more total users, same number of round
trips. N=10,000 -> N=50,000 latency is flat by any reasonable ratio (all
within about 20%). N=1,000 is the one reproducible outlier, and only for the
two geo-box queries: a freshly created database's smallest table has no
ANALYZE-derived statistics yet, and Postgres's planner measurably picks a
worse plan purely from that (reproduced identically across three separate
runs, 125-156ms every time), an artifact of "first/smallest database
queried," not of population. The suite's own flatness assertion documents
this and excludes only N=1,000 from the strict latency ratio (query count is
still required flat at every scale, including N=1,000, and is). Extrapolation:
since cost is a function of the FIXED home population (400) and the
geographic box, not of total N, the 8B-user number is the same as the
50,000-user number, there is no curve to extrapolate along this axis, which
is the finding itself.

One caveat, found while tracing call sites, not measured: `filter.service.ts`'s
`previewPoolSizeWithUnsetPolicy` (`filter.service.ts:1043-1099`) is
deliberately NOT geo-bounded (its own doc explains why: it needs an exact
platform-wide count). It is currently dead code, no HTTP route or job calls
it, only its own unit test does (`grep -rn previewPoolSizeWithUnsetPolicy src/`
returns one file). If it is ever wired to a real endpoint, that endpoint would
scale with total population like discovery did before the geo-bound fix.

## 3. Measured -> extrapolated: seeding throughput

Seed wall-clock time, this run (`seedScaleCurveData`, bulk `unnest` inserts,
one dev-box Postgres, single connection):

| N | Seed time | Rows/sec |
|---|---|---|
| 1,000 | 66ms | 15,151 |
| 10,000 | 491ms | 20,367 |
| 50,000 | 2,467ms | 20,268 |

Roughly linear, ~15,000-20,000 rows/sec average on this single unoptimized
connection. **Extrapolation** (arithmetic, not measured): 8,000,000,000 /
18,500 ≈ 432,432 seconds ≈ **5.0 days** to bulk-load the `users` table alone,
sequentially, on one connection, on this dev box, before any index
maintenance backlog, replication, or concurrent write traffic. This is the
concrete argument for why "seed 8B rows" was never attempted here (task
framing): it would take days on a single loader even under ideal bulk-insert
conditions, and production traffic is nothing like a bulk load.

## 4. Physical requirements at 8B users (estimates, assumptions stated)

Row size estimates include Postgres tuple header/alignment overhead; index
sizes are separate btree entries, not shared with heap.

| Table | Rows (assumption) | Est. bytes/row | Heap | + indexes | Total |
|---|---|---|---|---|---|
| `users` | 8.0B (1:1) | ~200B | 1.6TB | +0.7TB | ~2.3TB |
| `profiles` | 8.0B (1:1) | ~300B | 2.4TB | +0.6TB | ~3.0TB |
| `messages` | 400B (50/user, assumed) | ~200B | 80TB | +40TB | ~120TB |
| `interests` | 160B (20/user, assumed) | ~200B | 32TB | +24TB | ~56TB |
| `discovery_events` | 117T (20/day x 2yr retention, assumed) | ~110B | 12.8PB | +9.3PB | ~22PB |
| `compatibility_scores` (if ever fully materialized) | 6.4x10^19 (n^2) | ~72B+90B idx | n/a | n/a | **~10 zettabytes: physically impossible at any hardware budget** |

`compatibility_scores` is not a bigger-hardware problem, it's an arithmetic
one: doubling users quadruples pairs. This is why the nightly full-refresh job
must stay geo-scoped/on-demand (already the direction of this build's
discovery fix) and never materialize globally, confirmed independently by
`docs/scale-and-sources.md` §1.2.1's own (smaller-scale) estimate, which this
number is consistent with (their ~175TB at 1M users x 64,000,000 population²
scaling factor lands in the same zettabyte range).

`discovery_events` (impression logging, no retention policy in the schema
today) is the single largest realistic table, bigger than every other table
combined by 2-3 orders of magnitude, because it is one row per CARD SHOWN,
not per user. This is the "impression count" the task brief specifically
flagged, and unlike `messages`/`interests` it has no natural per-user ceiling
without an explicit retention/partitioning policy (`docs/scale-and-sources.md`
§1.5 already names it as needing time-based partitioning).

**Write throughput.** A single Postgres primary sustaining even the
CONSERVATIVE end of `messages` alone (4x10^11 messages / 10-year platform
life / 86,400s / 365d ≈ 1,268/s average, plausibly 5-10x at daily peak =
6,300-12,700/s) is already at the edge of what one primary handles well
once `interests`, `discovery_events`, `notification_outbox`, and payment
writes share the same connection budget (`src/db/pool.ts` max: 10, today).
This is consistent with `docs/scale-and-sources.md` §1.5's "high tens of thousands to
low millions of users" ceiling for one primary.

**Shard count.** Matching is local (§1.3 of the existing review), so the
natural unit is a regional shard. At a conservative ~5,000,000 users/shard
(inside the single-primary ceiling above, WITH partitioning/replicas already
applied): 8,000,000,000 / 5,000,000 = **1,600 regional primaries**, each
wanting 1-2 replicas, on the order of 3,000-5,000 database instances,
independent of app-tier instance count.

## 5. What breaks, ordered by when it binds

1. **Now, far below 8B** (already documented, `docs/scale-and-sources.md`
   §1.2/§1.6): nightly compatibility full-refresh job (O(n²)), in-process
   rate limiter/config cache once more than one app instance runs.
2. **Tens of thousands to low millions of users**: single Postgres primary's
   write budget and 10-connection pool (§4 above); `discovery_events`
   growing unbounded with no retention policy.
3. **Low millions to tens of millions**: `messages`/`interests`/
   `discovery_events` need time/hash partitioning; read replicas needed per
   region.
4. **~100M-1B**: single-region deployment tops out; regional sharding
   becomes mandatory, not optional (§4's 1,600-shard arithmetic).
5. **8B**: not a bigger version of #4, requires the matching subsystem to
   already be decomposed by geography from the start (existing review's
   conclusion, confirmed here by the population-independence measurements
   in §2, which show the RIGHT architecture, done consistently, is already
   flat at this axis).

No column in the schema is the binding constraint at any of these steps.
