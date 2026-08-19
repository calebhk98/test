"""Market analysis: is this price actually a good deal, and which way is the market moving?

Two different questions, with two different data requirements — worth keeping straight:

* **"Is this listing priced well?"** is *cross-sectional*. Every listing already stored is a
  data point of price against mileage and model year, so this works from the very first run:
  fit price against mileage (and year) across comparable cars, then read off how far this
  particular listing sits below or above that curve.

* **"Which way are prices moving?"** is *longitudinal*. That needs weeks of history, and
  builds up as the daily job runs — monthly medians, how often sellers cut prices and by how
  much, and how long cars sit before they disappear.

Everything here is deterministic arithmetic over the local SQLite data — ordinary least
squares solved with Gaussian elimination, medians, and percentiles. No LLM, no external
service, no extra API calls. Sample sizes and a confidence label are reported alongside every
estimate, because an "expected price" drawn from four cars deserves to be read as such.
"""

from __future__ import annotations

import math
import sqlite3
import statistics
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Sample-size tiers: what the data can support.
MIN_ROWS_FULL = 12      # price ~ mileage + year
MIN_ROWS_MILEAGE = 6    # price ~ mileage
MIN_ROWS_MEDIAN = 3     # median of comparables

# Deal bands, by percentage below/above the expected price.
DEAL_BANDS = (
    (-12.0, "great deal", "🟢"),
    (-5.0, "good deal", "🟢"),
    (5.0, "fair price", "🟡"),
    (12.0, "above market", "🟠"),
    (float("inf"), "well above market", "🔴"),
)

CONFIDENCE_BANDS = (
    (5, "very low"),
    (11, "low"),
    (24, "moderate"),
    (float("inf"), "good"),
)


