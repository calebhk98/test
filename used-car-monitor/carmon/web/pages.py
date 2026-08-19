"""HTML page handlers (everything that is not under `/api/`).

`PageHandlers` is a mixin consumed by `carmon.web.routes.CarMonHandler`, alongside
`carmon.web.api.ApiHandlers` (for `_search_kwargs`, `_latest_digest`, `_scrapers_overview`
and `_apply_scraper_toggle`, which the scrapers/settings pages reuse rather than
duplicate) and the response/auth helpers defined directly on `CarMonHandler`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .. import db, demo, market, quota
from ..config import get_secret
from ..nhtsa import recall_lookup_url, vin_recall_url
from ..result_shapes import nhtsa_urls
from ..settings import (
    SettingsError,
    apply_changes,
    editable_settings,
    secrets_status,
    update_secrets,
    writes_allowed,
)
from ..sources import grouped_sources, sources_for_listing
from . import render
from .forms import ApiError, parse_bool, parse_int, parse_str, secret_changes_from_body, settings_changes_from_body, since_date, truthy
from .render import e, fmt_money, fmt_mpg, fmt_num, score_class


class PageHandlers:
    # -- dashboard ----------------------------------------------------------
    def _page_dashboard(self, conn: Any, params: Dict[str, List[str]]) -> None:
        cap = int(self.config.api.get("monthly_call_cap", 500) or 500)
        stats = db.stats(conn, monthly_cap=cap)
        new_today = len(db.new_listings_since(conn, since_date(0), limit=500))
        drops_today = len(db.price_drops_since(conn, since_date(0), limit=500))
        nhtsa_model_years = conn.execute("SELECT COUNT(*) AS n FROM model_reliability").fetchone()["n"]

        kwargs = self._search_kwargs(params)
        sort = kwargs.get("sort") or "score"
        resolved_sort = sort if sort in db.SORTABLE else "score"
        try:
            listings = db.search_listings(conn, limit=200, offset=0, **kwargs)
        except Exception:
            listings = []

        pace_metrics = quota.pace_from_db(conn, cap)

        tiles = f"""
<div class="tiles">
  <div class="tile"><div class="label">Active listings</div><div class="value">{e(stats['listings_active'])}</div></div>
  <div class="tile"><div class="label">New today</div><div class="value">{e(new_today)}</div></div>
  <div class="tile"><div class="label">Price drops today</div><div class="value">{e(drops_today)}</div></div>
  {render.pace_tile(pace_metrics)}
  <div class="tile"><div class="label">Best score</div><div class="value">{e(stats['best_score'] if stats['best_score'] is not None else '-')}</div></div>
  <div class="tile"><div class="label">Model-years with NHTSA data</div><div class="value">{e(nhtsa_model_years)}</div></div>
</div>"""

        def sel(value: str) -> str:
            return " selected" if resolved_sort == value else ""

        q = e(parse_str(params, "q") or "")
        make = e(parse_str(params, "make") or "")
        max_price = e(parse_str(params, "max_price") or "")
        max_mileage = e(parse_str(params, "max_mileage") or "")
        min_score = e(parse_str(params, "min_score") or "")
        cpo_checked = " checked" if parse_bool(params, "cpo") else ""

        form = f"""
<form class="filters" method="get" action="/">
  <div class="field"><label for="q">Search</label><input type="text" id="q" name="q" value="{q}" placeholder="make, model, dealer, VIN"></div>
  <div class="field"><label for="make">Make</label><input type="text" id="make" name="make" value="{make}"></div>
  <div class="field"><label for="max_price">Max price</label><input type="number" id="max_price" name="max_price" value="{max_price}"></div>
  <div class="field"><label for="max_mileage">Max mileage</label><input type="number" id="max_mileage" name="max_mileage" value="{max_mileage}"></div>
  <div class="field"><label for="min_score">Min score</label><input type="number" step="0.1" id="min_score" name="min_score" value="{min_score}"></div>
  <div class="field"><label for="sort">Sort</label>
    <select id="sort" name="sort">
      {"".join(f'<option value="{key}"{sel(key)}>{e(label)}</option>' for key, label in render.SORT_LABELS.items())}
    </select>
  </div>
  <div class="field checkbox"><label class="checkbox"><input type="checkbox" name="cpo" value="1"{cpo_checked}> CPO only</label></div>
  <button type="submit">Filter</button>
