"""Command line entry point: `python -m carmon <command>`."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import (__version__, db, demo as demo_module, digest as digest_module, fueleconomy,
               market, nhtsa, notify, quota)
from .config import Config, ConfigError, PROJECT_ROOT, load_config, get_secret, validate_config
from .pipeline import probe_scrapers, refresh_market_values, rescore_all, run_daily, run_scrapers
from .scoring import score_listing
from .sources import build_sources, grouped_sources


def _force_utf8_output() -> None:
    """Make stdout/stderr UTF-8 safe on every platform.

    The digest, the pace gauge and the status icons use non-ASCII characters. On Windows
    the console handles them, but a *redirected* stream (which is exactly what the
    scheduled-task command does: `>> data\\run.log`) falls back to the ANSI code page and
    raises UnicodeEncodeError. Reconfiguring here keeps scheduled runs from dying on an
    emoji. `errors="replace"` means a genuinely undisplayable character degrades to "?"
    rather than taking the run down.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass  # already-wrapped or non-reconfigurable stream (e.g. a StringIO in tests)


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _open_db(config: Config):
    """Open the database and expire stale demo data before anything reads it."""
    conn = db.init_db(config.db_path)
    removed = demo_module.maybe_expire(conn, config)
    if removed:
        print(f"Cleared {removed} stale demo listing(s) automatically.", file=sys.stderr)
    banner = demo_module.demo_banner(conn)
    if banner:
        print(f"⚠️  {banner}", file=sys.stderr)
    return conn


def _config(args: argparse.Namespace) -> Config:
    config = load_config(args.config)
    if getattr(args, "db", None):
        config.data.setdefault("paths", {})["db"] = str(Path(args.db).resolve())
    return config


# --- commands -----------------------------------------------------------
def cmd_run(args: argparse.Namespace) -> int:
    config = _config(args)
    for warning in validate_config(config):
        print(f"config warning: {warning}", file=sys.stderr)
    conn = _open_db(config)
    run_date = args.date or date.today().isoformat()
    print(f"Running daily job for {run_date} (db: {config.db_path})")

    result = run_daily(config, conn=conn, run_date=run_date, dry_run=args.dry_run)
    summary = result.as_dict()
    print(json.dumps(summary, indent=2))

    markdown = digest_module.render_digest(config, conn, run_date=run_date, run_result=summary, days=args.days)
    if args.dry_run:
        print("\n--- digest (dry run, not saved) ---\n")
        print(markdown)
        conn.close()
        return 1 if result.errors else 0

    path = digest_module.save_digest(config, markdown, run_date=run_date)
    print(f"Digest written to {path}")
    conn.execute("UPDATE runs SET digest_path = ? WHERE id = (SELECT MAX(id) FROM runs)", (str(path),))
    conn.commit()

    if not args.no_discord:
        configured = get_secret("DISCORD_WEBHOOK_URL") or (
            get_secret("DISCORD_BOT_TOKEN") and get_secret("DISCORD_USER_ID")
        )
        if configured:
            try:
                transport = notify.send_digest(
                    config, conn, run_date=run_date, run_result=summary,
                    web_url=args.web_url, mode=args.discord_mode,
                )
                print(
                    "Digest sent as a Discord direct message."
                    if transport == "dm" else "Digest posted to the Discord webhook channel."
                )
            except notify.DiscordError as exc:
                print(f"Discord delivery failed: {exc}", file=sys.stderr)
                conn.close()
                return 1
        else:
            print(
                "No Discord delivery configured — set DISCORD_BOT_TOKEN + DISCORD_USER_ID (DM) "
                "or DISCORD_WEBHOOK_URL (channel) in .env."
            )
    conn.close()
    return 1 if result.errors else 0