# --- small linear algebra (stdlib only) ---------------------------------
def _solve(matrix: List[List[float]], vector: List[float]) -> Optional[List[float]]:
    """Gaussian elimination with partial pivoting. None if the system is singular."""
    size = len(vector)
    augmented = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda r: abs(augmented[r][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            return None
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / augmented[column][column]
            for col in range(column, size + 1):
                augmented[row][col] -= factor * augmented[column][col]
    solution = [0.0] * size
    for row in reversed(range(size)):
        total = augmented[row][size] - sum(augmented[row][c] * solution[c] for c in range(row + 1, size))
        solution[row] = total / augmented[row][row]
    return solution


def weighted_least_squares(
    predictors: Sequence[Sequence[float]], targets: Sequence[float], weights: Optional[Sequence[float]] = None
) -> Optional[Dict[str, Any]]:
    """Fit targets ~ intercept + coefficients·predictors. Returns coefficients and r²."""
    rows = len(targets)
    if rows == 0 or not predictors:
        return None
    width = len(predictors[0]) + 1  # +1 for the intercept
    if rows < width + 1:
        return None
    weights = list(weights) if weights else [1.0] * rows
    design = [[1.0, *predictor] for predictor in predictors]

    normal = [[0.0] * width for _ in range(width)]
    right = [0.0] * width
    for row_index in range(rows):
        weight = weights[row_index]
        row = design[row_index]
        for i in range(width):
            right[i] += weight * row[i] * targets[row_index]
            for j in range(width):
                normal[i][j] += weight * row[i] * row[j]

    coefficients = _solve(normal, right)
    if coefficients is None or any(math.isnan(c) or math.isinf(c) for c in coefficients):
        return None

    weight_total = sum(weights) or 1.0
    mean = sum(w * t for w, t in zip(weights, targets)) / weight_total
    ss_total = sum(w * (t - mean) ** 2 for w, t in zip(weights, targets))
    ss_residual = 0.0
    for row_index in range(rows):
        predicted = sum(c * x for c, x in zip(coefficients, design[row_index]))
        ss_residual += weights[row_index] * (targets[row_index] - predicted) ** 2
    r_squared = 1.0 - (ss_residual / ss_total) if ss_total > 0 else 0.0
    return {"coefficients": coefficients, "r_squared": round(r_squared, 3), "n": rows}


# --- data access --------------------------------------------------------
def age_weight(last_seen: Optional[str], half_life_days: float, today: Optional[date] = None) -> float:
    """Recent observations count for more; a listing last seen `half_life_days` ago counts half."""
    if not last_seen or half_life_days <= 0:
        return 1.0
    try:
        seen = date.fromisoformat(str(last_seen)[:10])
    except ValueError:
        return 1.0
    age = max(0, ((today or date.today()) - seen).days)
    return 0.5 ** (age / half_life_days)


def comparables(
    conn: sqlite3.Connection,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    year_window: int = 1,
    include_sold: bool = True,
    exclude_vin: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Stored listings comparable to a given car.

    Sold/expired listings are included by default: a car that left the market is *better*
    market evidence than one still sitting unsold, and dropping them would bias the sample
    towards overpriced inventory.
    """
    clauses = ["price_current IS NOT NULL", "price_current > 0", "source != 'demo'"]
    params: List[Any] = []
    if make:
        clauses.append("LOWER(make) = LOWER(?)")
        params.append(make)
    if model:
        clauses.append("LOWER(model) LIKE LOWER(?)")
        params.append(f"{model}%")
    if year:
        clauses.append("year BETWEEN ? AND ?")
        params.extend([year - year_window, year + year_window])
    if not include_sold:
        clauses.append("active = 1")
    if exclude_vin:
        clauses.append("vin != ?")
        params.append(exclude_vin)
    rows = conn.execute(
        f"SELECT * FROM listings WHERE {' AND '.join(clauses)} ORDER BY last_seen DESC", params
    ).fetchall()
    return [dict(row) for row in rows]


def _usable(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [row for row in rows if row.get("price_current") and row.get("mileage") is not None]


# --- the estimate -------------------------------------------------------
@dataclass
class Appraisal:
    expected_price: Optional[float] = None
    actual_price: Optional[int] = None
    delta: Optional[float] = None          # negative = priced below the curve = good
    delta_pct: Optional[float] = None
    percentile: Optional[float] = None     # where this price sits among comparables
    sample_size: int = 0
    method: str = "none"
    confidence: str = "none"
    r_squared: Optional[float] = None
    dollars_per_1k_miles: Optional[float] = None
    dollars_per_model_year: Optional[float] = None
    comparable_median: Optional[float] = None
    comparable_range: Optional[Tuple[int, int]] = None
    grade: Optional[str] = None
    grade_icon: str = ""
    basis: str = ""
    basis_level: str = "none"   # model_year | model | make | all
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "expected_price": round(self.expected_price) if self.expected_price else None,
            "actual_price": self.actual_price,
            "delta": round(self.delta) if self.delta is not None else None,
            "delta_pct": round(self.delta_pct, 1) if self.delta_pct is not None else None,
            "percentile": round(self.percentile) if self.percentile is not None else None,
            "sample_size": self.sample_size,
            "method": self.method,
            "confidence": self.confidence,
            "r_squared": self.r_squared,
            "dollars_per_1k_miles": round(self.dollars_per_1k_miles, 1) if self.dollars_per_1k_miles else None,
            "dollars_per_model_year": round(self.dollars_per_model_year) if self.dollars_per_model_year else None,
            "comparable_median": round(self.comparable_median) if self.comparable_median else None,
            "comparable_range": list(self.comparable_range) if self.comparable_range else None,
            "grade": self.grade,
            "grade_icon": self.grade_icon,
            "basis": self.basis,
            "basis_level": self.basis_level,
            "notes": self.notes,
            "summary": self.summary(),
        }

    def summary(self) -> str:
        if self.expected_price is None:
            return f"Not enough comparable data yet ({self.sample_size} similar cars stored)."
        if self.actual_price is None:
            return (
                f"Expected about ${self.expected_price:,.0f} for this mileage and year, from "
                f"{self.sample_size} comparable listings ({self.confidence} confidence, {self.method})."
            )
        line = (
            f"{self.grade_icon} {self.grade}: ${self.actual_price:,.0f} versus an expected "
            f"${self.expected_price:,.0f} for this mileage and year "
            f"({self.delta:+,.0f}, {self.delta_pct:+.1f}%)."
        )
        line += f" Based on {self.sample_size} comparable listings ({self.confidence} confidence, {self.method})."
        if self.percentile is not None:
            line += f" Cheaper than {100 - self.percentile:.0f}% of them."
        if self.dollars_per_1k_miles:
            line += f" This market charges about ${self.dollars_per_1k_miles:,.0f} per 1,000 miles."
        return line


def _grade(delta_pct: float) -> Tuple[str, str]:
    return next((label, icon) for threshold, label, icon in DEAL_BANDS if delta_pct <= threshold)


def _confidence(sample_size: int) -> str:
    return next(label for threshold, label in CONFIDENCE_BANDS if sample_size < threshold)


def _percentile(price: float, prices: Sequence[float]) -> Optional[float]:
    if not prices:
        return None
    below = sum(1 for value in prices if value < price)
    return 100.0 * below / len(prices)


def appraise(
    conn: sqlite3.Connection,
    car: Dict[str, Any],
    config: Optional[Any] = None,
    today: Optional[date] = None,
) -> Appraisal:
    """Estimate what a car *should* cost given the local market, and grade its asking price.

    `car` needs make, model, year and mileage; add price_current to have it graded.
    """
    make, model = car.get("make"), car.get("model")
    year, mileage = car.get("year"), car.get("mileage")
    price = car.get("price_current")
    half_life = 45.0
    if config is not None:
        half_life = float(getattr(config, "data", {}).get("market", {}).get("recency_half_life_days", 45))

    result = Appraisal(actual_price=int(price) if price else None)

    rows = _usable(comparables(conn, make, model, year, year_window=1, exclude_vin=car.get("vin")))
    basis, basis_level = f"{make} {model} within ±1 model year", "model_year"
    if len(rows) < MIN_ROWS_MEDIAN:
        rows = _usable(comparables(conn, make, model, exclude_vin=car.get("vin")))
        basis, basis_level = f"{make} {model}, any year", "model"
    if len(rows) < MIN_ROWS_MEDIAN:
        rows = _usable(comparables(conn, make, exclude_vin=car.get("vin")))
        basis, basis_level = f"all {make} models", "make"
        if rows:
            result.notes.append(
                f"No {make} {model} comparables stored yet, so this compares against other {make} "
                "models — different cars, so read it as a rough bearing, not a valuation."
            )
    if len(rows) < MIN_ROWS_MEDIAN:
        rows = _usable(comparables(conn, exclude_vin=car.get("vin")))
        basis, basis_level = "every tracked listing (no comparables for this model)", "all"
        if rows:
            result.notes.append(
                "No comparables for this make at all, so this is measured against every tracked car — "
                "a different mix of models entirely. Treat it as a sanity check only, and let the daily "
                "job collect a few more days of data before trusting a grade."
            )

    result.sample_size = len(rows)
    result.basis = basis
    result.basis_level = basis_level
    # A large sample of the WRONG cars is not confidence. Cap it by how close the
    # comparables actually are to the car being priced.
    confidence = _confidence(len(rows))
    ceiling = {"model_year": None, "model": None, "make": "low", "all": "very low"}[basis_level]
    if ceiling:
        order = ["very low", "low", "moderate", "good"]
        confidence = order[min(order.index(confidence), order.index(ceiling))]
    result.confidence = confidence
    if not rows:
        result.notes.append("No comparable listings stored yet. Let the daily job run for a few days.")
        return result

    prices = [float(row["price_current"]) for row in rows]
    result.comparable_median = statistics.median(prices)
    result.comparable_range = (int(min(prices)), int(max(prices)))
    weights = [age_weight(row.get("last_seen"), half_life, today) for row in rows]

    fit = None
    if mileage is not None:
        years = [row.get("year") for row in rows]
        if len(rows) >= MIN_ROWS_FULL and year and all(years) and len(set(years)) > 1:
            fit = weighted_least_squares(
                [[float(row["mileage"]), float(row["year"])] for row in rows], prices, weights
            )
            if fit:
                intercept, per_mile, per_year = fit["coefficients"]
                result.expected_price = intercept + per_mile * float(mileage) + per_year * float(year)
                result.dollars_per_1k_miles = -per_mile * 1000
                result.dollars_per_model_year = per_year
                result.method = "price ~ mileage + model year"
        if fit is None and len(rows) >= MIN_ROWS_MILEAGE:
            fit = weighted_least_squares([[float(row["mileage"])] for row in rows], prices, weights)
            if fit:
                intercept, per_mile = fit["coefficients"]
                result.expected_price = intercept + per_mile * float(mileage)
                result.dollars_per_1k_miles = -per_mile * 1000
                result.method = "price ~ mileage"

    if fit is None:
        result.expected_price = result.comparable_median
        result.method = "median of comparables"
        result.notes.append(
            f"Only {len(rows)} comparable listing(s) — using their median rather than fitting a curve."
        )
    else:
        result.r_squared = fit["r_squared"]
        if fit["r_squared"] < 0.25:
            result.notes.append(
                f"Mileage and year explain only {fit['r_squared'] * 100:.0f}% of the price spread here, "
                "so trim and condition matter more than the curve does for this model."
            )

    # A fitted curve can wander outside anything sane on thin data; keep it inside the
    # observed range so a bad extrapolation cannot masquerade as a bargain.
    if result.expected_price is not None:
        low, high = min(prices), max(prices)
        span = max(500.0, (high - low) * 0.25)
        clamped = min(max(result.expected_price, low - span), high + span)
        if abs(clamped - result.expected_price) > 1:
            result.notes.append("Curve extrapolated beyond the observed price range; clamped to stay realistic.")
        result.expected_price = clamped

    if price and result.expected_price:
        result.delta = float(price) - result.expected_price
        result.delta_pct = 100.0 * result.delta / result.expected_price
        result.percentile = _percentile(float(price), prices)
        result.grade, result.grade_icon = _grade(result.delta_pct)
        if result.sample_size < MIN_ROWS_FULL:
            result.notes.append(
                f"{result.sample_size} comparable listing(s) is a thin sample — treat the grade as indicative."
            )
    return result


def appraise_vin(conn: sqlite3.Connection, vin: str, config: Optional[Any] = None) -> Optional[Appraisal]:
    row = conn.execute("SELECT * FROM listings WHERE vin = ?", (vin,)).fetchone()
    if row is None:
        return None
    return appraise(conn, dict(row), config)


# --- trends over time ---------------------------------------------------
def price_trend(
    conn: sqlite3.Connection,
    make: Optional[str] = None,
    model: Optional[str] = None,
    months: int = 6,
) -> List[Dict[str, Any]]:
    """Monthly price observations, newest month last.

    Built from `price_history`, which records a point the first time each VIN is seen and
    again whenever its price or mileage moves — so this reflects what the market was actually
    asking over time, not just what is listed today.
    """
    clauses = ["h.price IS NOT NULL", "h.price > 0", "l.source != 'demo'"]
    params: List[Any] = []
    if make:
        clauses.append("LOWER(l.make) = LOWER(?)")
        params.append(make)
    if model:
        clauses.append("LOWER(l.model) LIKE LOWER(?)")
        params.append(f"{model}%")
    rows = conn.execute(
        f"""
        SELECT substr(h.date, 1, 7) AS month, h.price AS price, h.mileage AS mileage, h.vin AS vin
        FROM price_history h JOIN listings l ON l.vin = h.vin
        WHERE {' AND '.join(clauses)}
        ORDER BY h.date ASC
        """,
        params,
    ).fetchall()

    buckets: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        bucket = buckets.setdefault(row["month"], {"month": row["month"], "prices": [], "mileages": [], "vins": set()})
        bucket["prices"].append(float(row["price"]))
        if row["mileage"] is not None:
            bucket["mileages"].append(float(row["mileage"]))
        bucket["vins"].add(row["vin"])

    series: List[Dict[str, Any]] = []
    for month in sorted(buckets)[-months:]:
        bucket = buckets[month]
        prices = bucket["prices"]
        series.append({
            "month": month,
            "observations": len(prices),
            "cars": len(bucket["vins"]),
            "median_price": round(statistics.median(prices)),
            "mean_price": round(statistics.fmean(prices)),
            "min_price": round(min(prices)),
            "max_price": round(max(prices)),
            "median_mileage": round(statistics.median(bucket["mileages"])) if bucket["mileages"] else None,
        })
    for index in range(1, len(series)):
        previous = series[index - 1]["median_price"]
        current = series[index]["median_price"]
        series[index]["change_vs_previous"] = round(current - previous)
        series[index]["change_pct"] = round(100.0 * (current - previous) / previous, 1) if previous else None
    return series


def days_on_market(conn: sqlite3.Connection, make: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """How long listings survive before they stop appearing (a proxy for how fast they sell)."""
    clauses = ["active = 0", "source != 'demo'", "first_seen IS NOT NULL", "last_seen IS NOT NULL"]
    params: List[Any] = []
    if make:
        clauses.append("LOWER(make) = LOWER(?)")
        params.append(make)
    if model:
        clauses.append("LOWER(model) LIKE LOWER(?)")
        params.append(f"{model}%")
    rows = conn.execute(
        f"SELECT julianday(last_seen) - julianday(first_seen) AS days FROM listings WHERE {' AND '.join(clauses)}",
        params,
    ).fetchall()
    spans = [float(row["days"]) for row in rows if row["days"] is not None]
    if not spans:
        return {"sample_size": 0, "median_days": None, "mean_days": None,
                "note": "No listings have disappeared yet — this fills in as cars sell."}
    return {
        "sample_size": len(spans),
        "median_days": round(statistics.median(spans), 1),
        "mean_days": round(statistics.fmean(spans), 1),
        "note": "Days between first and last sighting for listings that have since vanished "
                "(sold, or pulled). Only a lower bound for cars still listed.",
    }


def price_cut_stats(conn: sqlite3.Connection, make: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """How often sellers cut prices here, and by how much — useful for judging negotiating room."""
    clauses = ["l.source != 'demo'", "l.price_first_seen IS NOT NULL", "l.price_current IS NOT NULL"]
    params: List[Any] = []
    if make:
        clauses.append("LOWER(l.make) = LOWER(?)")
        params.append(make)
    if model:
        clauses.append("LOWER(l.model) LIKE LOWER(?)")
        params.append(f"{model}%")
    rows = conn.execute(
        f"SELECT l.price_first_seen AS first, l.price_current AS current FROM listings l "
        f"WHERE {' AND '.join(clauses)}",
        params,
    ).fetchall()
    if not rows:
        return {"tracked": 0, "cut_count": 0, "cut_share_pct": None, "median_cut": None, "median_cut_pct": None}
    cuts = [(float(r["first"]) - float(r["current"])) for r in rows if r["current"] < r["first"]]
    cut_pcts = [
        100.0 * (float(r["first"]) - float(r["current"])) / float(r["first"])
        for r in rows if r["current"] < r["first"] and r["first"]
    ]
    return {
        "tracked": len(rows),
        "cut_count": len(cuts),
        "cut_share_pct": round(100.0 * len(cuts) / len(rows), 1),
        "median_cut": round(statistics.median(cuts)) if cuts else None,
        "median_cut_pct": round(statistics.median(cut_pcts), 1) if cut_pcts else None,
        "largest_cut": round(max(cuts)) if cuts else None,
    }


def model_summary(conn: sqlite3.Connection, min_rows: int = 3) -> List[Dict[str, Any]]:
    """One row per make/model: sample size, price spread, depreciation slope, days on market."""
    rows = conn.execute(
        "SELECT DISTINCT make, model FROM listings WHERE source != 'demo' AND make IS NOT NULL "
        "AND model IS NOT NULL ORDER BY make, model"
    ).fetchall()
    summaries: List[Dict[str, Any]] = []
    for row in rows:
        make, model = row["make"], row["model"]
        listings = _usable(comparables(conn, make, model))
        if len(listings) < min_rows:
            continue
        prices = [float(item["price_current"]) for item in listings]
        mileages = [float(item["mileage"]) for item in listings]
        fit = weighted_least_squares([[m] for m in mileages], prices) if len(listings) >= MIN_ROWS_MILEAGE else None
        summaries.append({
            "make": make,
            "model": model,
            "sample_size": len(listings),
            "median_price": round(statistics.median(prices)),
            "min_price": round(min(prices)),
            "max_price": round(max(prices)),
            "median_mileage": round(statistics.median(mileages)),
            "dollars_per_1k_miles": round(-fit["coefficients"][1] * 1000, 1) if fit else None,
            "r_squared": fit["r_squared"] if fit else None,
            "days_on_market": days_on_market(conn, make, model),
            "price_cuts": price_cut_stats(conn, make, model),
        })
    summaries.sort(key=lambda item: item["sample_size"], reverse=True)
    return summaries


def best_deals(
    conn: sqlite3.Connection,
    limit: int = 10,
    min_sample: int = MIN_ROWS_MEDIAN,
    active_only: bool = True,
    config: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Active listings ranked by how far below their expected price they sit."""
    clauses = ["price_current IS NOT NULL", "source != 'demo'"]
    if active_only:
        clauses.append("active = 1")
    rows = conn.execute(f"SELECT * FROM listings WHERE {' AND '.join(clauses)}").fetchall()
    scored: List[Dict[str, Any]] = []
    for row in rows:
        listing = dict(row)
        result = appraise(conn, listing, config)
        if result.delta_pct is None or result.sample_size < min_sample:
            continue
        listing["appraisal"] = result.as_dict()
        scored.append(listing)
    scored.sort(key=lambda item: item["appraisal"]["delta_pct"])
    return scored[:limit]


def market_report(conn: sqlite3.Connection, months: int = 6, config: Optional[Any] = None) -> Dict[str, Any]:
    """Everything the market pages, CLI and MCP need in one call."""
    tracked = conn.execute(
        "SELECT COUNT(*) AS n FROM listings WHERE source != 'demo'"
    ).fetchone()["n"]
    return {
        "listings_tracked": int(tracked),
        "trend": price_trend(conn, months=months),
        "models": model_summary(conn),
        "days_on_market": days_on_market(conn),
        "price_cuts": price_cut_stats(conn),
        "best_deals": [
            {
                "vin": item["vin"], "year": item.get("year"), "make": item.get("make"),
                "model": item.get("model"), "trim": item.get("trim"),
                "price_current": item.get("price_current"), "mileage": item.get("mileage"),
                "score": item.get("score"), "listing_url": item.get("listing_url"),
                "appraisal": item["appraisal"],
            }
            for item in best_deals(conn, limit=10, config=config)
        ],
        "data_note": (
            "Price-versus-mileage comparisons work from the first run. Month-over-month trends, "
            "days-on-market and price-cut frequency need weeks of history — they fill in as the "
            "daily job keeps running."
        ),
    }