</form>"""

        sort_caption = f'<p class="sort-caption">{e(render.sort_caption(sort))}</p>'
        body = tiles + form + f'<div class="section">{sort_caption}{render.results_table(conn, listings, self.config)}</div>'
        self._send_html(render.page("Dashboard", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    # -- listing detail -------------------------------------------------------
    def _page_listing_detail(self, conn: Any, params: Dict[str, List[str]], vin: str) -> None:
        listing = db.get_listing(conn, vin)
        if listing is None:
            self._send_html(
                render.page("Listing not found", f'<div class="empty">No listing found for VIN {e(vin)}.</div>'),
                status=404,
            )
            return
        history = db.get_price_history(conn, vin)
        cross_shop = sources_for_listing(listing, self.config.search)

        make, model, year = listing.get("make"), listing.get("model"), listing.get("year")

        city_mpg, highway_mpg, combined_mpg = (
            listing.get("city_mpg"), listing.get("highway_mpg"), listing.get("combined_mpg"),
        )
        if combined_mpg is None and make and model and year:
            cached_mpg = db.get_mpg(conn, make, model, year)
            if cached_mpg:
                city_mpg = city_mpg if city_mpg is not None else cached_mpg.get("city_mpg")
                highway_mpg = highway_mpg if highway_mpg is not None else cached_mpg.get("highway_mpg")
                combined_mpg = cached_mpg.get("combined_mpg")

        title = " ".join(
            str(part) for part in (listing.get("year"), listing.get("make"), listing.get("model"), listing.get("trim"))
            if part
        ) or vin

        kv_rows = _listing_detail_kv(listing, city_mpg, highway_mpg, combined_mpg)
        breakdown_html = _score_breakdown_section(listing.get("score_breakdown") or [])
        history_html = _price_history_section(history)
        cross_html = _cross_shop_section(cross_shop)
        source_link = (
            f'<p><a href="{e(listing.get("listing_url"))}" target="_blank" rel="noopener">View original listing</a></p>'
            if listing.get("listing_url") else ""
        )
        badge = f'<span class="badge {score_class(listing.get("score"))}">{e(listing.get("score"))}</span>{render.demo_tag(listing)}'

        appraisal_obj = market.appraise_vin(conn, vin, self.config)
        market_html = render.appraisal_block(appraisal_obj.as_dict() if appraisal_obj else None)

        nhtsa_vin_url, nhtsa_model_url = nhtsa_urls(vin, make, model, year, vin_recall_url, recall_lookup_url)
        reliability = db.get_reliability(conn, make, model, year) if make and model and year else None
        reliability_html = _reliability_section(reliability, nhtsa_vin_url, nhtsa_model_url, make, model, year)

        body = f"""
<h1>{e(title)} {badge}</h1>
{source_link}
<div class="section">
  <h2>Listing details</h2>
  <table class="kv">{kv_rows}</table>
</div>
<div class="section">
  <h2>Score breakdown</h2>
  {breakdown_html}
</div>
<div class="section">
  <h2>Versus the market</h2>
  {market_html}
</div>
<div class="section">
  <h2>Reliability (NHTSA)</h2>
  {reliability_html}
</div>
<div class="section">
  <h2>Price history</h2>
  {history_html}
</div>
<div class="section">
  <h2>Cross-shop this vehicle</h2>
  {cross_html}
</div>
"""
        self._send_html(render.page(title, body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    # -- static/simple pages --------------------------------------------------
    def _page_sources(self, conn: Any, params: Dict[str, List[str]]) -> None:
        grouped = grouped_sources(self.config.search)
        blocks = []
        for key, group in grouped.items():
            items = "".join(
                f'<li><a href="{e(src["url"])}" target="_blank" rel="noopener">{e(src["name"])}</a>'
                f' &mdash; {e(src["note"])}</li>'
                for src in group.get("sources", [])
            )
            heading = e(key.replace("_", " ").title())
            blocks.append(f"""<div class="cat">
  <h3>{heading}</h3>
  <p class="desc">{e(group.get('description') or '')}</p>
  <ul>{items or '<li>No sources configured.</li>'}</ul>
