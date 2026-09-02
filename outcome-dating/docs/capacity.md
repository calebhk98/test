# Capacity: does this scale to 8 billion users?

The owner asked whether 8B users of text fits in a few hundred GB and
computes in under an hour on a laptop - a whole-platform storage/compute
question. §5's answer is **no** on both, by roughly one to two orders of
magnitude, with numbers. But that is also the wrong question to worry about
operationally: matching is local, and §1-4 prove (not assert) that every
real per-operation cost depends on local population near one viewer, not
total N.

## 1. Per-operation time/space complexity

Variables: **N** = total users. **R** = users inside a viewer's search
radius, geographically (before any filter). **D** = local density
(users/km²), so R ≈ D·π·radius². **C** = `MAX_CANDIDATE_POOL_SIZE` (500),
`DASHBOARD_SCAN_CAP` (5,000) - fixed constants, not variables. **Q** =
questions a user has answered. **M** = messages in one conversation.

| Operation | Time | Space (working set) | Round trips |
|---|---|---|---|
| Discovery grid (`loadCandidatePool`) | O(log N + R) to match+order the WHERE-matched rows, index-scannable (see §2) | O(C) returned | O(1), measured flat: 14, from 1,000 to 50,000 local candidates (§2) |
| Reality dashboard (X/Y/Z) | O(log N + R), same shape, `DASHBOARD_SCAN_CAP` instead of `C` | O(min(R, 5,000)) | O(1), measured flat: 26 |
| Compatibility score, one candidate | O(Q) (shared-question overlap) | O(Q) | 0 (batched with the pool) |
| One discovery request, end to end | O(log N + R + C·Q) | O(C·Q) | O(1) |
| Message send / conversation timeline | O(M) | O(M) | O(1) |
| Nightly compatibility refresh (geo-scoped, existing design) | O(N · R_avg · Q) - **linear in N**, because each user's own refresh is itself O(R_avg·Q), never O(N) | O(R_avg·Q) per user in flight | O(N) jobs, parallelizable per user |
| Nightly compatibility refresh, if ever done densely (NOT this design) | O(N²) | - | - |

The load-bearing fact: **no single discovery-grid or dashboard request's
cost is a function of N.** It is a function of R (local density and search
radius, not how many people exist elsewhere on the planet) and the fixed
constants C/Q. `tests/perf/scaleCurve.perf.test.ts` proves this empirically:
the same home-city viewer, at N=1,000/10,000/50,000 total platform users
(the rest seeded >1,000km away), gets an IDENTICAL query count at every
scale (grid 14, dashboard 26). This is the proof, not an assertion, that "no
operation ever needs the whole planet at once": R, not N, is what every real
operation touches, and R is bounded by geography. The nightly refresh is the
one place N appears at all, and it appears LINEARLY (one bounded-cost pass
per user), because it is geo-scoped the same way discovery is
(`compatibility.service.ts`, not owned by this build); a full O(N²)
materialization was rejected for exactly this reason (§5).

## 2. Dense cities, concretely