def cmd_digest(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = _open_db(config)
    markdown = digest_module.render_digest(config, conn, run_date=args.date, days=args.days)
    if args.save:
        path = digest_module.save_digest(config, markdown, run_date=args.date)
        print(f"Digest written to {path}", file=sys.stderr)
    print(markdown)
    conn.close()
    return 0


def cmd_notify(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = _open_db(config)
    try:
        transport = notify.send_digest(
            config, conn, webhook_url=args.webhook, run_date=args.date,
            web_url=args.web_url, mode=args.discord_mode,
        )
    except notify.DiscordError as exc:
        print(f"Discord delivery failed: {exc}", file=sys.stderr)
        conn.close()
        return 1
    print(
        "Digest sent as a Discord direct message."
        if transport == "dm" else "Digest posted to the Discord webhook channel."
    )
    conn.close()
    return 0


def cmd_quota(args: argparse.Namespace) -> int:
    """Show MarketCheck usage against how much of the month has actually gone by."""
    config = _config(args)
    conn = _open_db(config)
    cap = int(config.api.get("monthly_call_cap", 500))
    metrics = quota.pace_from_db(conn, cap)
    sweep = quota.sweep_budget(metrics["used"], cap, config.api.get("month_end_sweep", {}))
    if args.json:
        print(json.dumps({**metrics, "summary": quota.summary_line(metrics),
                          "bar": quota.bar(metrics), "month_end_sweep": sweep}, indent=2))
        conn.close()
        return 0

    print(f"MarketCheck quota for {metrics['month']}")
    print(f"  {quota.bar(metrics, 32)}   (filled = used, | = today)")
    print(f"  used {metrics['used']} of {metrics['cap']} — {metrics['remaining']} left")
    print(f"  day {metrics['day_of_month']} of {metrics['days_in_month']} "
          f"({metrics['elapsed_fraction'] * 100:.0f}% of the month gone)")
    print(f"  expected ~{metrics['expected_by_now']:.0f} by now → "
          f"{metrics['pace_ratio']:.2f}x pace  {metrics['pace_icon']} {metrics['pace_label']}")
    print(f"  projected month total {metrics['projected_month_total']:.0f}"
          + (f" (overshoot {metrics['projected_overshoot']:.0f})" if metrics["projected_overshoot"] else ""))
    print(f"  ~{metrics['affordable_per_day']:.0f} calls/day still affordable for the rest of the month")
    print(f"  month-end sweep: {sweep['reason']}")
    conn.close()
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    config = _config(args)
    _open_db(config).close()
    from .webapp import serve  # imported lazily so the CLI works without the web module
    serve(config, host=args.host, port=args.port)
    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    config = _config(args)
    _open_db(config).close()
    from .mcp_server import main as mcp_main
    argv: List[str] = ["--config", str(config.path or "config.json"), "--db", str(config.db_path)]
    return int(mcp_main(argv) or 0)


def cmd_seed_demo(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = _open_db(config)
    if args.clear:
        removed = demo_module.clear_demo(conn)
        print(f"Removed {removed} demo listings.")
        conn.close()
        return 0
    vins = demo_module.seed(config, conn, count=args.count)
    print(f"Seeded {len(vins)} demo listings into {config.db_path}")
    print("Browse them with:  python -m carmon serve")
    conn.close()
    return 0


def cmd_enrich(args: argparse.Namespace) -> int:
    """Refresh the free NHTSA and EPA data for every model-year in the database."""
    config = _config(args)
    conn = _open_db(config)
    enrichment_config = config.data.get("enrichment", {})
    model_years = db.distinct_model_years(conn, active_only=not args.all)
    if args.limit:
        model_years = model_years[: args.limit]
    if not model_years:
        print("No listings stored yet — run `python3 -m carmon run` or `seed-demo` first.")
        conn.close()
        return 0

    print(f"Refreshing free data for {len(model_years)} model-year(s). No API key needed.")
    summary = {}
    if not args.mpg_only:
        summary["nhtsa"] = nhtsa.enrich_models(conn, model_years, enrichment_config, force_refresh=args.force)
    if not args.nhtsa_only:
        summary["mpg"] = fueleconomy.enrich_models(conn, model_years, enrichment_config, force_refresh=args.force)
    print(json.dumps(summary, indent=2))

    rescored = rescore_all(config, conn=conn)
    print(f"Rescored {rescored} listings with the refreshed data.")
    conn.close()
    return 0


def cmd_reliability(args: argparse.Namespace) -> int:
    """Show what NHTSA knows about one model-year."""
    config = _config(args)
    conn = _open_db(config)
    facts = db.get_reliability(conn, args.make, args.model, args.year)
    if facts is None and not args.no_fetch:
        client = nhtsa.NHTSAClient(conn, config.data.get("enrichment", {}))
        facts = client.facts_for(args.make, args.model, args.year)
    if facts is None:
        print(f"No NHTSA data for {args.year} {args.make} {args.model}.", file=sys.stderr)
        conn.close()
        return 1
    if args.json:
        print(json.dumps(facts, indent=2, default=str))
        conn.close()
        return 0

    print(f"{args.year} {args.make} {args.model} — NHTSA (free federal data)")
    print(f"  complaints: {facts.get('complaint_count')}   recalls: {facts.get('recall_count')}")
    print(
        f"  crash-related: {facts.get('crash_complaints')}   fire-related: {facts.get('fire_complaints')}"
        f"   injuries: {facts.get('injuries')}   deaths: {facts.get('deaths')}"
    )
    for component, count in (facts.get("top_components") or [])[:5]:
        print(f"    - {component}: {count}")
    for recall in (facts.get("recalls") or [])[:5]:
        flag = " [PARK IT]" if recall.get("park_it") else ""
        print(f"  recall {recall.get('campaign')}{flag}: {recall.get('component')}")
        if recall.get("consequence"):
            print(f"      consequence: {recall['consequence'][:160]}")
    repair = db.get_repair_cost(conn, args.make, args.model)
    if repair:
        print("  RepairPal (scraped, opt-in):")
        if repair.get("annual_repair_cost"):
            print(f"    average annual repair cost: ${repair['annual_repair_cost']:,.0f}")
        if repair.get("reliability_rating"):
            print(f"    reliability rating: {repair['reliability_rating']} / "
                  f"{repair.get('rating_scale') or 5}")
        if repair.get("rank_text"):
            print(f"    ranking: {repair['rank_text']}")
        if repair.get("fetched_at"):
            print(f"    fetched {repair['fetched_at']} from {repair.get('source_url', 'repairpal.com')}")
    print(f"  {nhtsa.recall_lookup_url(args.make, args.model, args.year)}")
    print(
        "  Note: complaint counts are raw and not adjusted for sales volume — a popular model\n"
        "  accumulates more of them. The recurring components above are the stronger signal."
    )
    conn.close()
    return 0


def cmd_config_check(args: argparse.Namespace) -> int:
    config = _config(args)
    warnings = validate_config(config)
    if not warnings:
        print(f"config.json looks consistent ({config.path}).")
        weights = config.scoring["weights"]
        print("Derived from search criteria (single source of truth):")
        print(f"  price ceiling      {weights.get('price_no_bonus_at')}  <- search.price_max")
        print(f"  mileage full pen.  {weights.get('mileage_full_penalty_at')}  <- search.mileage_max")
        print(f"  oldest year        {weights.get('year_no_bonus_at')}  <- search.year_min")
        return 0
    for warning in warnings:
        print(f"- {warning}")
    return 1


def _money(value) -> str:
    return f"${value:,.0f}" if value not in (None, "") else "n/a"


def cmd_market(args: argparse.Namespace) -> int:
    """Market trends: what things cost, how fast they move, and how much sellers cut."""
    config = _config(args)
    conn = _open_db(config)
    if args.refresh:
        summary = refresh_market_values(config, conn)
        print(f"Re-appraised {summary['listings_appraised']} listing(s); "
              f"{summary['below_market']} sit more than 5% below expected.")
    report = market.market_report(conn, months=args.months, config=config)
    if args.json:
        print(json.dumps(report, indent=2, default=str))
        conn.close()
        return 0

    print(f"Market report — {report['listings_tracked']} real listings tracked")
    print(f"\n{report['data_note']}\n")

    trend = report["trend"]
    if trend:
        print("Median asking price by month")
        widest = max(row["median_price"] for row in trend) or 1
        for row in trend:
            bar_width = max(1, round(28 * row["median_price"] / widest))
            change = ""
            if row.get("change_vs_previous") is not None:
                change = f"  {row['change_vs_previous']:+,} ({row['change_pct']:+.1f}%)"
            print(f"  {row['month']}  {'█' * bar_width:<28} {_money(row['median_price'])}"
                  f"  n={row['observations']:<4}{change}")
    else:
        print("No price history yet — this fills in once the daily job has run a few times.")

    dom = report["days_on_market"]
    cuts = report["price_cuts"]
    median_days = dom["median_days"]
    print(f"\nDays on market: median {median_days if median_days is not None else 'n/a'} "
          f"(from {dom['sample_size']} listings that have since vanished)")
    print(f"Price cuts: {cuts['cut_count']} of {cuts['tracked']} tracked listings "
          f"({cuts['cut_share_pct'] or 0}%), median cut {_money(cuts['median_cut'])}"
          + (f" ({cuts['median_cut_pct']}%)" if cuts.get("median_cut_pct") else ""))

    if report["models"]:
        print("\nBy model")
        header = f"  {'model':<28}{'n':>4}  {'median':>9}  {'range':>19}  {'$/1k mi':>8}  {'days':>5}  cuts"
        print(header)
        for row in report["models"]:
            name = f"{row['make']} {row['model']}"
            price_range = f"{_money(row['min_price'])}–{_money(row['max_price'])}"
            per_mile = f"{row['dollars_per_1k_miles']:.0f}" if row["dollars_per_1k_miles"] else "—"
            days = row["days_on_market"]["median_days"]
            days = f"{days:.0f}" if days is not None else "—"
            print(f"  {name[:28]:<28}{row['sample_size']:>4}  {_money(row['median_price']):>9}  "
                  f"{price_range:>19}  {per_mile:>8}  {days:>5}  "
                  f"{row['price_cuts']['cut_share_pct'] or 0}%")

    if report["best_deals"]:
        print("\nBest deals right now (price versus expected for that mileage and year)")
        for item in report["best_deals"][:args.limit]:
            appraisal = item["appraisal"]
            print(f"  {appraisal['grade_icon']} {item['year']} {item['make']} {item['model']} — "
                  f"{_money(item['price_current'])} vs {_money(appraisal['expected_price'])} expected "
                  f"({appraisal['delta']:+,}, {appraisal['delta_pct']:+.1f}%) · "
                  f"{item['mileage']:,} mi · n={appraisal['sample_size']} "
                  f"({appraisal['confidence']} confidence)")
    conn.close()
    return 0


def cmd_appraise(args: argparse.Namespace) -> int:
    """Compare one car — real or hypothetical — against the local market."""
    config = _config(args)
    conn = _open_db(config)
    if args.vin:
        result = market.appraise_vin(conn, args.vin, config)
        if result is None:
            print(f"No stored listing with VIN {args.vin}.", file=sys.stderr)
            conn.close()
            return 1
    else:
        result = market.appraise(conn, {
            "make": args.make, "model": args.model, "year": args.year,
            "mileage": args.mileage, "price_current": args.price,
        }, config)

    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
        conn.close()
        return 0

    print(result.summary())
    print(f"  basis: {result.basis} ({result.basis_level}), method: {result.method}"
          + (f", r² {result.r_squared}" if result.r_squared is not None else ""))
    if result.comparable_median:
        low, high = result.comparable_range or (None, None)
        print(f"  comparables: median {_money(result.comparable_median)}, "
              f"range {_money(low)}–{_money(high)}, n={result.sample_size}")
    if result.dollars_per_model_year:
        print(f"  each newer model year is worth about {_money(result.dollars_per_model_year)} here")
    for note in result.notes:
        print(f"  ⚠️  {note}")
    print("  This compares asking prices only — it knows nothing about condition, trim, options,")
    print("  accident history or title status. Always inspect the car itself.")
    conn.close()
    return 0


def cmd_deals(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = _open_db(config)
    deals = market.best_deals(conn, limit=args.limit, min_sample=args.min_sample, config=config)
    if args.json:
        print(json.dumps(deals, indent=2, default=str))
        conn.close()
        return 0
    if not deals:
        print("No listings have enough comparables to grade yet. Let the daily job run for a few days.")
        conn.close()
        return 0
    for item in deals:
        appraisal = item["appraisal"]
        print(f"{appraisal['grade_icon']} {appraisal['grade']}: {item['year']} {item['make']} "
              f"{item['model']} {item.get('trim') or ''}".rstrip())
        print(f"    {_money(item['price_current'])} vs {_money(appraisal['expected_price'])} expected "
              f"({appraisal['delta']:+,}, {appraisal['delta_pct']:+.1f}%) · {item['mileage']:,} mi · "
              f"score {item.get('score', 0):+.2f} · n={appraisal['sample_size']} "
              f"({appraisal['confidence']} confidence)")
        if item.get("listing_url"):
            print(f"    {item['listing_url']}")
    conn.close()
    return 0


def cmd_scrape(args: argparse.Namespace) -> int:
    """Run the optional scrapers — off by default, robots-obeying, hard-capped."""
    config = _config(args)
    conn = _open_db(config)
    scraper_config = config.data.get("scrapers", {}) or {}

    if args.status:
        usage = db.scrape_usage_today(conn)
        print(f"Scraper usage today ({usage['day']}):")
        print(f"  requests {usage['requests']} / {scraper_config.get('max_requests_per_day', 20)}")
        print(f"  listings {usage['listings']} / {scraper_config.get('max_listings_per_day', 100)}")
        for row in db.scrape_usage_by_source(conn):
            print(f"    {row['source']:<14} {row['requests']:>3} request(s), {row['listings']:>3} listing(s)")
        print(f"  enabled: {scraper_config.get('enabled', False)}; sources: "
              f"{ {k: v for k, v in (scraper_config.get('sources') or {}).items()} }")
        conn.close()
        return 0

    if args.probe:
        print("Probing each adapter (one request each). Blocked or disallowed is a normal, "
              "expected answer — it means that site does not want automated traffic.\n")
        for entry in probe_scrapers(config, conn):
            icon = {"ok": "✅", "empty": "⚠️ ", "blocked": "🚫", "disallowed": "⛔",
                    "unparsed": "⚠️ ", "budget": "⏳", "error": "❌"}.get(entry["status"], "?")
            print(f"  {icon} {entry.get('name', entry['source']):<12} {entry['status']}")
            if entry.get("message"):
                print(f"       {entry['message'][:180]}")
        conn.close()
        return 0

    sources = [args.source] if args.source else None
    summary = run_scrapers(config, conn, sources=sources, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2, default=str))
    if not summary.get("enabled"):
        conn.close()
        return 1
    conn.close()
    return 0


def cmd_rescore(args: argparse.Namespace) -> int:
    config = _config(args)
    count = rescore_all(config)
    print(f"Rescored {count} listings using scoring.mode='{config.scoring.get('mode', 'smooth')}'.")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = _open_db(config)
    print(json.dumps(db.stats(conn, int(config.api.get("monthly_call_cap", 500))), indent=2, default=str))
    conn.close()
    return 0


def cmd_sources(args: argparse.Namespace) -> int:
    config = _config(args)
    if args.json:
        print(json.dumps(grouped_sources(config.search), indent=2))
        return 0
    for source in build_sources(config.search):
        print(f"[{source.category}] {source.name}\n  {source.url}\n  {source.note}\n")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    config = _config(args)
    listing = {
        "make": args.make,
        "model": args.model,
        "mileage": args.mileage,
        "distance_miles": args.distance,
        "price_current": args.price,
        "price_first_seen": args.price_first_seen or args.price,
        "cpo": args.cpo,
    }
    result = score_listing(listing, config.scoring)
    print(result.explain() if not args.json else json.dumps(result.as_dict(), indent=2))
    return 0


def cmd_cron(args: argparse.Namespace) -> int:
    """Print the daily-schedule command for this machine (cron, launchd or Task Scheduler)."""
    python = sys.executable
    root = PROJECT_ROOT
    hour, minute = args.at.split(":") if ":" in args.at else (args.at, "0")
    hour, minute = int(hour), int(minute)
    target = (args.platform or ("windows" if os.name == "nt" else "unix")).lower()

    if target == "windows":
        print("# Windows Task Scheduler — run this once in an Administrator PowerShell/cmd:")
        print(
            f'schtasks /Create /SC DAILY /ST {hour:02d}:{minute:02d} /TN "UsedCarMonitor" '
            f'/TR "cmd /c cd /d {root} && \"{python}\" -m carmon run >> \"{root}/data/run.log\" 2>&1"'
        )
        print("\n# Check it, run it now, or remove it:")
        print('schtasks /Query /TN "UsedCarMonitor"')
        print('schtasks /Run /TN "UsedCarMonitor"')
        print('schtasks /Delete /TN "UsedCarMonitor" /F')
        print("\n# Task Scheduler skips runs while the machine is asleep; tick")
        print("# \"Run task as soon as possible after a scheduled start is missed\" in the GUI to catch up.")
        return 0

    line = f"{minute} {hour} * * * cd {root} && {python} -m carmon run >> {root}/data/cron.log 2>&1"
    print("# Add this to your crontab (`crontab -e`):")
    print(line)
    print("\n# Or install it now with:")
    print(f'(crontab -l 2>/dev/null; echo "{line}") | crontab -')
    print("\n# macOS: cron works, but launchd is more idiomatic — or use the systemd units in deploy/ on Linux.")
    print("# For the Windows form of this command: python3 -m carmon cron --platform windows")
    return 0


def cmd_selftest(args: argparse.Namespace) -> int:
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(str(PROJECT_ROOT / "tests"), top_level_dir=str(PROJECT_ROOT))
    runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
    return 0 if runner.run(suite).wasSuccessful() else 1


# --- parser -------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m carmon",
        description="Used Car Daily Monitor — MarketCheck search, scoring, digest, web/API/MCP.",
    )
    parser.add_argument("--version", action="version", version=f"used-car-monitor {__version__}")
    parser.add_argument("--config", help="path to config.json (default: project config.json)")
    parser.add_argument("--db", help="override the SQLite path from config.json")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="the daily job: fetch, store, score, digest, Discord")
    run.add_argument("--dry-run", action="store_true", help="fetch and score but write nothing")
    run.add_argument("--no-discord", action="store_true", help="skip the Discord post")
    run.add_argument("--date", help="run date (YYYY-MM-DD), defaults to today")
    run.add_argument("--days", type=int, default=1, help="digest lookback window in days")
    run.add_argument("--web-url", help="link to your website, included in the Discord message")
    run.add_argument("--discord-mode", dest="discord_mode", choices=("auto", "dm", "webhook"),
                     help="how to deliver: dm, webhook, or auto (default, from config.json)")
    run.set_defaults(func=cmd_run)

    digest = sub.add_parser("digest", help="render the digest from stored data (no API calls)")
    digest.add_argument("--date", help="digest date (YYYY-MM-DD)")
    digest.add_argument("--days", type=int, default=1, help="lookback window in days")
    digest.add_argument("--save", action="store_true", help="also write it to the digest directory")
    digest.set_defaults(func=cmd_digest)

    notify_cmd = sub.add_parser("notify", help="post the current digest to Discord")
    notify_cmd.add_argument("--webhook", help="webhook URL (defaults to DISCORD_WEBHOOK_URL)")
    notify_cmd.add_argument("--date", help="digest date (YYYY-MM-DD)")
    notify_cmd.add_argument("--web-url", help="link to your website, included in the message")
    notify_cmd.add_argument("--mode", dest="discord_mode", choices=("auto", "dm", "webhook"),
                            help="dm = direct message (needs DISCORD_BOT_TOKEN + DISCORD_USER_ID); "
                                 "webhook = server channel; auto = DM if configured, else webhook")
    notify_cmd.set_defaults(func=cmd_notify)

    quota_cmd = sub.add_parser("quota", help="MarketCheck usage vs how much of the month has passed")
    quota_cmd.add_argument("--json", action="store_true")
    quota_cmd.set_defaults(func=cmd_quota)

    serve = sub.add_parser("serve", help="run the website + JSON API")
    serve.add_argument("--host", help="bind host (default from config.web)")
    serve.add_argument("--port", type=int, help="bind port (default from config.web)")
    serve.set_defaults(func=cmd_serve)

    mcp = sub.add_parser("mcp", help="run the MCP server on stdio")
    mcp.set_defaults(func=cmd_mcp)

    seed = sub.add_parser("seed-demo", help="insert demo listings so the UI/API/MCP have data")
    seed.add_argument("--count", type=int, default=18)
    seed.add_argument("--clear", action="store_true", help="delete demo listings instead")
    seed.set_defaults(func=cmd_seed_demo)

    enrich = sub.add_parser("enrich", help="refresh free NHTSA + EPA MPG data, then rescore")
    enrich.add_argument("--force", action="store_true", help="ignore the cache and refetch")
    enrich.add_argument("--limit", type=int, help="only process the first N model-years")
    enrich.add_argument("--all", action="store_true", help="include inactive (sold) listings")
    enrich.add_argument("--nhtsa-only", action="store_true", dest="nhtsa_only")
    enrich.add_argument("--mpg-only", action="store_true", dest="mpg_only")
    enrich.set_defaults(func=cmd_enrich)

    reliability = sub.add_parser("reliability", help="NHTSA complaints and recalls for one model-year")
    reliability.add_argument("--make", required=True)
    reliability.add_argument("--model", required=True)
    reliability.add_argument("--year", type=int, required=True)
    reliability.add_argument("--json", action="store_true")
    reliability.add_argument("--no-fetch", action="store_true", dest="no_fetch",
                             help="only read the cache, never call NHTSA")
    reliability.set_defaults(func=cmd_reliability)

    config_check = sub.add_parser("config-check", help="validate config.json and report drift")
    config_check.set_defaults(func=cmd_config_check)

    market_cmd = sub.add_parser("market", help="price trends, days on market, and per-model stats")
    market_cmd.add_argument("--months", type=int, default=6)
    market_cmd.add_argument("--limit", type=int, default=5, help="how many best deals to list")
    market_cmd.add_argument("--refresh", action="store_true", help="re-appraise every listing first")
    market_cmd.add_argument("--json", action="store_true")
    market_cmd.set_defaults(func=cmd_market)

    appraise = sub.add_parser("appraise", help="is this price good? compare one car to the market")
    appraise.add_argument("--vin", help="appraise a stored listing instead of a hypothetical car")
    appraise.add_argument("--make")
    appraise.add_argument("--model")
    appraise.add_argument("--year", type=int)
    appraise.add_argument("--mileage", type=int)
    appraise.add_argument("--price", type=int, help="asking price to grade")
    appraise.add_argument("--json", action="store_true")
    appraise.set_defaults(func=cmd_appraise)

    deals = sub.add_parser("deals", help="active listings ranked by price versus expected")
    deals.add_argument("--limit", type=int, default=10)
    deals.add_argument("--min-sample", type=int, default=3, dest="min_sample")
    deals.add_argument("--json", action="store_true")
    deals.set_defaults(func=cmd_deals)

    scrape = sub.add_parser("scrape", help="run the optional scrapers (off by default, capped)")
    scrape.add_argument("--source", help="run just this adapter, ignoring its config toggle")
    scrape.add_argument("--probe", action="store_true", help="one request per adapter: is it reachable?")
    scrape.add_argument("--status", action="store_true", help="today's scraper usage against the caps")
    scrape.add_argument("--dry-run", action="store_true", help="fetch and parse but store nothing")
    scrape.set_defaults(func=cmd_scrape)

    rescore = sub.add_parser("rescore", help="recompute every stored score with the current config")
    rescore.set_defaults(func=cmd_rescore)

    stats = sub.add_parser("stats", help="DB and API-quota stats as JSON")
    stats.set_defaults(func=cmd_stats)

    sources = sub.add_parser("sources", help="print the cross-shopping deep links")
    sources.add_argument("--json", action="store_true")
    sources.set_defaults(func=cmd_sources)

    score = sub.add_parser("score", help="score a hypothetical car without touching the DB")
    score.add_argument("--make", required=True)
    score.add_argument("--model", required=True)
    score.add_argument("--mileage", type=int)
    score.add_argument("--distance", type=float)
    score.add_argument("--price", type=int)
    score.add_argument("--price-first-seen", type=int, dest="price_first_seen")
    score.add_argument("--cpo", action="store_true")
    score.add_argument("--json", action="store_true")
    score.set_defaults(func=cmd_score)

    cron = sub.add_parser("cron", help="print the daily schedule command for this OS")
    cron.add_argument("--at", default="7:30", help="local time HH:MM (default 7:30)")
    cron.add_argument("--platform", choices=("unix", "windows"),
                      help="force the output style (default: detected from this machine)")
    cron.set_defaults(func=cmd_cron)

    selftest = sub.add_parser("selftest", help="run the bundled test suite")
    selftest.set_defaults(func=cmd_selftest)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    _force_utf8_output()
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    try:
        return int(args.func(args) or 0)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