</div>""")
        body = f"""
<div class="note">These are manual cross-shopping links only. This app does not scrape any of these
sites; each link just pre-fills the same search criteria on that site's own search page so you can
check it by hand.</div>
{''.join(blocks)}
"""
        self._send_html(render.page("Sources", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    def _page_digest(self, conn: Any, params: Dict[str, List[str]]) -> None:
        path, markdown = self._latest_digest()
        if markdown is None:
            body = '<div class="empty">No digest has been generated yet.</div>'
        else:
            body = f'<p>{e(str(path))}</p><pre class="digest">{e(markdown)}</pre>'
        self._send_html(render.page("Digest", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    def _page_market(self, conn: Any, params: Dict[str, List[str]]) -> None:
        months = parse_int(params, "months") or 6
        months = max(1, min(months, 36))
        report = market.market_report(conn, months=months, config=self.config)
        trend, models, deals = report["trend"], report["models"], report["best_deals"]
        dom, cuts = report["days_on_market"], report["price_cuts"]

        latest_median = trend[-1]["median_price"] if trend else None
        cut_share = cuts.get("cut_share_pct")
        median_days = dom.get("median_days")
        tiles = f"""
<div class="tiles">
  <div class="tile"><div class="label">Listings tracked</div><div class="value">{e(report['listings_tracked'])}</div></div>
  <div class="tile"><div class="label">Median price (latest month)</div><div class="value">{fmt_money(latest_median) if latest_median is not None else '—'}</div></div>
  <div class="tile"><div class="label">Median days on market</div><div class="value">{f"{median_days:.0f}" if median_days is not None else '—'}</div></div>
  <div class="tile"><div class="label">Listings that cut price</div><div class="value">{f"{cut_share:.0f}%" if cut_share is not None else '—'}</div></div>
</div>"""

        trend_html = _table_or_empty(
            ["Month", "Observations", "Cars", "Median", "Mean", "Min", "Max", "Median mileage", "Change"],
            [render.trend_row(t) for t in trend],
            "No monthly price history yet -- this fills in as the daily job runs.",
        )
        chart_html = render.trend_chart_svg(trend)
        models_html = _table_or_empty(
            ["Make / Model", "Sample", "Median price", "Range", "Median mileage", "$ / 1k miles", "r&sup2;", "Median days", "Price cuts"],
            [render.model_row(m) for m in models],
            "No model has enough comparable listings stored yet.",
        )
        deals_html = _table_or_empty(
            ["Car", "Price", "Expected", "Delta", "Grade", "Sample / confidence"],
            [render.deal_row(d) for d in deals],
            "No active listing has enough comparable data to grade yet.",
        )

        body = f"""
<h1>Market</h1>
{tiles}
<p class="note">{e(render.CONDITION_BLIND_NOTE)}</p>
<div class="section">
  <h2>Monthly trend</h2>
  <p class="note">{e(report['data_note'])}</p>
  {chart_html}
  {trend_html}
</div>
<div class="section">
  <h2>By model</h2>
  {models_html}
</div>
<div class="section">
  <h2>Best deals right now</h2>
  {deals_html}
</div>
"""
        self._send_html(render.page("Market", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    def _page_appraise(self, conn: Any, params: Dict[str, List[str]]) -> None:
        make = parse_str(params, "make") or ""
        model = parse_str(params, "model") or ""
        year = parse_int(params, "year")
        mileage = parse_int(params, "mileage")
        price = parse_int(params, "price")

        form = f"""
<form class="filters" method="get" action="/appraise">
  <div class="field"><label for="make">Make</label><input type="text" id="make" name="make" value="{e(make)}"></div>
  <div class="field"><label for="model">Model</label><input type="text" id="model" name="model" value="{e(model)}"></div>
  <div class="field"><label for="year">Year</label><input type="number" id="year" name="year" value="{e(year) if year is not None else ''}"></div>
  <div class="field"><label for="mileage">Mileage</label><input type="number" id="mileage" name="mileage" value="{e(mileage) if mileage is not None else ''}"></div>
  <div class="field"><label for="price">Asking price (optional)</label><input type="number" id="price" name="price" value="{e(price) if price is not None else ''}"></div>
  <button type="submit">Appraise</button>
