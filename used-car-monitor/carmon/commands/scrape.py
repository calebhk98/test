"""`scrape` and `settings` — optional scrapers and reading/writing config.json + .env."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict

from .. import db
from ..pipeline import probe_scrapers, run_scrapers
from . import common

# Shared by --status (per-adapter health) and --probe (live reachability check).
_STATUS_ICONS = {"ok": "✅", "blocked": "🚫", "disallowed": "⛔", "budget": "⏳",
                 "error": "❌", "empty": "⚠️ ", "unparsed": "⚠️ "}


def cmd_scrape(args: argparse.Namespace) -> int:
    """Run the optional scrapers — off by default, robots-obeying, hard-capped."""
    config = common.config(args)
    with common.db_session(config) as conn:
        scraper_config = config.data.get("scrapers", {}) or {}

        if args.status:
            _print_scrape_status(conn, scraper_config)
            return 0

        if args.probe:
            _print_scrape_probe(config, conn)
            return 0

        sources = [args.source] if args.source else None
        summary = run_scrapers(config, conn, sources=sources, dry_run=args.dry_run)
        common.print_json(summary, default=str)
        return 0 if summary.get("enabled") else 1


def _print_scrape_status(conn, scraper_config: Dict[str, Any]) -> None:
    usage = db.scrape_usage_today(conn)
    print(f"Scraper usage today ({usage['day']}):")
    print(f"  requests {usage['requests']} / {scraper_config.get('max_requests_per_day', 20)}")
    print(f"  listings {usage['listings']} / {scraper_config.get('max_listings_per_day', 100)}")
    for row in db.scrape_usage_by_source(conn):
        print(f"    {row['source']:<14} {row['requests']:>3} request(s), {row['listings']:>3} listing(s)")

    from ..scrapers import REGISTRY
    toggles = scraper_config.get("sources") or {}
    health = {row["source"]: row for row in db.get_scraper_status(conn)}
    print(f"\n  master switch: {'ON' if scraper_config.get('enabled') else 'OFF'}")
    print(f"  {'adapter':<12} {'on?':<5} {'state':<12} last run")
    for key in sorted(set(REGISTRY) | set(toggles)):
        row = health.get(key)
        state = row["status"] if row else "never run"
        icon = _STATUS_ICONS.get(state, "·")
        last = (row["last_run_at"][:16].replace("T", " ") if row and row.get("last_run_at") else "—")
        print(f"  {key:<12} {'yes' if toggles.get(key) else 'no':<5} {icon} {state:<10} {last}")
        if row and row.get("last_error"):
            print(f"      last error: {row['last_error'][:120]}")


def _print_scrape_probe(config, conn) -> None:
    print("Probing each adapter (one request each). Blocked or disallowed is a normal, "
          "expected answer — it means that site does not want automated traffic.\n")
    for entry in probe_scrapers(config, conn):
        icon = _STATUS_ICONS.get(entry["status"], "?")
        print(f"  {icon} {entry.get('name', entry['source']):<12} {entry['status']}")
        if entry.get("message"):
            print(f"       {entry['message'][:180]}")


def cmd_settings(args: argparse.Namespace) -> int:
    """Read and change config.json (and .env secrets) from the terminal.

    The same rules the website enforces apply here: known keys only, types may not change,
    and secrets are written to .env rather than printed.
    """
    from .. import settings as settings_module

    config = common.config(args)

    if args.secrets:
        _print_secrets(settings_module)
        return 0

    if args.set_secret:
        return _set_secret(settings_module, args.set_secret)

    if args.set:
        return _apply_settings(settings_module, config, args)

    return _print_settings(settings_module, config, args)


def _print_secrets(settings_module) -> None:
    print("Secrets (from .env; values are never printed):")
    for entry in settings_module.secrets_status():
        state = f"set {entry['masked']}" if entry["set"] else "not set"
        source = " (from the environment)" if entry["from_environment"] else ""
        print(f"  {entry['key']:<22} {state}{source}")
        print(f"      {entry['label']}")


def _set_secret(settings_module, key: str) -> int:
    import getpass
    value = getpass.getpass(f"Value for {key} (input hidden, blank to clear): ")
    try:
        settings_module.update_secrets({key: value})
    except settings_module.SettingsError as exc:
        print(f"Rejected: {exc}", file=sys.stderr)
        return 1
    print(f"{key} updated in .env (chmod 600).")
    return 0


def _parse_setting_value(raw: str, kind: str):
    """Coerce one `--set key=value` pair's raw text to its declared type, or raise ValueError."""
    if kind == "bool":
        if raw.lower() not in ("1", "0", "true", "false", "yes", "no", "on", "off"):
            raise ValueError("expected true/false")
        return raw.lower() in ("1", "true", "yes", "on")
    if kind == "number":
        return float(raw) if "." in raw else int(raw)
    if kind == "list":
        return [item.strip() for item in raw.split(",") if item.strip()]
    return raw


