# Where the data comes from

The three data sources, what each costs, and how the free tier is paced.

[← back to the README](../README.md)

---

## Where the data comes from

| Source | Key needed? | What it gives | Cost |
| --- | --- | --- | --- |
| **MarketCheck** Inventory Search | **yes** (free tier) | the listings themselves | 500 calls/month, enforced |
| **NHTSA** Complaints & Recalls (`api.nhtsa.gov`) | **no** | consumer-filed defect complaints and manufacturer recall campaigns per model-year | free, unlimited, cached 30 days |
| **EPA** fueleconomy.gov | **no** | combined MPG when MarketCheck omits it | free, unlimited, cached 180 days |

NHTSA is real federal data — the same underlying dataset every third-party reliability site
repackages. It gives raw counts and descriptions, not a friendly 1–5 score, and it feeds two
components of every listing's score.

**It is looked up automatically.** Every daily run collects the distinct make/model/year
combinations it just fetched and, for any it has never seen before, calls NHTSA (and EPA for
MPG) right then — no separate step, no key, no MarketCheck quota consumed. Results are cached
per model-year, so fifty Civics cost one lookup and a model already known costs nothing. The
digest names each first-time lookup ("first NHTSA lookup: 2022 Kia Forte (31 complaints, 1
recall)"). `python3 -m carmon enrich` forces a refresh; `--force` ignores the cache.

That data then shows up everywhere: MPG and a `complaints / recalls` column on the dashboard,
a full Reliability section on each listing page (top components, each recall campaign, VIN
lookup link), `GET /api/reliability` and per-listing fields in the API, and the
`get_reliability` / `refresh_reliability` / `list_reliability` MCP tools. Neither free source counts against the MarketCheck quota,
and neither can break the daily run: if either is unreachable, the run logs it and carries on
with the last cached values.

> **Read complaint counts carefully.** They are *not* adjusted for sales volume — a 2022 Civic
> shows 878 complaints and a 2022 Corolla 95, partly because Honda sold a lot of Civics. The
> stronger signal is *which components recur* (729 of those Civic complaints are STEERING) and
> whether recalls are still unrepaired on the specific VIN. That is why the complaint weight is
> deliberately small and every listing page links the NHTSA VIN lookup.

RepairPal (repair cost, visit frequency, severity), Edmunds and KBB owner reviews have **no
public API** — Edmunds' is partner/business-only, not self-serve. They are deep links only,
alongside the retailers and aggregators; see [SOURCES.md](SOURCES.md).

---

## Quota pacing and the month-end sweep

500 calls a month only means something next to how much of the month has gone by, so the
raw counter is always shown against the calendar:

```bash
python3 -m carmon quota
```

```
MarketCheck quota for 2026-08
  ████████░░░░░░░|░░░░░░░░░░░░░░░░   (filled = used, | = today)
  used 100 of 500 — 400 left
  day 15 of 31 (48% of the month gone)
  expected ~242 by now → 0.41x pace  🟢 well under pace
  projected month total 207
  ~26 calls/day still affordable for the rest of the month
```

100 calls on the 15th reads **0.41x — well under pace**; the same 100 calls on the 5th reads
**1.24x — running hot**, projecting 620 against a 500 cap. The bands are: well under pace ·
under pace · on pace · running hot · far ahead of pace.

**This is a metric, not a limit.** Nothing throttles or blocks on it. The only hard stop is
still the cap itself, enforced in the client. The same numbers appear in the digest, the
Discord message, the dashboard's pace tile, `GET /api/quota`, and the `get_quota_pace` MCP tool.

### Spending leftover calls before they expire

Unused free-tier calls do not roll over — an unused balance is simply gone at midnight on the
last day of the month. So on that day the run spends what is left rather than wasting it:
deeper pagination first (a normal run only reads the cheapest few pages), then one targeted
query per preferred model, which surfaces cars that price-sorted paging never reaches.

Configured under `api.month_end_sweep`: `enabled`, `trigger_last_days` (default 1),
`reserve_calls` (20, kept back for a retry), `max_extra_calls` (400) and `max_pages_per_query`.
The digest and Discord message report what the sweep spent and what it found.

---

Next: [configuration and scoring](configuration.md) · [optional scrapers](scrapers.md)