This build's fix (see `src/services/discovery.service.ts#loadCandidatePool`,
`db/migrations/026_density.sql`) closed two defects: hard filters used to be
applied AFTER the pool was truncated to 500 rows by recency, so (a) a
recently-active-but-filter-failing crowd could produce an empty grid despite
real matches existing, and (b) ranking only ever saw the 500 most recently
active people, never the actually best match if that match wasn't recently
active. The fix pushes the viewer's own cheap, indexable filters (age,
gender, relationship intention, height, weight, body type) into the SQL
WHERE clause, and replaced `ORDER BY last_active_at DESC` with `ORDER BY
discovery_shuffle_key` (a static per-row random value, indexed, assigned once
- chosen over `ORDER BY random()` specifically so the ordering stays
index-scannable and cheap at density, see the migration's doc).
**Adaptive pool expansion and geographic-cell walking were both considered
and rejected**: either makes a single request's query COUNT depend on local
density, which is the exact "cost grows with population" shape that took the
original unbounded query down. The fix keeps query count fixed at one query
for the pool, regardless of density, verified in `tests/perf/density.perf.test.ts`
(measured below) and in `tests/perf/discovery.perf.test.ts` (unchanged,
still passes: 14/26 queries flat across all six seeded cities).

**Candidate pool size at radius r, density D: R = D · π · r².**

| City (stated assumption) | Density | R at 1km | R at 5km | R at 10km | R at default 160km |
|---|---|---|---|---|---|
| New York, 8M / ~780km² (5 boroughs) | ~10,256/km² | 32,220 | 805,500 | 3,222,000 | ~8,000,000 (whole city fits inside the box) |
| Shanghai, 25M / ~6,340km² | ~3,943/km² | 12,384 | 309,600 | 1,238,400 | ~25,000,000 |
| 70M megacity cluster / ~40,000km² assumed | ~1,750/km² | 5,498 | 137,445 | 549,780 | ~70,000,000 |
| Extreme urban core, 46,000/km² (task figure) | 46,000/km² | 144,513 | 3,613,000 | 14,451,000 | n/a (city-scale, not applicable) |

**Where geography alone fails.** At 46,000/km², keeping R at or below the
500-candidate cap by shrinking the radius ALONE would require r ≈
√(500/(46,000·π)) ≈ **59 meters** - a dating app cannot suggest "within one
building." Proof that a bounding box is a performance prefilter, never a
correctness mechanism, at real urban density: even 1km (an easy walk) is
already 64-289x the pool cap across every row above. **Result quality**: the
pool is a bounded, representative sample of R, not all of R. At NYC's
default-radius R≈8,000,000, a served pool of 500 is 0.006% of the eligible
population; nobody sees "everyone nearby," and no query-layer fix changes
that, only which 500 (filter-passing, not recency-biased) get shown.
Whether the single global-best match among 8,000,000 people appears in any
one request is NOT guaranteed (scoring 8,000,000 candidates per request is
the O(N) blowup being avoided); what IS guaranteed is filter-passing
candidates are never crowded out by filter-failing ones, and inclusion is
no longer systematically biased toward one irrelevant trait (recency).
Closing that last gap (surfacing the literal best-of-millions every time)
needs precomputed per-cell top-K ranking or an ANN index over compatibility
embeddings - out of scope here, flagged as the honest next step at
NYC-core-scale density.

**Measured** (`tests/perf/density.perf.test.ts`, 50,000 candidates in ONE
box, 49,000 recently-active filter-failing + 1,000 old filter-passing, the
worst pre-fix shape): `getDiscoveryGrid` costs **14 queries, 56ms**,
identical query count to a 6-city, 24,000-user spread
(`discovery.perf.test.ts`). The full 500-candidate ranked pool (5 paginated
calls) is **100% real matches, 0% crowd**, in 520ms/70 queries. Extrapolating
(not measured) to NYC's ~8,000,000-row default-radius box: if Postgres uses
the `discovery_shuffle_key` index with an early LIMIT stop, cost stays near
this measurement (dominated by the fixed cap, not R); if the planner sorts
the whole matched set instead, linear extrapolation (56ms · 8,000,000/50,000)
suggests **~9 seconds**, worst case, still O(1) round trips. Confirming which
plan Postgres picks at that literal scale needs a real NYC-scale dataset,
impractical to seed in a fast suite; flagged as a follow-up before launch.

## 3. Rural users

Confirmed by reading the code (`filter.service.ts`, function formerly
`resolveSearchRadiusKm`, now `resolveRadiusAndStructuredFilters`): a user's
own enabled `distance_km` filter (`lte`/`lt`) is read directly
(`toComparableNumber(row.value)`) and used as `radiusKm` with **no upper
clamp anywhere** - not in this function, not in `boundingBoxForRadius`
(which widens to cover a huge radius rather than erroring), not in the zod
schema for `updateMyFilters` (`value: z.unknown()`). `DEFAULT_DISCOVERY_RADIUS_KM`
(160km) applies only when no filter is set; the moment a user sets their
own distance, it wins outright, confirmed by existing, unmodified tests
(`filter.test.ts`'s `resolveGeoSearchContext` test,
`discovery.test.ts`'s "uses the viewer's OWN distance_km filter" test). So a
rural user with "a couple dozen within 10 miles" who sets 100+ miles
(161km+) gets exactly that radius, no silent override, no hidden ceiling.
At that density R (a few hundred at most across 100 miles) never approaches
C (500), so this build's density fix doesn't even engage for them - every
eligible person is returned, exactly, every time; the bug it fixes is a
dense-city problem specifically, confirmed absent at rural density by
construction (R < C means no truncation of any kind).

## 4. Shard edges (design only, nothing implemented today)

No sharding exists today (single Postgres primary, one `DATABASE_URL`,
`src/db/pool.ts`). Honest answer to "what happens at a partition boundary"
if geographic sharding were added: a NAIVE scheme (route every query to the
viewer's own home shard only) silently loses real matches just across the
line - the exact "filters produce wrong results at the edge" failure this
build exists to avoid elsewhere. **The fix: fan-out, using the SAME
bounding box already computed.** `boundingBoxForRadius(lat, lon, radiusKm)`
already produces the exact rectangle a viewer's search can reach. Under a
grid-cell shard scheme (each shard owns a fixed lat/long tile), that same
box determines which tiles - and therefore shards - to query: map the box's
corners to tile ids, issue the SAME single bounded pool query against every
touched shard IN PARALLEL, merge and re-cap client-side to
`MAX_CANDIDATE_POOL_SIZE` before ranking. **Cost**: bounded by tiles
overlapped, not shard count. With tiles larger than a typical search radius
(say 100km tiles against a 160km default), a box overlaps 1 tile in the
common case, at most 4 near a corner - O(1) average, O(4) worst case, not
O(all shards). A 100+mile rural request can span more tiles; cap the
fan-out at a fixed maximum rather than letting radius alone set the cost.
The alternative (each shard stores a buffered copy of neighbors within X km
of its border, so one shard alone finds edge matches) avoids fan-out
queries but pays in storage duplication and replication lag; fan-out is the
better default since the box this build already computes makes "which
shards" nearly free to answer.

## 5. The owner's arithmetic: storage and compute, no hedging

**Storage: not achievable at "a few hundred gigabytes."** Per-row estimates
(Postgres tuple overhead included): `users` ~200B/row, `profiles` ~300B/row;
heap+index totals at 8.0×10⁹ rows: `users` 2.3TB, `profiles` 3.0TB (full
workings: `docs/scale-and-sources.md`'s 32-bit column audit, unchanged by
this build). **Just those two tables, the bare minimum for "a user exists
with a profile," already total 5.3TB** (~660 bytes/user) - **10-25x** a "few
hundred GB" (200-500GB) budget, before a single message, filter, tag, or
answered question exists. Add what matching actually needs
(`hard_filters`, `user_tags`, ~20-30 answered questions/user at ~130B/row)
and per-user footprint grows to ~4-5KB: **8×10⁹ × 4.5KB ≈ 36TB**, the honest
complete "text-only matching data" figure, **~70-180x** over budget.
**Achievable figure: 5TB (bare identity+profile) to ~35-40TB (what matching
needs to actually work).**

**Compute: depends entirely on which operation.** The PER-USER operation
(one discovery request) is genuinely fast at any N, proven in §1/§2: tens
of milliseconds, O(log N + R), not O(N). That part of "compute this on a
laptop" is real and already true today. NOT achievable in an hour on a
laptop is any WHOLE-PLATFORM pass: reading just the minimal 5.3TB
(users+profiles) once, sequentially, at a generous modern-NVMe 1GB/s, takes
5.3TB / 1GB/s ≈ 5,300s ≈ **88 minutes** - over an hour before a single byte
of scoring happens. The realistic 36TB figure takes **≈10 hours** for that
same bare read. A full O(N²) compatibility matrix is not merely slow, it is
**6.4×10¹⁹ pairs ≈ 10 zettabytes** if materialized
(`docs/scale-and-sources.md`'s independent, consistent estimate) - physically
impossible at any hardware budget; this is why the nightly refresh must
stay geo-scoped (§1's linear-in-N design), never global. **Bulk-loading**
8×10⁹ rows sequentially, measured at 15,000-20,000 rows/sec on one dev-box
connection (`scaleCurve.perf.test.ts`'s seeding numbers), extrapolates to
**≈5.0 days** for `users` alone, one connection, before index maintenance
or concurrent traffic.

**Bottom line, no hedging**: storage is not "a few hundred GB," it is
**5-40TB**, one to two orders of magnitude over the estimate. Compute for
any single real operation (what a user actually waits on) is genuinely
sub-second regardless of N, proven, not assumed. Compute for any
whole-platform operation is not achievable on a laptop in an hour at any
scope from "read every row once" upward; the achievable figure is **hours
to days on one machine**, or minutes with the same geo-scoped parallelism
this build's fix already uses, spread across the ~1,600 regional shards
§4 implies at 8B users (5M users/shard, inside one primary's write budget,
`docs/scale-and-sources.md` §1.5). The fix was never "make the
whole-platform number smaller," it was proving no real operation is one.