</form>"""

        if make and model:
            car = {"make": make, "model": model, "year": year, "mileage": mileage, "price_current": price}
            appraisal_obj = market.appraise(conn, car, self.config)
            appraisal = appraisal_obj.as_dict()
            result_html = f'<p>{e(appraisal["summary"])}</p>{render.appraisal_block(appraisal)}'
        else:
            result_html = '<div class="empty">Fill in at least a make and model to get an estimate.</div>'

        body = f"""
<h1>Appraise a car</h1>
<p class="sort-caption">Estimate a fair price from comparable listings already tracked here -- a
cross-sectional read on price versus mileage and year, not a valuation.</p>
{form}
<div class="section">{result_html}</div>
"""
        self._send_html(render.page("Appraise", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn)))

    # -- scrapers page ----------------------------------------------------
    def _page_scrapers(self, conn: Any, params: Dict[str, List[str]]) -> None:
        self._send_html(self._render_scrapers_page(conn, params))

    def _page_scrapers_post(self, conn: Any, params: Dict[str, List[str]]) -> None:
        body = self._read_body_dict()
        try:
            self._require_write_auth(body)
        except ApiError as exc:
            self._send_html(self._render_scrapers_page(conn, params, error=exc.message), status=exc.status)
            return
        source = (body.get("source") or "").strip() or None
        try:
            self._apply_scraper_toggle(body)
        except ApiError as exc:
            self._send_html(self._render_scrapers_page(conn, params, error=exc.message), status=exc.status)
            return
        enabled = truthy(body.get("enabled"))
        message = f"{'Enabled' if enabled else 'Disabled'} {source or 'scrapers (master switch)'}."
        self._send_html(self._render_scrapers_page(conn, params, message=message))

    def _render_scrapers_page(
        self, conn: Any, params: Dict[str, List[str]],
        message: Optional[str] = None, error: Optional[str] = None,
    ) -> str:
        overview = self._scrapers_overview(conn)
        allowed, reason, disabled_attr = self._write_availability()
        banner = _status_banner(message, error)
        writable_note = (
            '<p class="note">Writable from this address -- toggling a source or running/probing it here '
            "takes effect immediately.</p>"
            if allowed else
            f'<p class="note">⚠️ Read-only from this address: {e(reason)}</p>'
        )

        usage = overview["usage_today"]
        limits = overview["limits"]
        req_cap = limits.get("max_requests_per_day")
        listing_cap = limits.get("max_listings_per_day")
        tiles = f"""
<div class="tiles">
  <div class="tile"><div class="label">Scrapers master switch</div><div class="value">{"On" if overview["enabled"] else "Off"}</div></div>
  <div class="tile"><div class="label">Requests today</div><div class="value">{e(usage["requests"])}/{e(req_cap)}</div></div>
  <div class="tile"><div class="label">Listings today</div><div class="value">{e(usage["listings"])}/{e(listing_cap)}</div></div>
</div>"""

        master_form = f"""<form method="post" action="/scrapers" style="display:inline">
  <input type="hidden" name="confirm" value="1">
  <input type="hidden" name="enabled" value="{"0" if overview["enabled"] else "1"}">
  <button type="submit"{disabled_attr}>{"Turn scrapers off" if overview["enabled"] else "Turn scrapers on"}</button>
</form>
<button type="button" onclick="carmonScraperAction('probe', null, false)"{disabled_attr}>Probe all</button>"""

        adapters_html = _adapters_table(overview["adapters"], disabled_attr)

        events = db.recent_scrape_events(conn, limit=25)
        events_html = _table_or_empty(
            ["Time", "Source", "URL", "HTTP status", "Note"],
            [_scrape_event_row(ev) for ev in events],
            "No scrape requests logged yet.",
        )

        body = f"""
<h1>Scrapers</h1>
<p class="note">A status of <strong>blocked</strong> or <strong>disallowed</strong> is a normal, expected
answer -- it means the site's robots.txt or bot defenses declined automated access, not a bug to fix. This
project always obeys robots.txt and never tries to work around blocking.</p>
{writable_note}
{banner}
{tiles}
<div class="section">{master_form}</div>
<div class="section">
  <h2>Adapters</h2>
  {adapters_html}
