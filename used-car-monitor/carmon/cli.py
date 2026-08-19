"""Command line entry point: `python -m carmon <command>`."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from . import __version__
from .commands import demo, market, reliability, run, scrape, system
from .config import ConfigError


def _ensure_env() -> None:
    """Create a documented, blank .env on first run — no copying an example file."""
    from .settings import ensure_env_file
    if ensure_env_file():
        print("Created .env (chmod 600) with every secret blank and where to get each one.",
              file=sys.stderr)
        print("Fill it in there, or on the website: python3 -m carmon serve → Settings.",
              file=sys.stderr)


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

    # Order here is the order `--help` lists subcommands in — keep it stable.
    run.add_run_parser(sub)
    run.add_digest_parser(sub)
    run.add_notify_parser(sub)
    run.add_quota_parser(sub)
    system.add_serve_parser(sub)
    system.add_mcp_parser(sub)
    demo.add_seed_demo_parser(sub)
    reliability.add_enrich_parser(sub)
    reliability.add_reliability_parser(sub)
    system.add_config_check_parser(sub)
    market.add_market_parser(sub)
    market.add_appraise_parser(sub)
    market.add_deals_parser(sub)
    scrape.add_scrape_parser(sub)
    scrape.add_settings_parser(sub)
    reliability.add_rescore_parser(sub)
    demo.add_stats_parser(sub)
    demo.add_sources_parser(sub)
    demo.add_score_parser(sub)
    demo.add_cron_parser(sub)
    system.add_selftest_parser(sub)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    _force_utf8_output()
    _ensure_env()
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
