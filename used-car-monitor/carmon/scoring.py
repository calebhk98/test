"""Deterministic listing scoring.

Two modes, selected by `scoring.mode` in config.json:

* ``step``   — the literal rules from the spec (+2 preferred, -2 caution unless CPO,
               +2 CPO, +1 price drop, -1 per 25mi past 50mi, -1 if mileage > 40k).
* ``smooth`` — the same rules made continuous (default), so 39,950 miles and 40,050
               miles score within a rounding error of each other while 60,000 miles
               is genuinely, proportionally worse.

Beyond the spec's original five rules, the score also weighs price against budget, model
year, EPA combined MPG, and NHTSA complaint/recall history. Every weight lives in
``config.json`` under ``scoring.weights``; the ``DEFAULT_WEIGHTS`` below are only a
fallback for keys a config omits (``tests/test_config_consistency.py`` keeps the two in
step).

Every component is returned with its own value and a human-readable explanation,
so nothing about the final number is hidden.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_WEIGHTS: Dict[str, float] = {
    "preferred_bonus": 2.0,
    "caution_penalty": -2.0,
    "cpo_bonus": 2.0,
    "price_drop_bonus_max": 1.5,
    "price_drop_full_bonus_pct": 3.0,
    "distance_free_miles": 50.0,
    "distance_penalty_per_miles": 25.0,
    "distance_penalty_floor": -3.0,
    "mileage_zero_penalty_at": 20000.0,
    "mileage_full_penalty_at": 60000.0,
    "mileage_full_penalty": -2.0,
    "price_bonus_max": 1.5,
    "price_full_bonus_at": 12000.0,
    "price_no_bonus_at": 20000.0,
    "year_bonus_max": 1.0,
    "year_no_bonus_at": 2021.0,
    "year_full_bonus_at": 2025.0,
    "mpg_bonus_max": 1.0,
    "mpg_no_bonus_at": 28.0,
    "mpg_full_bonus_at": 40.0,
    "mpg_min_factor": -0.5,
    "complaints_penalty_max": -1.5,
    "complaints_no_penalty_at": 100.0,
    "complaints_full_penalty_at": 600.0,
    "recall_penalty_each": -0.15,
    "recall_penalty_floor": -0.75,
    "market_bonus_max": 1.5,
    "market_full_bonus_pct": 12.0,
    "market_min_sample": 6.0,
}


def normalize(text: Optional[str]) -> str:
    """Lowercase and strip non-alphanumerics so 'Mazda3' == 'Mazda 3' == 'MAZDA-3'."""
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


@dataclass
class ScoreComponent:
    label: str
    value: float
    detail: str

    def as_dict(self) -> Dict[str, Any]:
        return {"label": self.label, "value": round(self.value, 3), "detail": self.detail}


@dataclass
class ScoreResult:
    score: float
    mode: str
    components: List[ScoreComponent] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 2),
            "mode": self.mode,
            "components": [c.as_dict() for c in self.components],
        }

    def explain(self) -> str:
        lines = [f"score {self.score:+.2f} ({self.mode} mode)"]
        for component in self.components:
            lines.append(f"  {component.value:+.2f}  {component.label}: {component.detail}")
        return "\n".join(lines)


def _matches(entries: Iterable[Dict[str, str]], make: str, model: str) -> Optional[Dict[str, str]]:
    """Match a make/model pair against a config list.

    A config model matches when the listing model starts with it, so 'Corolla' also
    catches 'Corolla Hatchback' but not an unrelated model. An entry with no model
    matches every model of that make.
    """
    listing_make, listing_model = normalize(make), normalize(model)
    for entry in entries or []:
        entry_make = normalize(entry.get("make"))
        entry_model = normalize(entry.get("model"))
        if entry_make and entry_make != listing_make:
            continue
        if entry_model and not listing_model.startswith(entry_model):
            continue
        if not entry_make and not entry_model:
            continue
        return entry
    return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def score_listing(listing: Dict[str, Any], scoring_config: Dict[str, Any] | None = None) -> ScoreResult:
    """Score one listing dict.

    Expected keys (all optional, missing values simply score 0 for that component):
    make, model, cpo (bool), mileage (int), distance_miles (float),
    price_current (int), price_first_seen (int).
    """
    scoring_config = scoring_config or {}
    mode = str(scoring_config.get("mode", "smooth")).lower()
    if mode not in ("smooth", "step"):
        mode = "smooth"
    weights = dict(DEFAULT_WEIGHTS)
    for key, value in (scoring_config.get("weights") or {}).items():
        try:
            weights[key] = float(value)
        except (TypeError, ValueError):
            # e.g. an "auto" marker that was never resolved (config.Config.scoring does that);
            # fall back to the default rather than crashing the run.
            continue

    make = listing.get("make") or ""
    model = listing.get("model") or ""
    cpo = bool(listing.get("cpo"))
    components: List[ScoreComponent] = []

    # 1. Preferred / caution make+model -----------------------------------
    preferred = _matches(scoring_config.get("preferred", []), make, model)
    caution = _matches(scoring_config.get("caution", []), make, model)
    if preferred:
        components.append(
            ScoreComponent(
                "preferred model",
                weights["preferred_bonus"],
                f"{make} {model} is on the preferred list",
            )
        )
    elif caution:
        reason = caution.get("reason", "on the caution list")
        if cpo:
            components.append(
                ScoreComponent(
                    "caution model (waived)",
                    0.0,
                    f"{make} {model} is a caution model ({reason}) but is manufacturer CPO, so no penalty",
                )
            )
        else:
            components.append(
                ScoreComponent(
                    "caution model",
                    weights["caution_penalty"],
                    f"{make} {model}: {reason}, and this listing is not CPO",
                )
            )
    else:
        components.append(ScoreComponent("model preference", 0.0, f"{make} {model} is neutral"))

    # 2. Certified Pre-Owned ---------------------------------------------
    if cpo:
        components.append(ScoreComponent("CPO", weights["cpo_bonus"], "listed as Certified Pre-Owned"))
    else:
        components.append(ScoreComponent("CPO", 0.0, "not certified pre-owned"))

    # 3. Price drop since first seen --------------------------------------
    price_now = listing.get("price_current")
    price_first = listing.get("price_first_seen")
    if price_now and price_first and price_first > 0 and price_now < price_first:
        drop = price_first - price_now
        drop_pct = 100.0 * drop / price_first
        if mode == "step":
            value = 1.0
            detail = f"price dropped ${drop:,.0f} (${price_first:,.0f} -> ${price_now:,.0f})"
        else:
            full_at = max(0.1, weights["price_drop_full_bonus_pct"])
            value = weights["price_drop_bonus_max"] * _clamp(drop_pct / full_at, 0.0, 1.0)
            detail = (
                f"price dropped ${drop:,.0f} ({drop_pct:.1f}%) since first seen "
                f"(${price_first:,.0f} -> ${price_now:,.0f}); full bonus at {full_at:.1f}%"
            )
        components.append(ScoreComponent("price drop", value, detail))
    else:
        components.append(ScoreComponent("price drop", 0.0, "no price drop since first seen"))

    # 4. Distance ---------------------------------------------------------
    distance = listing.get("distance_miles")
    free = weights["distance_free_miles"]
    per = max(1.0, weights["distance_penalty_per_miles"])
    if distance is None:
        components.append(ScoreComponent("distance", 0.0, "distance unknown"))
    else:
        distance = float(distance)
        extra = max(0.0, distance - free)
        if mode == "step":
            value = -1.0 * (int(extra) // int(per))
        else:
            value = -1.0 * (extra / per)
        value = max(weights["distance_penalty_floor"], value)
        components.append(
            ScoreComponent(
                "distance",
                value,
                f"{distance:.0f} mi away; first {free:.0f} mi free, then -1 per {per:.0f} mi",
            )
        )

    # 5. Mileage ----------------------------------------------------------
    mileage = listing.get("mileage")
    if mileage is None:
        components.append(ScoreComponent("mileage", 0.0, "mileage unknown"))
    else:
        mileage = float(mileage)
        if mode == "step":
            value = -1.0 if mileage > 40000 else 0.0
            detail = f"{mileage:,.0f} miles ({'over' if value else 'under'} the 40,000 mile line)"
        else:
            low = weights["mileage_zero_penalty_at"]
            high = max(low + 1.0, weights["mileage_full_penalty_at"])
            ramp = _clamp((mileage - low) / (high - low), 0.0, 1.0)
            value = weights["mileage_full_penalty"] * ramp
            detail = (
                f"{mileage:,.0f} miles; penalty ramps linearly from 0 at {low:,.0f} "
                f"to {weights['mileage_full_penalty']:.1f} at {high:,.0f} "
                f"(40,000 mi lands at {weights['mileage_full_penalty'] * _clamp((40000 - low) / (high - low), 0, 1):+.2f})"
            )
        components.append(ScoreComponent("mileage", value, detail))

    # 6. Price against budget ---------------------------------------------
    price = listing.get("price_current")
    if not price:
        components.append(ScoreComponent("price", 0.0, "price unknown"))
    else:
        price = float(price)
        cheap_at = weights["price_full_bonus_at"]
        dear_at = max(cheap_at + 1.0, weights["price_no_bonus_at"])
        if mode == "step":
            midpoint = (cheap_at + dear_at) / 2
            value = 1.0 if price <= midpoint else 0.0
            detail = f"${price:,.0f} ({'at or under' if value else 'over'} ${midpoint:,.0f})"
        else:
            ramp = _clamp((dear_at - price) / (dear_at - cheap_at), 0.0, 1.0)
            value = weights["price_bonus_max"] * ramp
            detail = (
                f"${price:,.0f}; bonus ramps from 0 at ${dear_at:,.0f} (budget ceiling) "
                f"to {weights['price_bonus_max']:+.2f} at ${cheap_at:,.0f}"
            )
        components.append(ScoreComponent("price", value, detail))

    # 7. Model year --------------------------------------------------------
    year = listing.get("year")
    if not year:
        components.append(ScoreComponent("model year", 0.0, "year unknown"))
    else:
        year = float(year)
        old_at = weights["year_no_bonus_at"]
        new_at = max(old_at + 1.0, weights["year_full_bonus_at"])
        if mode == "step":
            value = 1.0 if year >= (old_at + new_at) / 2 else 0.0
            detail = f"{year:.0f} model year"
        else:
            ramp = _clamp((year - old_at) / (new_at - old_at), 0.0, 1.0)
            value = weights["year_bonus_max"] * ramp
            detail = (
                f"{year:.0f}; bonus ramps from 0 at {old_at:.0f} to "
                f"{weights['year_bonus_max']:+.2f} at {new_at:.0f}"
            )
        components.append(ScoreComponent("model year", value, detail))

    # 8. Fuel economy (EPA combined) ---------------------------------------
    mpg = listing.get("combined_mpg")
    if not mpg:
        city, highway = listing.get("city_mpg"), listing.get("highway_mpg")
        if city and highway:
            mpg = 0.55 * float(city) + 0.45 * float(highway)
    if not mpg:
        components.append(
            ScoreComponent("fuel economy", 0.0, "no MPG data (MarketCheck and EPA both missing)")
        )
    else:
        mpg = float(mpg)
        thirsty_at = weights["mpg_no_bonus_at"]
        frugal_at = max(thirsty_at + 1.0, weights["mpg_full_bonus_at"])
        if mode == "step":
            value = 1.0 if mpg >= (thirsty_at + frugal_at) / 2 else 0.0
            detail = f"{mpg:.0f} mpg combined"
        else:
            ramp = _clamp((mpg - thirsty_at) / (frugal_at - thirsty_at), weights["mpg_min_factor"], 1.0)
            value = weights["mpg_bonus_max"] * ramp
            detail = (
                f"{mpg:.1f} mpg combined; 0 at {thirsty_at:.0f} mpg, "
                f"{weights['mpg_bonus_max']:+.2f} at {frugal_at:.0f} mpg, mildly negative below"
            )
        components.append(ScoreComponent("fuel economy", value, detail))

    # 9. NHTSA complaints ---------------------------------------------------
    complaints = listing.get("complaint_count")
    if complaints is None:
        components.append(ScoreComponent("NHTSA complaints", 0.0, "no NHTSA data for this model year"))
    else:
        complaints = float(complaints)
        quiet_at = weights["complaints_no_penalty_at"]
        loud_at = max(quiet_at + 1.0, weights["complaints_full_penalty_at"])
        top = listing.get("top_complaint_components") or []
        top_text = ""
        if isinstance(top, list) and top:
            first = top[0]
            if isinstance(first, (list, tuple)) and len(first) >= 2:
                top_text = f"; most common: {first[0]} ({first[1]})"
        if mode == "step":
            value = -1.0 if complaints > loud_at else 0.0
            detail = f"{complaints:,.0f} owner complaints filed with NHTSA{top_text}"
        else:
            ramp = _clamp((complaints - quiet_at) / (loud_at - quiet_at), 0.0, 1.0)
            value = weights["complaints_penalty_max"] * ramp
            detail = (
                f"{complaints:,.0f} owner complaints filed with NHTSA for this model year{top_text}; "
                f"penalty ramps from 0 at {quiet_at:,.0f} to {weights['complaints_penalty_max']:.2f} "
                f"at {loud_at:,.0f} (raw counts are not sales-volume adjusted)"
            )
        components.append(ScoreComponent("NHTSA complaints", value, detail))

    # 10. NHTSA recalls -----------------------------------------------------
    recalls = listing.get("recall_count")
    if recalls is None:
        components.append(ScoreComponent("NHTSA recalls", 0.0, "no NHTSA data for this model year"))
    else:
        recalls = int(recalls)
        if mode == "step":
            value = -0.5 if recalls >= 3 else 0.0
        else:
            value = max(weights["recall_penalty_floor"], weights["recall_penalty_each"] * recalls)
        detail = (
            f"{recalls} recall campaign(s) for this model year"
            + ("; check the VIN against NHTSA to see what is still unrepaired" if recalls else "")
        )
        components.append(ScoreComponent("NHTSA recalls", value, detail))

    # 11. Price versus the local market -------------------------------------
    delta_pct = listing.get("market_delta_pct")
    sample = listing.get("market_sample_size") or 0
    if delta_pct is None:
        components.append(
            ScoreComponent("vs market", 0.0, "no market comparison yet (needs comparable listings)")
        )
    elif sample < weights["market_min_sample"]:
        components.append(
            ScoreComponent(
                "vs market", 0.0,
                f"only {int(sample)} comparable listing(s) — too thin to score, "
                f"needs {int(weights['market_min_sample'])}",
            )
        )
    else:
        delta_pct = float(delta_pct)
        full_at = max(1.0, weights["market_full_bonus_pct"])
        if mode == "step":
            value = weights["market_bonus_max"] if delta_pct <= -5 else (
                -weights["market_bonus_max"] if delta_pct >= 5 else 0.0
            )
        else:
            value = weights["market_bonus_max"] * _clamp(-delta_pct / full_at, -1.0, 1.0)
        direction = "below" if delta_pct < 0 else "above"
        detail = (
            f"{abs(delta_pct):.1f}% {direction} the expected price for this model, mileage and year "
            f"({int(sample)} comparables); full ±{weights['market_bonus_max']:.1f} at {full_at:.0f}%"
        )
        grade = listing.get("market_grade")
        if grade:
            detail = f"{grade} — " + detail
        components.append(ScoreComponent("vs market", value, detail))

    total = sum(component.value for component in components)
    return ScoreResult(score=round(total, 2), mode=mode, components=components)


def score_to_json(result: ScoreResult) -> Dict[str, Any]:
    return result.as_dict()