def _apply_settings(settings_module, config, args: argparse.Namespace) -> int:
    changes: Dict[str, Any] = {}
    fields = settings_module.editable_settings(config)
    for pair in args.set:
        if "=" not in pair:
            print(f"Expected key=value, got {pair!r}", file=sys.stderr)
            return 2
        key, _, raw = pair.partition("=")
        key, raw = key.strip(), raw.strip()
        field = fields.get(key)
        if field is None:
            print(f"Unknown setting: {key}", file=sys.stderr)
            return 2
        kind = field["type"]
        try:
            changes[key] = _parse_setting_value(raw, kind)
        except ValueError:
            print(f"{key} expects a {kind}, but got {raw!r}. Nothing was changed.", file=sys.stderr)
            return 2
    try:
        result = settings_module.apply_changes(config, changes, dry_run=args.dry_run)
    except settings_module.SettingsError as exc:
        print(f"Rejected (nothing was changed): {exc}", file=sys.stderr)
        return 1
    for key, value in result["applied"].items():
        print(f"{'would set' if args.dry_run else 'set'} {key} = {value!r}")
    for warning in result["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)
    if result.get("backup"):
        print(f"previous config archived to {result['backup']}")
    return 0


def _print_settings(settings_module, config, args: argparse.Namespace) -> int:
    fields = settings_module.editable_settings(config)
    if args.json:
        common.print_json({key: field["value"] for key, field in fields.items()})
        return 0
    section = None
    for key, field in fields.items():
        if args.filter and args.filter not in key:
            continue
        head = key.split(".")[0]
        if head != section:
            section = head
            print(f"\n[{section}]")
        print(f"  {key:<44} {field['value']!r}")
    print("\nChange one with:  python3 -m carmon settings --set search.zip=37211")
    print("Secrets:          python3 -m carmon settings --secrets")
    return 0


def add_scrape_parser(sub) -> None:
    scrape = sub.add_parser("scrape", help="run the optional scrapers (off by default, capped)")
    scrape.add_argument("--source", help="run just this adapter, overriding its config toggle "
                                         "(the master scrapers.enabled switch still applies)")
    scrape.add_argument("--probe", action="store_true", help="one request per adapter: is it reachable?")
    scrape.add_argument("--status", action="store_true", help="today's scraper usage against the caps")
    scrape.add_argument("--dry-run", action="store_true",
                        help="fetch and parse but store nothing — still makes requests and still "
                             "spends the daily budget")
    scrape.set_defaults(func=cmd_scrape)


def add_settings_parser(sub) -> None:
    settings_cmd = sub.add_parser("settings", help="view or change config.json and .env")
    settings_cmd.add_argument("--set", action="append", metavar="KEY=VALUE",
                              help="change a setting (repeatable); applied all-or-nothing")
    settings_cmd.add_argument("--secrets", action="store_true", help="which secrets are set (masked)")
    settings_cmd.add_argument("--set-secret", metavar="KEY", help="set one secret, prompting without echo")
    settings_cmd.add_argument("--filter", help="only show keys containing this text")
    settings_cmd.add_argument("--dry-run", action="store_true", help="validate without writing")
    settings_cmd.add_argument("--json", action="store_true")
    settings_cmd.set_defaults(func=cmd_settings)
