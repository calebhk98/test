"""JSON API handlers (the `/api/*` routes).

`ApiHandlers` is a mixin consumed by `carmon.web.routes.CarMonHandler`. Every method here
expects the handler's usual instance attributes (`self.config`, `self._env()`,
`self._send_json()`, `self._read_body_dict()`, `self._require_write_auth()`) to be
provided by that class -- this module only owns turning a request into a JSON payload.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import carmon
from .. import db, demo, market, quota
from ..config import get_secret
from ..nhtsa import recall_lookup_url, vin_recall_url
from ..result_shapes import count_envelope, nhtsa_urls, reliability_row_to_dict
from ..settings import (
    SettingsError,
    apply_changes,
    editable_settings,
    secrets_status,
    update_secrets,
    writes_allowed,
)
from ..sources import grouped_sources, sources_for_listing
from .forms import (
    ApiError,
    parse_bool,
    parse_float,
    parse_int,
    parse_str,
    secret_changes_from_body,
    settings_changes_from_body,
    since_date,
    truthy,
)


class ApiHandlers:
    # -- filter parsing shared by /api/listings and the dashboard --------
    def _search_kwargs(self, params: Dict[str, List[str]]) -> Dict[str, Any]:
        cpo_raw = params.get("cpo")
        return {
            "make": parse_str(params, "make"),
            "model": parse_str(params, "model"),
            "max_price": parse_int(params, "max_price"),
            "min_price": parse_int(params, "min_price"),
            "max_mileage": parse_int(params, "max_mileage"),
            "min_year": parse_int(params, "min_year"),
            "max_distance": parse_float(params, "max_distance"),
            "min_score": parse_float(params, "min_score"),
            "cpo_only": parse_bool(params, "cpo") if cpo_raw else False,
            "active_only": parse_bool(params, "active", default=True),
            "new_since": parse_str(params, "new_since"),
            "query": parse_str(params, "q"),
            "sort": parse_str(params, "sort") or "score",
        }

    # -- read-only JSON handlers -------------------------------------------
    def _api_health(self, conn: Any, params: Dict[str, List[str]]) -> None:
        self._send_json({
            "status": "ok",
            "version": carmon.__version__,
            "listings": db.count_listings(conn, active_only=True),
            "demo_listings": demo.demo_count(conn),
            "demo_warning": demo.demo_banner(conn),
        })

    def _api_stats(self, conn: Any, params: Dict[str, List[str]]) -> None:
        cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        data = db.stats(conn, monthly_cap=cap)
        data["pace"] = quota.pace_from_db(conn, cap)
        data["demo_listings"] = demo.demo_count(conn)
        data["demo_warning"] = demo.demo_banner(conn)
        self._send_json(data)

    def _api_quota(self, conn: Any, params: Dict[str, List[str]]) -> None:
        cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        metrics = quota.pace_from_db(conn, cap)
        payload = dict(metrics)
        payload["summary"] = quota.summary_line(metrics)
        payload["bar"] = quota.bar(metrics)
        self._send_json(payload)

    def _api_listings(self, conn: Any, params: Dict[str, List[str]]) -> None:
        kwargs = self._search_kwargs(params)
        limit = parse_int(params, "limit")
        offset = parse_int(params, "offset") or 0
        limit = 50 if limit is None else max(1, min(limit, 500))
        max_complaints = parse_int(params, "max_complaints")
        max_recalls = parse_int(params, "max_recalls")
        results = db.search_listings(conn, limit=limit, offset=offset, **kwargs)
        if max_complaints is not None or max_recalls is not None:
            results = self._filter_by_nhtsa(conn, results, max_complaints, max_recalls)
        filters = {k: v for k, v in kwargs.items() if v not in (None, False)}
        if max_complaints is not None:
            filters["max_complaints"] = max_complaints
        if max_recalls is not None:
            filters["max_recalls"] = max_recalls
        self._send_json(count_envelope("listings", results, limit=limit, offset=offset, filters=filters))

    def _filter_by_nhtsa(
        self,
        conn: Any,
        listings: List[Dict[str, Any]],
        max_complaints: Optional[int],
        max_recalls: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Drop listings whose cached NHTSA counts exceed the caps. Unknown (uncached) counts
        are never dropped -- absence of data is not evidence of a problem."""
        cache: Dict[Tuple[Any, Any, Any], Optional[Dict[str, Any]]] = {}
        kept = []
        for item in listings:
            make, model, year = item.get("make"), item.get("model"), item.get("year")
            key = (make, model, year)
            if key not in cache:
                cache[key] = db.get_reliability(conn, make, model, year) if make and model and year else None
            facts = cache[key]
            if facts:
                complaints, recalls = facts.get("complaint_count"), facts.get("recall_count")
                if max_complaints is not None and complaints is not None and complaints > max_complaints:
                    continue
                if max_recalls is not None and recalls is not None and recalls > max_recalls:
                    continue
            kept.append(item)
        return kept

    def _api_listing_detail(self, conn: Any, params: Dict[str, List[str]], vin: str) -> None:
        listing = db.get_listing(conn, vin)
        if listing is None:
            self._send_json({"error": f"unknown vin: {vin}"}, status=404)
            return
        listing = dict(listing)
        listing["price_history"] = db.get_price_history(conn, vin)
        listing["cross_shop"] = sources_for_listing(listing, self.config.search)
        try:
            from .. import pipeline
        except ImportError:
            pipeline = None  # type: ignore[assignment]
        if pipeline is not None:
            listing = pipeline.attach_cached_enrichment(conn, listing)
        make, model, year = listing.get("make"), listing.get("model"), listing.get("year")
        vin_url, model_url = nhtsa_urls(vin, make, model, year, vin_recall_url, recall_lookup_url)
        listing["nhtsa_vin_url"] = vin_url
        if model_url:
            listing["nhtsa_model_url"] = model_url
        appraisal = market.appraise_vin(conn, vin, self.config)
        listing["appraisal"] = appraisal.as_dict() if appraisal else None
        self._send_json(listing)

    def _api_reliability_detail(
        self, conn: Any, params: Dict[str, List[str]], make: str, model: str, year: str
    ) -> None:
        from urllib.parse import unquote

        make, model = unquote(make), unquote(model)
        try:
            year_int = int(unquote(year))
        except ValueError:
            raise ApiError(400, f"invalid year: {year!r}")
        record = db.get_reliability(conn, make, model, year_int)
        if record is None:
            self._send_json(
                {
                    "error": (
                        f"no cached NHTSA reliability data for {year_int} {make} {model}; "
                        "run `python3 -m carmon enrich` to fetch it"
                    )
                },
                status=404,
            )
            return
        record = dict(record)
        record["nhtsa_url"] = recall_lookup_url(make, model, year_int)
        self._send_json(record)

    def _api_reliability_list(self, conn: Any, params: Dict[str, List[str]]) -> None:
        rows = conn.execute("SELECT * FROM model_reliability ORDER BY complaint_count DESC").fetchall()
        models = [reliability_row_to_dict(row) for row in rows]
        self._send_json(count_envelope("models", models))

    def _api_listing_history(self, conn: Any, params: Dict[str, List[str]], vin: str) -> None:
        listing = db.get_listing(conn, vin)
        if listing is None:
            self._send_json({"error": f"unknown vin: {vin}"}, status=404)
            return
        self._send_json({"vin": vin, "history": db.get_price_history(conn, vin)})

    def _api_new(self, conn: Any, params: Dict[str, List[str]]) -> None:
        days = parse_int(params, "days") or 1
        limit = parse_int(params, "limit") or 25
        limit = max(1, min(limit, 500))
        since = since_date(days)
        listings = db.new_listings_since(conn, since, limit=limit)
        self._send_json(count_envelope("listings", listings, days=days, since=since))

    def _api_price_drops(self, conn: Any, params: Dict[str, List[str]]) -> None:
        days = parse_int(params, "days") or 1
        limit = parse_int(params, "limit") or 25
        limit = max(1, min(limit, 500))
        since = since_date(days)
        listings = db.price_drops_since(conn, since, limit=limit)
        self._send_json(count_envelope("listings", listings, days=days, since=since))

    def _api_top(self, conn: Any, params: Dict[str, List[str]]) -> None:
        limit = parse_int(params, "limit") or 5
        limit = max(1, min(limit, 500))
        listings = db.search_listings(conn, sort="score", limit=limit)
        self._send_json(count_envelope("listings", listings))

    def _api_digest_latest(self, conn: Any, params: Dict[str, List[str]]) -> None:
        path, markdown = self._latest_digest()
        self._send_json({"path": str(path) if path else None, "markdown": markdown})

    def _api_sources(self, conn: Any, params: Dict[str, List[str]]) -> None:
        self._send_json({"categories": grouped_sources(self.config.search)})

    def _api_config(self, conn: Any, params: Dict[str, List[str]]) -> None:
        self._send_json(self.config.to_dict())

    def _api_runs(self, conn: Any, params: Dict[str, List[str]]) -> None:
        limit = parse_int(params, "limit") or 10
        limit = max(1, min(limit, 500))
        runs = db.recent_runs(conn, limit=limit)
        self._send_json(count_envelope("runs", runs))

    def _api_market(self, conn: Any, params: Dict[str, List[str]]) -> None:
        months = parse_int(params, "months") or 6
        months = max(1, min(months, 36))
        self._send_json(market.market_report(conn, months=months, config=self.config))

    def _api_market_trend(self, conn: Any, params: Dict[str, List[str]]) -> None:
        make = parse_str(params, "make")
        model = parse_str(params, "model")
        months = parse_int(params, "months") or 6
        months = max(1, min(months, 36))
        self._send_json({
            "make": make,
            "model": model,
            "trend": market.price_trend(conn, make=make, model=model, months=months),
        })

    def _api_appraise(self, conn: Any, params: Dict[str, List[str]]) -> None:
        car = {
            "make": parse_str(params, "make"),
            "model": parse_str(params, "model"),
            "year": parse_int(params, "year"),
            "mileage": parse_int(params, "mileage"),
            "price_current": parse_int(params, "price"),
        }
        result = market.appraise(conn, car, self.config)
        self._send_json(result.as_dict())

    def _api_deals(self, conn: Any, params: Dict[str, List[str]]) -> None:
        limit = parse_int(params, "limit") or 10
        limit = max(1, min(limit, 200))
        deals = market.best_deals(conn, limit=limit, config=self.config)
        self._send_json(count_envelope("deals", deals))

    # -- scraper adapters ---------------------------------------------------
    def _scrapers_overview(self, conn: Any) -> Dict[str, Any]:
        """Shared by GET /api/scrapers and the /scrapers page: merge REGISTRY metadata, the
        config toggles and the scraper_status history so an adapter with no run history yet
        still shows up (never silently omitted)."""
        try:
            from ..scrapers import REGISTRY
        except ImportError:
            REGISTRY: Dict[str, Any] = {}  # tolerate an empty/unavailable registry

        scraper_cfg = self.config.data.get("scrapers", {}) or {}
        enabled_sources = scraper_cfg.get("sources", {}) or {}
        status_rows = {row["source"]: row for row in db.get_scraper_status(conn)}
        keys = sorted(set(REGISTRY) | set(enabled_sources) | set(status_rows))

        adapters = []
        for key in keys:
            cls = REGISTRY.get(key)
            status = status_rows.get(key) or {}
            adapters.append({
                "key": key,
                "name": getattr(cls, "name", key) if cls else key,
                "site": getattr(cls, "site", "") if cls else "",
                "kind": getattr(cls, "kind", "listings") if cls else "listings",
                "registered": cls is not None,
                "enabled": bool(enabled_sources.get(key)),
                "status": status.get("status") or "never run",
                "message": status.get("message"),
                "last_run_at": status.get("last_run_at"),
                "pages": status.get("pages") or 0,
                "listings": status.get("listings") or 0,
                "kept": status.get("kept") or 0,
                "ok_runs": status.get("ok_runs") or 0,
                "failed_runs": status.get("failed_runs") or 0,
                "last_ok_at": status.get("last_ok_at"),
                "last_error": status.get("last_error"),
                "last_error_at": status.get("last_error_at"),
            })

        limits = {k: v for k, v in scraper_cfg.items() if k not in ("sources", "enabled")}
        return {
            "enabled": bool(scraper_cfg.get("enabled")),
            "limits": limits,
            "usage_today": db.scrape_usage_today(conn),
            "by_source": db.scrape_usage_by_source(conn),
            "adapters": adapters,
        }

    def _api_scrapers(self, conn: Any, params: Dict[str, List[str]]) -> None:
        self._send_json(self._scrapers_overview(conn))

    def _api_scrapers_events(self, conn: Any, params: Dict[str, List[str]]) -> None:
        limit = parse_int(params, "limit") or 25
        limit = max(1, min(limit, 200))
        source = parse_str(params, "source")
        events = db.recent_scrape_events(conn, limit=limit, source=source)
        self._send_json(count_envelope("events", events))

    def _api_scrapers_run(self, conn: Any, params: Dict[str, List[str]]) -> None:
        body = self._read_body_dict()
        self._require_write_auth(body)
        try:
            from .. import pipeline
        except ImportError:
            pipeline = None  # type: ignore[assignment]
        if pipeline is None:
            raise ApiError(501, "pipeline module is unavailable")
        source = (body.get("source") or "").strip() or None
        dry_run = truthy(body.get("dry_run"))
        summary = pipeline.run_scrapers(self.config, conn, sources=[source] if source else None, dry_run=dry_run)
        self._send_json(summary)

    def _api_scrapers_probe(self, conn: Any, params: Dict[str, List[str]]) -> None:
        body = self._read_body_dict()
        self._require_write_auth(body)
        try:
            from .. import pipeline
        except ImportError:
            pipeline = None  # type: ignore[assignment]
        if pipeline is None:
            raise ApiError(501, "pipeline module is unavailable")
        results = pipeline.probe_scrapers(self.config, conn)
        self._send_json(count_envelope("results", results))

    def _api_scrapers_toggle(self, conn: Any, params: Dict[str, List[str]]) -> None:
        body = self._read_body_dict()
        self._require_write_auth(body)
        result = self._apply_scraper_toggle(body)
        self._send_json(result)

    def _apply_scraper_toggle(self, body: Dict[str, Any]) -> Dict[str, Any]:
        source = (body.get("source") or "").strip() or None
        enabled = truthy(body.get("enabled"))
        dotted = f"scrapers.sources.{source}" if source else "scrapers.enabled"
        try:
            return apply_changes(self.config, {dotted: enabled})
        except SettingsError as exc:
            raise ApiError(400, str(exc))

    # -- settings ---------------------------------------------------------
    def _api_settings_get(self, conn: Any, params: Dict[str, List[str]]) -> None:
        token = get_secret("CARMON_API_TOKEN", env=self._env())
        allowed, reason = writes_allowed(self.server.server_address[0] or None, token)
        self._send_json({
            "fields": editable_settings(self.config),
            "secrets": secrets_status(),
            "writable": allowed,
            "reason": reason,
        })

    def _api_settings_post(self, conn: Any, params: Dict[str, List[str]]) -> None:
        body = self._read_body_dict()
        self._require_write_auth(body)
        changes, dry_run = settings_changes_from_body(self.config, body, editable_settings)
        try:
            result = apply_changes(self.config, changes, dry_run=dry_run)
        except SettingsError as exc:
            raise ApiError(400, str(exc))
        self._send_json(result)

    def _api_settings_secrets_post(self, conn: Any, params: Dict[str, List[str]]) -> None:
        body = self._read_body_dict()
        self._require_write_auth(body)
        changes = secret_changes_from_body(body)
        if not changes:
            raise ApiError(400, "no secret changes supplied")
        try:
            result = update_secrets(changes)
        except SettingsError as exc:
            raise ApiError(400, str(exc))
        self._send_json(result)

    def _latest_digest(self) -> Tuple[Optional[Path], Optional[str]]:
        try:
            from .. import digest as digest_module
        except ImportError:
            return None, None
        latest_fn = getattr(digest_module, "latest_digest_path", None)
        if latest_fn is None:
            return None, None
        path = latest_fn(self.config)
        if not path:
            return None, None
        path = Path(path)
        try:
            return path, path.read_text(encoding="utf-8")
        except OSError:
            return path, None
