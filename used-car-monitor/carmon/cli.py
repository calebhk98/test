"""Command line entry point: `python -m carmon <command>`."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__, db, demo as demo_module, digest as digest_module, notify
from .config import Config, ConfigError, PROJECT_ROOT, load_config, get_secret
from .pipeline import rescore_all, run_daily
from .scoring import score_listing
from .sources import build_sources, grouped_sources


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _config(args: argparse.Namespace) -> Config:
    config = load_config(args.config)
    if getattr(args, "db", None):
        config.data.setdefault("paths", {})["db"] = str(Path(args.db).resolve())
    return config


# --- commands -----------------------------------------------------------
def cmd_run(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = db.init_db(config.db_path)
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
        webhook = get_secret("DISCORD_WEBHOOK_URL")
        if webhook:
            try:
                notify.send_digest(
                    config, conn, webhook_url=webhook, run_date=run_date,
                    run_result=summary, web_url=args.web_url,
                )
                print("Digest posted to Discord.")
            except notify.DiscordError as exc:
                print(f"Discord delivery failed: {exc}", file=sys.stderr)
                conn.close()
                return 1
        else:
            print("DISCORD_WEBHOOK_URL not set — skipping Discord delivery.")
    conn.close()
    return 1 if result.errors else 0


def cmd_digest(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = db.init_db(config.db_path)
    markdown = digest_module.render_digest(config, conn, run_date=args.date, days=args.days)
    if args.save:
        path = digest_module.save_digest(config, markdown, run_date=args.date)
        print(f"Digest written to {path}", file=sys.stderr)
    print(markdown)
    conn.close()
    return 0


def cmd_notify(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = db.init_db(config.db_path)
    webhook = args.webhook or get_secret("DISCORD_WEBHOOK_URL", required=True)
    try:
        notify.send_digest(config, conn, webhook_url=webhook, run_date=args.date, web_url=args.web_url)
    except notify.DiscordError as exc:
        print(f"Discord delivery failed: {exc}", file=sys.stderr)
        conn.close()
        return 1
    print("Digest posted to Discord.")
    conn.close()
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    config = _config(args)
    db.init_db(config.db_path).close()
    from .webapp import serve  # imported lazily so the CLI works without the web module
    serve(config, host=args.host, port=args.port)
    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    config = _config(args)
    db.init_db(config.db_path).close()
    from .mcp_server import main as mcp_main
    argv: List[str] = ["--config", str(config.path or "config.json"), "--db", str(config.db_path)]
    return int(mcp_main(argv) or 0)


def cmd_seed_demo(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = db.init_db(config.db_path)
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


def cmd_rescore(args: argparse.Namespace) -> int:
    config = _config(args)
    count = rescore_all(config)
    print(f"Rescored {count} listings using scoring.mode='{config.scoring.get('mode', 'smooth')}'.")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    config = _config(args)
    conn = db.init_db(config.db_path)
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
    python = sys.executable
    root = PROJECT_ROOT
    hour, minute = args.at.split(":") if ":" in args.at else (args.at, "0")
    line = f"{int(minute)} {int(hour)} * * * cd {root} && {python} -m carmon run >> {root}/data/cron.log 2>&1"
    print("# Add this to your crontab (`crontab -e`):")
    print(line)
    print("\n# Or install it now with:")
    print(f'(crontab -l 2>/dev/null; echo "{line}") | crontab -')
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
    notify_cmd.set_defaults(func=cmd_notify)

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

    cron = sub.add_parser("cron", help="print a crontab line for the daily run")
    cron.add_argument("--at", default="7:30", help="local time HH:MM (default 7:30)")
    cron.set_defaults(func=cmd_cron)

    selftest = sub.add_parser("selftest", help="run the bundled test suite")
    selftest.set_defaults(func=cmd_selftest)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
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