</div>
<div class="section">
  <h2>Recent scrape events</h2>
  {events_html}
</div>
{_SCRAPER_ACTION_SCRIPT}
"""
        return render.page("Scrapers", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn))

    # -- settings page ------------------------------------------------------
    def _page_settings(self, conn: Any, params: Dict[str, List[str]]) -> None:
        self._send_html(self._render_settings_page(conn, params))

    def _page_settings_post(self, conn: Any, params: Dict[str, List[str]]) -> None:
        body = self._read_body_dict()
        try:
            self._require_write_auth(body)
        except ApiError as exc:
            self._send_html(self._render_settings_page(conn, params, error=exc.message), status=exc.status)
            return

        setting_changes, dry_run = settings_changes_from_body(self.config, body, editable_settings)
        secret_changes = secret_changes_from_body(body)
        messages: List[str] = []
        warnings: List[str] = []
        try:
            if setting_changes:
                result = apply_changes(self.config, setting_changes, dry_run=dry_run)
                warnings.extend(result.get("warnings") or [])
                if result.get("applied"):
                    messages.append(f"Saved {len(result['applied'])} setting(s).")
            if secret_changes:
                update_secrets(secret_changes)
                messages.append(f"Saved {len(secret_changes)} secret(s).")
        except SettingsError as exc:
            self._send_html(self._render_settings_page(conn, params, error=str(exc)), status=400)
            return

        message = " ".join(messages) if messages else "Nothing changed."
        self._send_html(self._render_settings_page(conn, params, message=message, warnings=warnings))

    def _settings_field_row(self, dotted: str, info: Dict[str, Any], disabled_attr: str) -> str:
        value = info["value"]
        type_name = info["type"]
        editable = True
        if type_name == "bool":
            checked = " checked" if value else ""
            field = f'<input type="checkbox" name="{e(dotted)}" value="1"{checked}{disabled_attr}>'
        elif type_name == "number":
            field = f'<input type="number" step="any" name="{e(dotted)}" value="{e(value)}"{disabled_attr}>'
        elif type_name == "list":
            if isinstance(value, list) and all(isinstance(v, (str, int, float, bool)) for v in value):
                joined = ", ".join(str(v) for v in value)
                field = f'<input type="text" name="{e(dotted)}" value="{e(joined)}"{disabled_attr}>'
            else:
                editable = False
                field = '<span class="mv-sample">Complex list (not editable here) -- edit config.json directly.</span>'
        else:
            field = f'<input type="text" name="{e(dotted)}" value="{e(value)}"{disabled_attr}>'
        marker = f'<input type="hidden" name="present.{e(dotted)}" value="1">' if editable else ""
        return f"<tr><td>{e(dotted)}{marker}</td><td>{field}</td></tr>"

    def _render_settings_page(
        self, conn: Any, params: Dict[str, List[str]],
        message: Optional[str] = None, warnings: Optional[List[str]] = None, error: Optional[str] = None,
    ) -> str:
        allowed, reason, disabled_attr = self._write_availability()

        fields = editable_settings(self.config)
        sections: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
        for dotted, info in fields.items():
            sections.setdefault(dotted.split(".")[0], []).append((dotted, info))

        writable_note = (
            '<p class="note">Settings are writable from this address.</p>' if allowed else
            f'<p class="note">⚠️ Settings are read-only from this address: {e(reason)}</p>'
        )
        banner = _status_banner(message, error, warnings)

        section_blocks = []
        for section in sorted(sections):
            rows = "".join(self._settings_field_row(dotted, info, disabled_attr) for dotted, info in sorted(sections[section]))
            section_blocks.append(f"""<div class="cat">
  <h3>{e(section)}</h3>
  <table class="kv">{rows}</table>
</div>""")

        secrets_rows = [_secret_row(s, disabled_attr) for s in secrets_status()]

        body = f"""
<h1>Settings</h1>
{writable_note}
{banner}
<form method="post" action="/settings">
  <input type="hidden" name="confirm" value="1">
  {''.join(section_blocks)}
  <button type="submit"{disabled_attr}>Save settings</button>
