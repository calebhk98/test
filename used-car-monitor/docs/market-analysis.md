# Judging a deal: market comparison and trends

How the monitor decides whether a price is good — and what it refuses to claim.

[← back to the README](../README.md)

---

The monitor answers "is this price any good?" from your own accumulated data, with no extra
API calls — it is ordinary least squares over the listings already in SQLite.

```bash
python3 -m carmon appraise --make Toyota --model Corolla --year 2022 --mileage 35000 --price 17500
```

```
🟢 good deal: $17,500 versus an expected $18,437 for this mileage and year (-937, -5.1%).
Based on 42 comparable listings (good confidence, price ~ mileage + model year).
Cheaper than 62% of them. This market charges about $98 per 1,000 miles.
  basis: Toyota Corolla within ±1 model year (model_year), method: price ~ mileage + model year, r² 0.944
  comparables: median $18,353, range $15,652–$21,808, n=42
  each newer model year is worth about $892 here
  This compares asking prices only — it knows nothing about condition, trim, options,
  accident history or title status. Always inspect the car itself.
```

Other entry points: `python3 -m carmon appraise --vin <VIN>` for a stored listing,
`python3 -m carmon deals` for everything ranked by how far below expected it sits, and
`python3 -m carmon market` for the trend report. The website has `/market` and `/appraise`
pages plus a "vs market" column, and the MCP server exposes `appraise_car`, `market_trend`,
`market_report`, `best_deals` and `list_comparables`.

### Two questions, two different waiting periods

This matters for a search that runs a month or two before you buy:

| Question | Kind | Ready when |
| --- | --- | --- |
| "Is this 2022 Corolla at 35k miles priced well?" | cross-sectional | **the first run** — every listing fetched is a price/mileage/year data point |
| "Are prices drifting down?" · "How long do these sit?" · "Do sellers cut?" | longitudinal | **weeks** — it needs repeat observations of the same cars |

So day one gives you deal grading; by week three you also get month-over-month medians, days
on market, and price-cut frequency. `python3 -m carmon market` shows all of it:

```
Median asking price by month
  2026-06  ████████████████████████████ $18,522  n=42
  2026-07  ███████████████████████████  $17,842  n=42    -680 (-3.7%)
  2026-08  ███████████████████████████  $17,876  n=42    +34 (+0.2%)

Days on market: median 21.0 (from 18 listings that have since vanished)
Price cuts: 14 of 126 tracked listings (11.1%), median cut $700 (3.9%)

By model
  model                          n     median                range   $/1k mi   days  cuts
  Honda Civic                   42    $19,120      $15,642–$22,236       116     18  12%
  Toyota Corolla                42    $18,353      $15,652–$21,808       120     24   9%
```

### How the estimate works

1. **Comparables** — same make and model, within ±1 model year, including cars that have since
   sold. Sold listings are the *best* evidence of a real market price; dropping them would bias
   the sample toward overpriced inventory that nobody bought.
2. **Fit** — weighted least squares of price against mileage and model year, weighting recent
   sightings more heavily (`market.recency_half_life_days`, default 45). With 12+ comparables it
   fits both variables; with 6+ it fits mileage alone; below that it falls back to the median
   and says so.
3. **Grade** — the gap between asking price and the fitted expectation: ≤−12% great deal, ≤−5%
   good, ±5% fair, ≥+5% above market, ≥+12% well above.
4. **Guards** — an estimate is clamped to stay near the observed price range so a wild
   extrapolation can't masquerade as a bargain, and a car is never compared against itself.

### What it will not pretend to know

Every grade ships with `sample_size`, `confidence` and `basis_level`, and they are not
decoration:

* **Confidence is capped by what the comparables actually are.** If no Kia Fortes are stored,
  the estimate falls back to other makes and confidence is forced to "very low" no matter how
  many cars are in the sample — a large sample of the wrong cars is not confidence.
* **`basis_level`** tells you which rung it used: `model_year` → `model` → `make` → `all`.
  Anything past `model` is a rough bearing, not a valuation.
* **It reads asking prices, not sale prices**, and it knows nothing about condition, trim,
  options, accident history or title status. A car priced 15% below the curve is often priced
  that way for a reason — it is a prompt to go look, not a verdict.

The comparison also feeds the score as a **`vs market`** component (up to ±1.5, full value at
12% off the expected price), which stays at 0 until there are at least 6 comparables.

---

Next: [optional scrapers](scrapers.md) · [website, API and MCP](interfaces.md)
