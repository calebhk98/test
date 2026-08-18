# Cross-shopping sources

MarketCheck is the only thing v1 *queries*. These sites are covered as **deep links**
pre-filled with the criteria from `config.json` (2021+, under $20k, under 60k miles, within
100 miles of 38464) — they appear at the bottom of every daily digest, on the `/sources` page,
in `GET /api/sources`, and through the `list_sources` MCP tool.

Regenerate them any time with:

```bash
python3 -m carmon sources          # human-readable
python3 -m carmon sources --json   # grouped JSON
```

Change the ZIP, radius, price or mileage in `config.json` and every link updates with it.

---

## 1. Franchise dealer CPO programs

Manufacturer-backed CPO — the strongest warranty coverage of the three categories, since it's
backed by the automaker rather than a third party. Prices run a bit higher than the other two
lanes, but for "no repeat of 20 issues, 0 value" this is the lane to check first.

| Source | Why |
| --- | --- |
| Toyota Certified Used Vehicles | 12mo/12k comprehensive + 7yr/100k powertrain, 160-point inspection |
| Honda Certified Pre-Owned | 7yr/100k powertrain, non-powertrain extended 1yr/12k |
| Hyundai Certified Pre-Owned | remainder of 10yr/100k powertrain + 1yr/12k platinum coverage |
| Kia Certified Pre-Owned | 10yr/100k powertrain from original in-service date |
| Mazda Certified Pre-Owned | 12mo/12k limited + 7yr/100k powertrain |

The last three are here because Elantra, Forte and Mazda3 are on your preferred list — same
manufacturer-backed structure as Toyota/Honda.

Note how this interacts with scoring: CPO is worth **+2**, and it's what waives the −2 penalty
on the Nissan CVT models. A CPO Altima scores like a neutral car; a non-CPO one does not.

## 2. Big used-car retailers

No-haggle pricing (no negotiation) and a short return window — CarMax and Carvana both offer
7 days. CarMax also sells its own MaxCare extended coverage. Prices tend to sit slightly above
private-party or small independent dealers for the same car; that gap is what you pay for the
convenience and the inspection process.

CarMax · Carvana · Vroom (verify Vroom's current return policy before buying — it has changed).

## 3. Marketplace aggregators

These pull from thousands of dealers, so they're the best way to see the whole market and
compare one model across many sellers at once. CarGurus adds a **deal rating** (great / good /
fair / overpriced) based on how a listing compares to similar cars nationally — a genuinely
useful sanity check on whether a price is out of line. TrueCar shows what others actually paid.

CarGurus · Autotrader · Cars.com · TrueCar.

---

## If MarketCheck turns out not to be worth it

The free tier is 500 calls/month and a 100-mile radius. If coverage in the 38464 area is thin,
the fallback is a scraper for one or two of the sites above.

`carmon/scrapers/` already holds the seam for that: implement `ListingSource.fetch(search)`
to yield dicts shaped like `pipeline.normalize_listing()` output (vin, year, make, model, trim,
body_type, fuel_type, mileage, price_current, dealer_*, distance_miles, cpo, listing_url,
source) and register it. Storage, scoring, dedup, price history, the digest, the website, the
API and the MCP server all work unchanged — they never assume where a listing came from, and
`listings.source` records it per row.

Sources marked `"adapter": "stub"` in `python3 -m carmon sources --json` are the ones whose
listing pages are the most tractable to parse: Toyota/Honda certified inventory, CarMax,
Carvana, CarGurus, Autotrader, Cars.com.

**Before enabling any scraper, check that site's Terms of Service and `robots.txt`.** Several
of them prohibit automated collection outright, and some offer an official feed, partner
program or affiliate API that is the supported path — cheaper than fighting bot detection, and
it won't get the search blocked. v1 ships no adapters by design; the spec lists scraping these
sites as an explicit non-goal.