</form>
<div class="section">
  <h2>Secrets</h2>
  <p class="note">Fill these in here -- there is nothing to copy by hand. Saving writes them straight into
  <code>.env</code> (created automatically, permissions locked to your account only) and secret values are
  write-only from then on: the current value is never shown or returned by this API, only whether it is
  set and its last few characters.</p>
  <form method="post" action="/settings">
    <input type="hidden" name="confirm" value="1">
    <table class="kv">{''.join(secrets_rows)}</table>
    <button type="submit"{disabled_attr}>Save secrets</button>
  </form>
</div>
"""
        return render.page("Settings", body, self._last_run_str(conn), demo_warning=demo.demo_banner(conn))

    # -- small shared bit of page state --------------------------------------
    def _write_availability(self) -> Tuple[bool, str, str]:
        """(allowed, reason, disabled_attr) for the address this request arrived on --
        used by both the scrapers and settings pages to grey out their forms identically."""
        token = get_secret("CARMON_API_TOKEN", env=self._env())
        allowed, reason = writes_allowed(self.server.server_address[0] or None, token)
        return allowed, reason, ("" if allowed else " disabled")


# --------------------------------------------------------------------------
# module-level render helpers used by exactly one page above -- kept as plain
# functions (no `self`) so the page method they support stays flat instead of
# nesting three levels of "if this data exists, build a table" inline.
# --------------------------------------------------------------------------
def _table_or_empty(headers: List[str], rows: List[str], empty_message: str) -> str:
    """The `<table>` skeleton every page here wants for a possibly-empty list of rows:
    a real table when there is data, an `.empty` placeholder otherwise."""
    if not rows:
        return f'<div class="empty">{e(empty_message)}</div>'
    head = "".join(f"<th>{h}</th>" for h in headers)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def _status_banner(message: Optional[str], error: Optional[str], warnings: Optional[List[str]] = None) -> str:
    """The success/error banner shown at the top of the scrapers and settings pages after
    a POST -- identical shape on both, so it is computed once here."""
    if error:
        return f'<p class="note">⚠️ {e(error)}</p>'
    if message:
        warn_html = "".join(f'<p class="note">⚠️ {e(w)}</p>' for w in (warnings or []))
        return f'<p class="note">✅ {e(message)}</p>{warn_html}'
    return ""


def _listing_detail_kv(listing: Dict[str, Any], city_mpg: Any, highway_mpg: Any, combined_mpg: Any) -> str:
    fields = [
        ("VIN", listing.get("vin")),
        ("Year / Make / Model / Trim", " / ".join(str(x) for x in (
            listing.get("year"), listing.get("make"), listing.get("model"), listing.get("trim")) if x)),
        ("Body / Fuel", f"{listing.get('body_type') or '-'} / {listing.get('fuel_type') or '-'}"),
        ("MPG (city / hwy / combined)", f"{fmt_mpg(city_mpg)} / {fmt_mpg(highway_mpg)} / {fmt_mpg(combined_mpg)}"),
        ("Price", fmt_money(listing.get("price_current"))),
        ("Price when first seen", fmt_money(listing.get("price_first_seen"))),
        ("Mileage", fmt_num(listing.get("mileage"))),
        ("Distance", f"{listing.get('distance_miles')} mi" if listing.get("distance_miles") is not None else "-"),
        ("CPO", "Yes" if listing.get("cpo") else "No"),
        ("Dealer", f"{listing.get('dealer_name') or '-'} - {listing.get('dealer_city') or '-'}, {listing.get('dealer_state') or '-'}"),
        ("Active", "Yes" if listing.get("active") else "No (likely sold/removed)"),
        ("First seen", listing.get("first_seen")),
        ("Last seen", listing.get("last_seen")),
        ("Score", listing.get("score")),
    ]
    return "".join(f"<tr><td>{e(k)}</td><td>{e(v)}</td></tr>" for k, v in fields)


def _score_breakdown_section(breakdown: List[Dict[str, Any]]) -> str:
    if not breakdown:
        return '<div class="empty">No score breakdown recorded.</div>'
    rows = "".join(
        f"<tr><td>{e(item.get('label'))}</td><td>{e(item.get('value'))}</td><td>{e(item.get('detail'))}</td></tr>"
        for item in breakdown
    )
    return f"""<div class="table-wrap"><table>
