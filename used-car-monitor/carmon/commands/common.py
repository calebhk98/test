"""Shared plumbing for CLI command bodies: config/DB setup, formatting, JSON output."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

from .. import db, demo as demo_module
from ..config import Config, load_config


def config(args: argparse.Namespace) -> Config:
    """Load config.json, applying the `--db` override shared by every subcommand."""
    cfg = load_config(args.config)
    if getattr(args, "db", None):
        cfg.data.setdefault("paths", {})["db"] = str(Path(args.db).resolve())
    return cfg


def open_db(cfg: Config):
    """Open the database and expire stale demo data before anything reads it."""
    conn = db.init_db(cfg.db_path)
    removed = demo_module.maybe_expire(conn, cfg)
    if removed:
        print(f"Cleared {removed} stale demo listing(s) automatically.", file=sys.stderr)
    banner = demo_module.demo_banner(conn)
    if banner:
        print(f"⚠️  {banner}", file=sys.stderr)
    return conn


@contextmanager
def db_session(cfg: Config) -> Iterator[Any]:
    """Open the DB for one command and guarantee it closes on every exit path."""
    conn = open_db(cfg)
    try:
        yield conn
    finally:
        conn.close()


def touch_db(cfg: Config) -> None:
    """Run the open_db side effects (demo expiry, banner) without keeping a connection."""
    open_db(cfg).close()


def money(value: Optional[float]) -> str:
    return f"${value:,.0f}" if value not in (None, "") else "n/a"


def print_json(data: Any, default=None) -> None:
    print(json.dumps(data, indent=2, default=default))
