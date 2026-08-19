"""`serve`, `mcp`, `config-check` and `selftest` — process-level and diagnostic commands."""

from __future__ import annotations

import argparse
from typing import List, Optional

from ..config import PROJECT_ROOT, validate_config
from . import common


def cmd_serve(args: argparse.Namespace) -> int:
    config = common.config(args)
    common.touch_db(config)
    from ..webapp import serve  # imported lazily so the CLI works without the web module
    serve(config, host=args.host, port=args.port)
    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    config = common.config(args)
    common.touch_db(config)
    from ..mcp_server import main as mcp_main
    argv: List[str] = ["--config", str(config.path or "config.json"), "--db", str(config.db_path)]
    return int(mcp_main(argv) or 0)


def cmd_config_check(args: argparse.Namespace) -> int:
    config = common.config(args)
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


def cmd_selftest(args: argparse.Namespace) -> int:
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(str(PROJECT_ROOT / "tests"), top_level_dir=str(PROJECT_ROOT))
    runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
    return 0 if runner.run(suite).wasSuccessful() else 1


def add_serve_parser(sub) -> None:
    serve = sub.add_parser("serve", help="run the website + JSON API")
    serve.add_argument("--host", help="bind host (default from config.web)")
    serve.add_argument("--port", type=int, help="bind port (default from config.web)")
    serve.set_defaults(func=cmd_serve)


def add_mcp_parser(sub) -> None:
    mcp = sub.add_parser("mcp", help="run the MCP server on stdio")
    mcp.set_defaults(func=cmd_mcp)


def add_config_check_parser(sub) -> None:
    config_check = sub.add_parser("config-check", help="validate config.json and report drift")
    config_check.set_defaults(func=cmd_config_check)


def add_selftest_parser(sub) -> None:
    selftest = sub.add_parser("selftest", help="run the bundled test suite")
    selftest.set_defaults(func=cmd_selftest)