<thead><tr><th>Component</th><th>Value</th><th>Detail</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""


def _price_history_section(history: List[Dict[str, Any]]) -> str:
    if not history:
        return '<div class="empty">No price history recorded yet.</div>'
    rows = []
    prev_price = None
    for point in history:
        price = point.get("price")
        delta = "-"
        if prev_price is not None and price is not None:
            diff = price - prev_price
            delta = f"{'+' if diff > 0 else ''}{diff:,}"
        rows.append(
            f"<tr><td>{e(point.get('date'))}</td><td>{fmt_money(price)}</td>"
            f"<td>{delta}</td><td>{fmt_num(point.get('mileage'))}</td></tr>"
        )
        prev_price = price if price is not None else prev_price
    return f"""<div class="table-wrap"><table>
<thead><tr><th>Date</th><th>Price</th><th>&Delta;</th><th>Mileage</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""


def _cross_shop_section(cross_shop: List[Dict[str, Any]]) -> str:
    if not cross_shop:
        return '<div class="empty">No cross-shop links for this vehicle.</div>'
    return "<ul>" + "".join(
        f'<li><a href="{e(link["url"])}" target="_blank" rel="noopener">{e(link["name"])}</a></li>'
        for link in cross_shop
    ) + "</ul>"


def _reliability_section(
    reliability: Optional[Dict[str, Any]],
    nhtsa_vin_url: str,
    nhtsa_model_url: Optional[str],
    make: Any, model: Any, year: Any,
) -> str:
    if not reliability:
        return (
            '<div class="empty">No cached NHTSA data for this model year yet. '
            'Run <code>python3 -m carmon enrich</code> to fetch it.</div>'
            f'<p><a href="{e(nhtsa_vin_url)}" target="_blank" rel="noopener">Look up this VIN on NHTSA</a></p>'
        )

    comp_html = _table_or_empty(
        ["Component", "Complaints"],
        [f"<tr><td>{e(name)}</td><td>{e(count)}</td></tr>" for name, count in reliability.get("top_components") or []],
        "No component breakdown recorded.",
    )
    recall_html = _table_or_empty(
        ["Campaign", "Component", "Consequence", "Remedy"],
        [
            f"<tr><td>{e(r.get('campaign'))}</td><td>{e(r.get('component'))}</td>"
            f"<td>{e(r.get('consequence'))}</td><td>{e(r.get('remedy'))}</td></tr>"
            for r in reliability.get("recalls") or []
        ],
        "No recall campaigns recorded.",
    )
    reliability_kv = [
        ("Complaints filed", fmt_num(reliability.get("complaint_count"))),
        ("Recall campaigns", fmt_num(reliability.get("recall_count"))),
        ("Crash-related complaints", fmt_num(reliability.get("crash_complaints"))),
        ("Fire-related complaints", fmt_num(reliability.get("fire_complaints"))),
        ("Injuries reported", fmt_num(reliability.get("injuries"))),
        ("Deaths reported", fmt_num(reliability.get("deaths"))),
        ("NHTSA data fetched", reliability.get("fetched_at") or "-"),
    ]
    reliability_kv_html = "".join(f"<tr><td>{e(k)}</td><td>{e(v)}</td></tr>" for k, v in reliability_kv)

    return f"""
<p class="note">{e(render.NHTSA_VOLUME_CAVEAT)}</p>
<table class="kv">{reliability_kv_html}</table>
<h3>Top complaint components</h3>
{comp_html}
<h3>Recalls</h3>
{recall_html}
<p><a href="{e(nhtsa_vin_url)}" target="_blank" rel="noopener">Look up this VIN on NHTSA</a>
 &middot; <a href="{e(nhtsa_model_url or nhtsa_vin_url)}" target="_blank" rel="noopener">NHTSA recalls for {e(year)} {e(make)} {e(model)}</a></p>
