"""Deterministic listing scoring.

Two modes, selected by `scoring.mode` in config.json:

* ``step``   — the literal rules from the spec (+2 preferred, -2 caution unless CPO,
               +2 CPO, +1 price drop, -1 per 25mi past 50mi, -1 if mileage > 40k).
* ``smooth`` — the same rules made continuous (default), so 39,950 miles and 40,050
               miles score within a rounding error of each other while 60,000 miles
               is genuinely, proportionally worse.

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
    weights.update({k: float(v) for k, v in (scoring_config.get("weights") or {}).items()})

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

    total = sum(component.value for component in components)
    return ScoreResult(score=round(total, 2), mode=mode, components=components)


def score_to_json(result: ScoreResult) -> Dict[str, Any]:
    return result.as_dict()
