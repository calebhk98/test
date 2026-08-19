"""NHTSA Complaints and Recalls — free, public, no API key.

Endpoints (api.nhtsa.gov):
  * recalls    GET /recalls/recallsByVehicle?make=&model=&modelYear=      -> {"Count": n, "results": [...]}
  * complaints GET /complaints/complaintsByVehicle?make=&model=&modelYear= -> {"count": n, "results": [...]}
  * VIN decode GET https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json

Note the inconsistent casing in NHTSA's own responses ("Count" vs "count") — both are
handled. This is consumer-filed defect complaints and manufacturer recall campaigns: the
same federal data every third-party reliability site repackages. It gives raw counts and
descriptions, not a friendly 1-5 score.

**Read complaint counts with care.** They are not volume-adjusted: a Corolla has more
complaints than a Forte partly because there are far more Corollas on the road. Treat the
number as a soft signal and lean on *which components* recur and on unrepaired recalls.
That is why the reliability weight in `config.json` is deliberately small.

Results are cached in the `model_reliability` table, so a model/year is fetched once per
`enrichment.cache_days` (default 30) no matter how many listings share it.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests

from . import db

LOG = logging.getLogger("carmon.nhtsa")

RECALLS_URL = "https://api.nhtsa.gov/recalls/recallsByVehicle"
COMPLAINTS_URL = "https://api.nhtsa.gov/complaints/complaintsByVehicle"
VIN_DECODE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}"


class NHTSAError(RuntimeError):
    pass


def recall_lookup_url(make: str, model: str, year: int) -> str:
    """Human-facing NHTSA page for the same query (for digests and the website)."""
    return (
        "https://www.nhtsa.gov/recalls?"
        f"vehicleMake={quote(str(make))}&vehicleModel={quote(str(model))}&vehicleYear={year}"
    )


def vin_recall_url(vin: str) -> str:
    return f"https://www.nhtsa.gov/recalls?vin={quote(str(vin))}"


class NHTSAClient:
    """Thin, polite client. No API key exists for this service and none is needed."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        enrichment_config: Optional[Dict[str, Any]] = None,
        session: Optional[Any] = None,
    ):
        config = enrichment_config or {}
        self.conn = conn
        self.session = session or requests.Session()
        self.timeout = int(config.get("timeout_seconds", 20))
        self.cache_days = int(config.get("cache_days", 30))
        self.max_retries = int(config.get("max_retries", 2))
        self.min_interval = float(config.get("min_seconds_between_calls", 0.25))
        self.max_recalls_stored = int(config.get("max_recalls_stored", 10))
        self.calls_made = 0
        self._last_call_at = 0.0

    def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        attempt = 0
        while True:
            attempt += 1
            elapsed = time.monotonic() - self._last_call_at
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self._last_call_at = time.monotonic()
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except Exception as exc:
                if attempt > self.max_retries:
                    raise NHTSAError(f"NHTSA request failed: {exc}") from exc
                time.sleep(min(8, 2 ** attempt))
                continue
            self.calls_made += 1
            status = getattr(response, "status_code", 0)
            if status == 200:
                try:
                    return response.json() or {}
                except ValueError as exc:
                    raise NHTSAError(f"NHTSA returned non-JSON: {getattr(response, 'text', '')[:200]}") from exc
            if status == 400:
                # The recalls endpoint answers HTTP 400 with a perfectly valid
                # {"Count": 0, "Message": "Results returned successfully", "results": []}
                # body when a model-year simply has no recall campaigns. That is an
                # empty result, not an error, so accept any 400 that carries a count.
                try:
                    payload = response.json() or {}
                except ValueError:
                    payload = {}
                if isinstance(payload, dict) and ("Count" in payload or "count" in payload):
                    return payload
            if status in (429,) or 500 <= status < 600:
                if attempt > self.max_retries:
                    raise NHTSAError(f"NHTSA HTTP {status} after {attempt} attempts")
                time.sleep(min(8, 2 ** attempt))
                continue
            raise NHTSAError(f"NHTSA HTTP {status}: {getattr(response, 'text', '')[:200]}")

    # --- raw endpoints ---------------------------------------------------
    def recalls(self, make: str, model: str, year: int) -> List[Dict[str, Any]]:
        payload = self._get(RECALLS_URL, {"make": make, "model": model, "modelYear": year})
        return payload.get("results") or []

    def complaints(self, make: str, model: str, year: int) -> List[Dict[str, Any]]:
        payload = self._get(COMPLAINTS_URL, {"make": make, "model": model, "modelYear": year})
        return payload.get("results") or []

    def decode_vin(self, vin: str) -> Dict[str, Any]:
        payload = self._get(VIN_DECODE_URL.format(vin=quote(vin)), {"format": "json"})
        results = payload.get("Results") or []
        return results[0] if results else {}

    # --- the useful bit --------------------------------------------------
    def facts_for(
        self, make: str, model: str, year: int, force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Complaint/recall summary for a model-year, cached in SQLite.

        Returns None only if NHTSA could not be reached and nothing is cached — callers
        treat that as "no reliability signal" rather than an error, so a network hiccup
        never fails the daily run.
        """
        if not make or not model or not year:
            return None
        if not force_refresh:
            cached = db.get_reliability(self.conn, make, model, year, max_age_days=self.cache_days)
            if cached:
                return cached

        # The two endpoints fail independently: a recalls outage must not throw away
        # perfectly good complaint data (and vice versa).
        complaints: Optional[List[Dict[str, Any]]] = None
        recalls: Optional[List[Dict[str, Any]]] = None
        errors: List[str] = []
        try:
            complaints = self.complaints(make, model, year)
        except NHTSAError as exc:
            errors.append(f"complaints: {exc}")
        try:
            recalls = self.recalls(make, model, year)
        except NHTSAError as exc:
            errors.append(f"recalls: {exc}")
        if errors:
            LOG.warning("NHTSA partial failure for %s %s %s: %s", year, make, model, "; ".join(errors))
        if complaints is None and recalls is None:
            return db.get_reliability(self.conn, make, model, year)
        complaints = complaints or []
        recalls = recalls or []

        components: Counter[str] = Counter()
        crashes = fires = injuries = deaths = 0
        for complaint in complaints:
            for component in str(complaint.get("components") or "").split(","):
                component = component.strip()
                if component and component.upper() not in ("UNKNOWN OR OTHER", ""):
                    components[component] += 1
            crashes += 1 if complaint.get("crash") else 0
            fires += 1 if complaint.get("fire") else 0
            injuries += int(complaint.get("numberOfInjuries") or 0)
            deaths += int(complaint.get("numberOfDeaths") or 0)

        facts = {
            "complaint_count": len(complaints),
            "recall_count": len(recalls),
            "crash_complaints": crashes,
            "fire_complaints": fires,
            "injuries": injuries,
            "deaths": deaths,
            "top_components": components.most_common(5),
            "recalls": [
                {
                    "campaign": recall.get("NHTSACampaignNumber"),
                    "component": recall.get("Component"),
                    "summary": (recall.get("Summary") or "")[:400],
                    "consequence": (recall.get("Consequence") or "")[:300],
                    "remedy": (recall.get("Remedy") or "")[:300],
                    "report_date": recall.get("ReportReceivedDate"),
                    "park_it": bool(recall.get("parkIt")),
                    "park_outside": bool(recall.get("parkOutSide")),
                }
                for recall in recalls[: self.max_recalls_stored]
            ],
            "source": "nhtsa",
        }
        db.save_reliability(self.conn, make, model, year, facts)
        stored = db.get_reliability(self.conn, make, model, year)
        if stored is not None:
            # `partial` is a property of this fetch, not of the cached row.
            stored["partial"] = bool(errors)
        return stored


def enrich_models(
    conn: sqlite3.Connection,
    model_years: List[Dict[str, Any]],
    enrichment_config: Optional[Dict[str, Any]] = None,
    client: Optional[NHTSAClient] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Fetch NHTSA facts for a list of {make, model, year} dicts. Never raises."""
    client = client or NHTSAClient(conn, enrichment_config)
    updated, skipped = 0, 0
    newly_seen: List[str] = []
    for entry in model_years:
        make, model, year = entry.get("make"), entry.get("model"), entry.get("year")
        was_cached = db.get_reliability(conn, make, model, year) is not None
        facts = client.facts_for(make, model, year, force_refresh)
        if facts:
            updated += 1
            if not was_cached:
                # A model-year we had never looked up before — worth naming in the digest.
                newly_seen.append(
                    f"{year} {make} {model} ({facts.get('complaint_count', 0)} complaints, "
                    f"{facts.get('recall_count', 0)} recalls)"
                )
        else:
            skipped += 1
    return {
        "models": len(model_years), "updated": updated, "skipped": skipped,
        "api_calls": client.calls_made, "new_models": newly_seen,
    }