"""


def _adapters_table(adapters: List[Dict[str, Any]], disabled_attr: str) -> str:
    return _table_or_empty(
        ["Adapter", "Kind", "Enabled", "Last run", "Status", "Message",
         "Last run pages/listings", "Run tally", "Actions"],
        [_adapter_row(a, disabled_attr) for a in adapters],
        "No scraper adapters registered.",
    )


def _adapter_row(a: Dict[str, Any], disabled_attr: str) -> str:
    cls = render.SCRAPER_STATUS_CLASSES.get(a["status"], "neutral")
    toggle = f"""<form method="post" action="/scrapers" style="display:inline">
  <input type="hidden" name="confirm" value="1">
  <input type="hidden" name="source" value="{e(a["key"])}">
  <input type="hidden" name="enabled" value="{"0" if a["enabled"] else "1"}">
  <button type="submit"{disabled_attr}>{"Disable" if a["enabled"] else "Enable"}</button>
</form>"""
    actions = f"""<button type="button" onclick="carmonScraperAction('probe', '{e(a["key"])}', false)"{disabled_attr}>Probe</button>
<button type="button" onclick="carmonScraperAction('run', '{e(a["key"])}', false)"{disabled_attr}>Run</button>
<button type="button" onclick="carmonScraperAction('run', '{e(a["key"])}', true)"{disabled_attr}>Dry run</button>"""
    missing_badge = '' if a["registered"] else ' <span class="badge bad" title="No adapter module registered for this key">missing</span>'
    return f"""<tr>
  <td>{e(a["name"])}{missing_badge}</td>
  <td>{e(a["kind"])}</td>
  <td>{"Yes" if a["enabled"] else "No"} {toggle}</td>
  <td>{e(a["last_run_at"] or "-")}</td>
  <td><span class="badge {cls}">{e(a["status"])}</span></td>
  <td>{e(a["message"] or a["last_error"] or "-")}</td>
  <td>{e(a["pages"])} pages &middot; {e(a["listings"])} listings</td>
  <td>{e(a["ok_runs"])} ok / {e(a["failed_runs"])} failed</td>
  <td>{actions}</td>
</tr>"""


def _scrape_event_row(ev: Dict[str, Any]) -> str:
    return (
        f"<tr><td>{e(ev.get('ts'))}</td><td>{e(ev.get('source'))}</td><td>{e(ev.get('url') or '-')}</td>"
        f"<td>{e(ev.get('status') if ev.get('status') is not None else '-')}</td><td>{e(ev.get('note') or '-')}</td></tr>"
    )


def _secret_row(s: Dict[str, Any], disabled_attr: str) -> str:
    """One row of the secrets form: masked current state, the input, and -- new -- what
    the secret is for, how to get one, and a link to go get it (when there is a URL)."""
    state_bits = "set" if s["set"] else "not set"
    if s["set"]:
        state_bits += f" ({e(s['masked'])})"
    if s["from_environment"]:
        state_bits += " -- from environment, overrides .env"
    link_html = (
        f' <a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">Get one here &rarr;</a>'
        if s.get("url") else ""
    )
    return f"""<tr>
  <td>{e(s["label"])}<div class="mv-sample">{e(s["key"])} &middot; currently {state_bits}</div>
  <p class="secret-help"><strong>{e(s.get("purpose"))}</strong></p></td>
  <td>
    <input type="password" name="secret.{e(s["key"])}" placeholder="leave blank to keep current value" autocomplete="off"{disabled_attr}>
    <p class="secret-help">{e(s.get("how"))}{link_html}</p>
  </td>
</tr>"""


_SCRAPER_ACTION_SCRIPT = """
<script>
function carmonScraperAction(action, source, dryRun) {
  var url = action === 'probe' ? '/api/scrapers/probe' : '/api/scrapers/run';
  var body = {confirm: 1};
  if (source) { body.source = source; }
  if (action === 'run') { body.dry_run = !!dryRun; }
  fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-Carmon-Write': '1'},
    body: JSON.stringify(body)
  }).then(function (r) { return r.json().then(function (data) { return {ok: r.ok, data: data}; }); })
    .then(function (result) {
      alert((result.ok ? 'Done: ' : 'Failed: ') + JSON.stringify(result.data));
      window.location.reload();
    })
    .catch(function (err) { alert('Request failed: ' + err); });
}
</script>"""
