"""Configuration loading: config.json for search/scoring knobs, .env for secrets."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


class ConfigError(RuntimeError):
    """Raised when configuration is missing or malformed."""


def load_env(env_path: Path | str | None = None) -> Dict[str, str]:
    """Read a simple KEY=VALUE .env file into a dict (does not overwrite real env vars).

    Values already present in os.environ win, so `MARKETCHECK_API_KEY=... python -m carmon`
    works the same as putting the key in .env.
    """
    path = Path(env_path) if env_path else DEFAULT_ENV_PATH
    values: Dict[str, str] = {}
    if path.exists():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            values[key.strip()] = value
    for key in ("MARKETCHECK_API_KEY", "DISCORD_WEBHOOK_URL", "CARMON_API_TOKEN"):
        env_value = os.environ.get(key)
        if env_value:
            values[key] = env_value
    return values


def get_secret(name: str, env: Dict[str, str] | None = None, required: bool = False) -> str:
    env = env if env is not None else load_env()
    value = (env.get(name) or "").strip()
    if required and not value:
        raise ConfigError(
            f"{name} is not set. Copy .env.example to .env and fill it in "
            f"(or export {name} in your shell)."
        )
    return value


# Weights that must always agree with the search criteria. Setting one of these to
# "auto" in config.json (the default) derives it from `search`, so a budget or mileage
# ceiling is defined in exactly one place and can never drift out of step.
AUTO_DERIVED_WEIGHTS: Dict[str, str] = {
    "price_no_bonus_at": "price_max",
    "mileage_full_penalty_at": "mileage_max",
    "year_no_bonus_at": "year_min",
    "distance_penalty_floor": "",  # not derived; listed here only for documentation
}
AUTO_DERIVED_WEIGHTS = {key: value for key, value in AUTO_DERIVED_WEIGHTS.items() if value}


class Config:
    """Thin wrapper around the parsed config.json with convenience accessors."""

    def __init__(self, data: Dict[str, Any], path: Path | None = None):
        self.data = data
        self.path = path

    # --- sections -------------------------------------------------------
    @property
    def search(self) -> Dict[str, Any]:
        return self.data.setdefault("search", {})

    @property
    def scoring(self) -> Dict[str, Any]:
        """Scoring config with "auto" weights resolved from the search criteria."""
        scoring = self.data.setdefault("scoring", {})
        weights = dict(scoring.get("weights") or {})
        search = self.data.get("search", {})
        for weight_key, search_key in AUTO_DERIVED_WEIGHTS.items():
            value = weights.get(weight_key)
            if value is None or (isinstance(value, str) and value.strip().lower() == "auto"):
                derived = search.get(search_key)
                if derived is not None:
                    weights[weight_key] = float(derived)
                else:
                    weights.pop(weight_key, None)
        resolved = dict(scoring)
        resolved["weights"] = weights
        return resolved

    @property
    def scoring_raw(self) -> Dict[str, Any]:
        """The scoring section exactly as written in config.json, "auto" markers intact."""
        return self.data.setdefault("scoring", {})

    @property
    def api(self) -> Dict[str, Any]:
        return self.data.setdefault("api", {})

    @property
    def digest(self) -> Dict[str, Any]:
        return self.data.setdefault("digest", {})

    @property
    def web(self) -> Dict[str, Any]:
        return self.data.setdefault("web", {})

    @property
    def paths(self) -> Dict[str, Any]:
        return self.data.setdefault("paths", {})

    # --- resolved paths -------------------------------------------------
    def _resolve(self, value: str) -> Path:
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            return candidate
        return (PROJECT_ROOT / candidate).resolve()

    @property
    def db_path(self) -> Path:
        return self._resolve(self.paths.get("db", "data/carmon.db"))

    @property
    def digest_dir(self) -> Path:
        return self._resolve(self.paths.get("digest_dir", "data/digests"))

    def to_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self.data)


def load_config(path: Path | str | None = None) -> Config:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Config file {config_path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Config file {config_path} must contain a JSON object")
    return Config(data, config_path)


def validate_config(config: "Config") -> List[str]:
    """Report configuration problems and single-source-of-truth drift.

    Returns a list of human-readable warnings (empty means everything checks out).
    Surfaced by `python3 -m carmon config-check` and printed before every daily run.
    """
    from .scoring import DEFAULT_WEIGHTS  # imported here to avoid a circular import

    warnings: List[str] = []
    search = config.data.get("search", {})
    scoring = config.data.get("scoring", {})
    weights = scoring.get("weights") or {}

    for section in ("search", "scoring", "api", "digest", "paths"):
        if section not in config.data:
            warnings.append(f"config.json is missing the '{section}' section")

    unknown = sorted(set(weights) - set(DEFAULT_WEIGHTS))
    if unknown:
        warnings.append(
            f"scoring.weights has unknown key(s): {', '.join(unknown)} — they are ignored. "
            "Check for a typo against carmon/scoring.py DEFAULT_WEIGHTS."
        )

    mode = str(scoring.get("mode", "smooth")).lower()
    if mode not in ("smooth", "step"):
        warnings.append(f"scoring.mode '{mode}' is not recognised; falling back to 'smooth'")

    radius = search.get("radius_miles")
    if radius and float(radius) > 100:
        warnings.append(
            f"search.radius_miles is {radius}, above the MarketCheck free-tier limit of 100 "
            "— requests will be clamped to 100."
        )

    cap = config.data.get("api", {}).get("monthly_call_cap")
    if cap and int(cap) > 500:
        warnings.append(
            f"api.monthly_call_cap is {cap}, above the free tier's 500 calls/month. "
            "Only raise this if you have actually upgraded the MarketCheck plan."
        )

    # Drift between weights that are meant to track the search criteria.
    for weight_key, search_key in AUTO_DERIVED_WEIGHTS.items():
        raw = weights.get(weight_key)
        expected = search.get(search_key)
        if raw is None or (isinstance(raw, str) and raw.strip().lower() == "auto"):
            continue
        if expected is not None and float(raw) != float(expected):
            warnings.append(
                f"scoring.weights.{weight_key} ({raw}) disagrees with search.{search_key} ({expected}). "
                f'Set it to "auto" to derive it from the search criteria instead of repeating the number.'
            )

    scrapers = config.data.get("scrapers", {}) or {}
    if scrapers.get("enabled"):
        on = [key for key, value in (scrapers.get("sources") or {}).items() if value]
        warnings.append(
            "scrapers.enabled is true"
            + (f" with {', '.join(on)} switched on. " if on else " but no source is switched on. ")
            + "Check each site's Terms of Service; robots.txt is always obeyed and daily caps apply."
        )
        if int(scrapers.get("max_listings_per_day", 100)) > 500:
            warnings.append(
                f"scrapers.max_listings_per_day is {scrapers['max_listings_per_day']} — that is a lot of "
                "traffic for a personal search. Consider keeping it near the 100 default."
            )

    if search.get("include_electric_hybrid") and search.get("excluded_fuel_types"):
        warnings.append(
            "search.include_electric_hybrid is true, so search.excluded_fuel_types is not applied."
        )

    return warnings
