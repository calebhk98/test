"""`seed-demo`, `stats`, `sources`, `score` and `cron` — small self-contained commands."""

from __future__ import annotations

import argparse
import json
import os
import sys

from .. import db, demo as demo_module
from ..config import PROJECT_ROOT
from ..scoring import score_listing
from ..sources import build_sources, grouped_sources
from . import common


def cmd_seed_demo(args: argparse.Namespace) -> int:
    config = common.config(args)
    with common.db_session(config) as conn:
        if args.clear:
            removed = demo_module.clear_demo(conn)
            print(f"Removed {removed} demo listings.")
            return 0
        vins = demo_module.seed(config, conn, count=args.count)
        print(f"Seeded {len(vins)} demo listings into {config.db_path}")
        print("Browse them with:  python -m carmon serve")
        return 0


def cmd_stats(args: argparse.Namespace) -> int:
    config = common.config(args)
    with common.db_session(config) as conn:
        common.print_json(db.stats(conn, int(config.api.get("monthly_call_cap", 500))), default=str)
        return 0


def cmd_sources(args: argparse.Namespace) -> int:
    config = common.config(args)
    if args.json:
        common.print_json(grouped_sources(config.search))
        return 0
    for source in build_sources(config.search):
        print(f"[{source.category}] {source.name}\n  {source.url}\n  {source.note}\n")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    config = common.config(args)
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
        _print_windows_cron(python, root, hour, minute)
        return 0

    _print_unix_cron(python, root, hour, minute)
    return 0


def _print_windows_cron(python: str, root, hour: int, minute: int) -> None:
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


def _print_unix_cron(python: str, root, hour: int, minute: int) -> None:
    line = f"{minute} {hour} * * * cd {root} && {python} -m carmon run >> {root}/data/cron.log 2>&1"
    print("# Add this to your crontab (`crontab -e`):")
    print(line)
    print("\n# Or install it now with:")
    print(f'(crontab -l 2>/dev/null; echo "{line}") | crontab -')
    print("\n# macOS: cron works, but launchd is more idiomatic — or use the systemd units in deploy/ on Linux.")
    print("# For the Windows form of this command: python3 -m carmon cron --platform windows")


def add_seed_demo_parser(sub) -> None:
    seed = sub.add_parser("seed-demo", help="insert demo listings so the UI/API/MCP have data")
    seed.add_argument("--count", type=int, default=18)
    seed.add_argument("--clear", action="store_true", help="delete demo listings instead")
    seed.set_defaults(func=cmd_seed_demo)


def add_stats_parser(sub) -> None:
    stats = sub.add_parser("stats", help="DB and API-quota stats as JSON")
    stats.set_defaults(func=cmd_stats)


def add_sources_parser(sub) -> None:
    sources = sub.add_parser("sources", help="print the cross-shopping deep links")
    sources.add_argument("--json", action="store_true")
    sources.set_defaults(func=cmd_sources)


def add_score_parser(sub) -> None:
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


def add_cron_parser(sub) -> None:
    cron = sub.add_parser("cron", help="print the daily schedule command for this OS")
    cron.add_argument("--at", default="7:30", help="local time HH:MM (default 7:30)")
    cron.add_argument("--platform", choices=("unix", "windows"),
                      help="force the output style (default: detected from this machine)")
    cron.set_defaults(func=cmd_cron)
