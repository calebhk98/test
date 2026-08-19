"""`run`, `digest`, `notify` and `quota` — the daily job and what it reports."""

from __future__ import annotations

import argparse
import sys
from datetime import date

from .. import digest as digest_module, notify, quota
from ..config import get_secret, validate_config
from ..pipeline import run_daily
from . import common


def cmd_run(args: argparse.Namespace) -> int:
    config = common.config(args)
    for warning in validate_config(config):
        print(f"config warning: {warning}", file=sys.stderr)
    with common.db_session(config) as conn:
        run_date = args.date or date.today().isoformat()
        print(f"Running daily job for {run_date} (db: {config.db_path})")

        result = run_daily(config, conn=conn, run_date=run_date, dry_run=args.dry_run)
        summary = result.as_dict()
        common.print_json(summary)

        markdown = digest_module.render_digest(config, conn, run_date=run_date, run_result=summary, days=args.days)
        if args.dry_run:
            print("\n--- digest (dry run, not saved) ---\n")
            print(markdown)
            return 1 if result.errors else 0

        path = digest_module.save_digest(config, markdown, run_date=run_date)
        print(f"Digest written to {path}")
        conn.execute("UPDATE runs SET digest_path = ? WHERE id = (SELECT MAX(id) FROM runs)", (str(path),))
        conn.commit()

        if not args.no_discord:
            try:
                _post_to_discord(config, conn, args, run_date, summary)
            except notify.DiscordError as exc:
                print(f"Discord delivery failed: {exc}", file=sys.stderr)
                return 1
        return 1 if result.errors else 0


def _post_to_discord(config, conn, args: argparse.Namespace, run_date: str, summary: dict) -> None:
    """The Discord half of `cmd_run` — its own return path would need conn.close() too."""
    configured = get_secret("DISCORD_WEBHOOK_URL") or (
        get_secret("DISCORD_BOT_TOKEN") and get_secret("DISCORD_USER_ID")
    )
    if not configured:
        print(
            "No Discord delivery configured — set DISCORD_BOT_TOKEN + DISCORD_USER_ID (DM) "
            "or DISCORD_WEBHOOK_URL (channel) in .env."
        )
        return
    transport = notify.send_digest(
        config, conn, run_date=run_date, run_result=summary,
        web_url=args.web_url, mode=args.discord_mode,
    )
    print(
        "Digest sent as a Discord direct message."
        if transport == "dm" else "Digest posted to the Discord webhook channel."
    )


def cmd_digest(args: argparse.Namespace) -> int:
    config = common.config(args)
    with common.db_session(config) as conn:
        markdown = digest_module.render_digest(config, conn, run_date=args.date, days=args.days)
        if args.save:
            path = digest_module.save_digest(config, markdown, run_date=args.date)
            print(f"Digest written to {path}", file=sys.stderr)
        print(markdown)
        return 0


def cmd_notify(args: argparse.Namespace) -> int:
    config = common.config(args)
    with common.db_session(config) as conn:
        try:
            transport = notify.send_digest(
                config, conn, webhook_url=args.webhook, run_date=args.date,
                web_url=args.web_url, mode=args.discord_mode,
            )
        except notify.DiscordError as exc:
            print(f"Discord delivery failed: {exc}", file=sys.stderr)
            return 1
        print(
            "Digest sent as a Discord direct message."
            if transport == "dm" else "Digest posted to the Discord webhook channel."
        )
        return 0


def cmd_quota(args: argparse.Namespace) -> int:
    """Show MarketCheck usage against how much of the month has actually gone by."""
    config = common.config(args)
    with common.db_session(config) as conn:
        cap = int(config.api.get("monthly_call_cap", 500))
        metrics = quota.pace_from_db(conn, cap)
        sweep = quota.sweep_budget(metrics["used"], cap, config.api.get("month_end_sweep", {}))
        if args.json:
            common.print_json({**metrics, "summary": quota.summary_line(metrics),
                               "bar": quota.bar(metrics), "month_end_sweep": sweep})
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
        return 0


def add_run_parser(sub) -> None:
    run = sub.add_parser("run", help="the daily job: fetch, store, score, digest, Discord")
    run.add_argument("--dry-run", action="store_true", help="fetch and score but write nothing")
    run.add_argument("--no-discord", action="store_true", help="skip the Discord post")
    run.add_argument("--date", help="run date (YYYY-MM-DD), defaults to today")
    run.add_argument("--days", type=int, default=1, help="digest lookback window in days")
    run.add_argument("--web-url", help="link to your website, included in the Discord message")
    run.add_argument("--discord-mode", dest="discord_mode", choices=("auto", "dm", "webhook"),
                     help="how to deliver: dm, webhook, or auto (default, from config.json)")
    run.set_defaults(func=cmd_run)


def add_digest_parser(sub) -> None:
    digest = sub.add_parser("digest", help="render the digest from stored data (no API calls)")
    digest.add_argument("--date", help="digest date (YYYY-MM-DD)")
    digest.add_argument("--days", type=int, default=1, help="lookback window in days")
    digest.add_argument("--save", action="store_true", help="also write it to the digest directory")
    digest.set_defaults(func=cmd_digest)


def add_notify_parser(sub) -> None:
    notify_cmd = sub.add_parser("notify", help="post the current digest to Discord")
    notify_cmd.add_argument("--webhook", help="webhook URL (defaults to DISCORD_WEBHOOK_URL)")
    notify_cmd.add_argument("--date", help="digest date (YYYY-MM-DD)")
    notify_cmd.add_argument("--web-url", help="link to your website, included in the message")
    notify_cmd.add_argument("--mode", dest="discord_mode", choices=("auto", "dm", "webhook"),
                            help="dm = direct message (needs DISCORD_BOT_TOKEN + DISCORD_USER_ID); "
                                 "webhook = server channel; auto = DM if configured, else webhook")
    notify_cmd.set_defaults(func=cmd_notify)


def add_quota_parser(sub) -> None:
    quota_cmd = sub.add_parser("quota", help="MarketCheck usage vs how much of the month has passed")
    quota_cmd.add_argument("--json", action="store_true")
    quota_cmd.set_defaults(func=cmd_quota)
