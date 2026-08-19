"""`reliability`, `enrich` and `rescore` — NHTSA/EPA data and recomputing scores from it."""

from __future__ import annotations

import argparse
import sys

from .. import db, fueleconomy, nhtsa
from ..pipeline import rescore_all
from . import common


def cmd_enrich(args: argparse.Namespace) -> int:
    """Refresh the free NHTSA and EPA data for every model-year in the database."""
    config = common.config(args)
    with common.db_session(config) as conn:
        enrichment_config = config.data.get("enrichment", {})
        model_years = db.distinct_model_years(conn, active_only=not args.all)
        if args.limit:
            model_years = model_years[: args.limit]
        if not model_years:
            print("No listings stored yet — run `python3 -m carmon run` or `seed-demo` first.")
            return 0

        print(f"Refreshing free data for {len(model_years)} model-year(s). No API key needed.")
        summary = {}
        if not args.mpg_only:
            summary["nhtsa"] = nhtsa.enrich_models(conn, model_years, enrichment_config, force_refresh=args.force)
        if not args.nhtsa_only:
            summary["mpg"] = fueleconomy.enrich_models(conn, model_years, enrichment_config, force_refresh=args.force)
        common.print_json(summary)

        rescored = rescore_all(config, conn=conn)
        print(f"Rescored {rescored} listings with the refreshed data.")
        return 0


def cmd_reliability(args: argparse.Namespace) -> int:
    """Show what NHTSA knows about one model-year."""
    config = common.config(args)
    with common.db_session(config) as conn:
        facts = db.get_reliability(conn, args.make, args.model, args.year)
        if facts is None and not args.no_fetch:
            client = nhtsa.NHTSAClient(conn, config.data.get("enrichment", {}))
            facts = client.facts_for(args.make, args.model, args.year)
        if facts is None:
            print(f"No NHTSA data for {args.year} {args.make} {args.model}.", file=sys.stderr)
            return 1
        if args.json:
            common.print_json(facts, default=str)
            return 0

        _print_reliability(args, conn, facts)
        return 0


def _print_reliability(args: argparse.Namespace, conn, facts: dict) -> None:
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


def cmd_rescore(args: argparse.Namespace) -> int:
    config = common.config(args)
    count = rescore_all(config)
    print(f"Rescored {count} listings using scoring.mode='{config.scoring.get('mode', 'smooth')}'.")
    return 0


def add_enrich_parser(sub) -> None:
    enrich = sub.add_parser("enrich", help="refresh free NHTSA + EPA MPG data, then rescore")
    enrich.add_argument("--force", action="store_true", help="ignore the cache and refetch")
    enrich.add_argument("--limit", type=int, help="only process the first N model-years")
    enrich.add_argument("--all", action="store_true", help="include inactive (sold) listings")
    enrich.add_argument("--nhtsa-only", action="store_true", dest="nhtsa_only")
    enrich.add_argument("--mpg-only", action="store_true", dest="mpg_only")
    enrich.set_defaults(func=cmd_enrich)


def add_reliability_parser(sub) -> None:
    reliability = sub.add_parser("reliability", help="NHTSA complaints and recalls for one model-year")
    reliability.add_argument("--make", required=True)
    reliability.add_argument("--model", required=True)
    reliability.add_argument("--year", type=int, required=True)
    reliability.add_argument("--json", action="store_true")
    reliability.add_argument("--no-fetch", action="store_true", dest="no_fetch",
                             help="only read the cache, never call NHTSA")
    reliability.set_defaults(func=cmd_reliability)


def add_rescore_parser(sub) -> None:
    rescore = sub.add_parser("rescore", help="recompute every stored score with the current config")
    rescore.set_defaults(func=cmd_rescore)
