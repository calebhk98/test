"""`market`, `appraise` and `deals` — comparing listings against the local market."""

from __future__ import annotations

import argparse
import sys

from .. import market
from ..pipeline import refresh_market_values
from . import common


def cmd_market(args: argparse.Namespace) -> int:
    """Market trends: what things cost, how fast they move, and how much sellers cut."""
    config = common.config(args)
    with common.db_session(config) as conn:
        if args.refresh:
            summary = refresh_market_values(config, conn)
            print(f"Re-appraised {summary['listings_appraised']} listing(s); "
                  f"{summary['below_market']} sit more than 5% below expected.")
        report = market.market_report(conn, months=args.months, config=config)
        if args.json:
            common.print_json(report, default=str)
            return 0

        _print_market_report(report, args.limit)
        return 0


def _print_market_report(report: dict, deal_limit: int) -> None:
    print(f"Market report — {report['listings_tracked']} real listings tracked")
    print(f"\n{report['data_note']}\n")

    _print_price_trend(report["trend"])
    _print_days_and_cuts(report["days_on_market"], report["price_cuts"])
    _print_models(report["models"])
    _print_best_deals(report["best_deals"], deal_limit)


def _print_price_trend(trend: list) -> None:
    if not trend:
        print("No price history yet — this fills in once the daily job has run a few times.")
        return
    print("Median asking price by month")
    widest = max(row["median_price"] for row in trend) or 1
    for row in trend:
        bar_width = max(1, round(28 * row["median_price"] / widest))
        change = ""
        if row.get("change_vs_previous") is not None:
            change = f"  {row['change_vs_previous']:+,} ({row['change_pct']:+.1f}%)"
        print(f"  {row['month']}  {'█' * bar_width:<28} {common.money(row['median_price'])}"
              f"  n={row['observations']:<4}{change}")


def _print_days_and_cuts(dom: dict, cuts: dict) -> None:
    median_days = dom["median_days"]
    print(f"\nDays on market: median {median_days if median_days is not None else 'n/a'} "
          f"(from {dom['sample_size']} listings that have since vanished)")
    print(f"Price cuts: {cuts['cut_count']} of {cuts['tracked']} tracked listings "
          f"({cuts['cut_share_pct'] or 0}%), median cut {common.money(cuts['median_cut'])}"
          + (f" ({cuts['median_cut_pct']}%)" if cuts.get("median_cut_pct") else ""))


def _print_models(models: list) -> None:
    if not models:
        return
    print("\nBy model")
    header = f"  {'model':<28}{'n':>4}  {'median':>9}  {'range':>19}  {'$/1k mi':>8}  {'days':>5}  cuts"
    print(header)
    for row in models:
        name = f"{row['make']} {row['model']}"
        price_range = f"{common.money(row['min_price'])}–{common.money(row['max_price'])}"
        per_mile = f"{row['dollars_per_1k_miles']:.0f}" if row["dollars_per_1k_miles"] else "—"
        days = row["days_on_market"]["median_days"]
        days = f"{days:.0f}" if days is not None else "—"
        print(f"  {name[:28]:<28}{row['sample_size']:>4}  {common.money(row['median_price']):>9}  "
              f"{price_range:>19}  {per_mile:>8}  {days:>5}  "
              f"{row['price_cuts']['cut_share_pct'] or 0}%")


def _print_best_deals(deals: list, limit: int) -> None:
    if not deals:
        return
    print("\nBest deals right now (price versus expected for that mileage and year)")
    for item in deals[:limit]:
        appraisal = item["appraisal"]
        print(f"  {appraisal['grade_icon']} {item['year']} {item['make']} {item['model']} — "
              f"{common.money(item['price_current'])} vs {common.money(appraisal['expected_price'])} expected "
              f"({appraisal['delta']:+,}, {appraisal['delta_pct']:+.1f}%) · "
              f"{item['mileage']:,} mi · n={appraisal['sample_size']} "
              f"({appraisal['confidence']} confidence)")


def cmd_appraise(args: argparse.Namespace) -> int:
    """Compare one car — real or hypothetical — against the local market."""
    config = common.config(args)
    with common.db_session(config) as conn:
        if args.vin:
            result = market.appraise_vin(conn, args.vin, config)
            if result is None:
                print(f"No stored listing with VIN {args.vin}.", file=sys.stderr)
                return 1
        else:
            result = market.appraise(conn, {
                "make": args.make, "model": args.model, "year": args.year,
                "mileage": args.mileage, "price_current": args.price,
            }, config)

        if args.json:
            common.print_json(result.as_dict())
            return 0

        print(result.summary())
        print(f"  basis: {result.basis} ({result.basis_level}), method: {result.method}"
              + (f", r² {result.r_squared}" if result.r_squared is not None else ""))
        if result.comparable_median:
            low, high = result.comparable_range or (None, None)
            print(f"  comparables: median {common.money(result.comparable_median)}, "
                  f"range {common.money(low)}–{common.money(high)}, n={result.sample_size}")
        if result.dollars_per_model_year:
            print(f"  each newer model year is worth about {common.money(result.dollars_per_model_year)} here")
        for note in result.notes:
            print(f"  ⚠️  {note}")
        print("  This compares asking prices only — it knows nothing about condition, trim, options,")
        print("  accident history or title status. Always inspect the car itself.")
        return 0


def cmd_deals(args: argparse.Namespace) -> int:
    config = common.config(args)
    with common.db_session(config) as conn:
        deals = market.best_deals(conn, limit=args.limit, min_sample=args.min_sample, config=config)
        if args.json:
            common.print_json(deals, default=str)
            return 0
        if not deals:
            print("No listings have enough comparables to grade yet. Let the daily job run for a few days.")
            return 0
        for item in deals:
            appraisal = item["appraisal"]
            print(f"{appraisal['grade_icon']} {appraisal['grade']}: {item['year']} {item['make']} "
                  f"{item['model']} {item.get('trim') or ''}".rstrip())
            print(f"    {common.money(item['price_current'])} vs {common.money(appraisal['expected_price'])} expected "
                  f"({appraisal['delta']:+,}, {appraisal['delta_pct']:+.1f}%) · {item['mileage']:,} mi · "
                  f"score {item.get('score', 0):+.2f} · n={appraisal['sample_size']} "
                  f"({appraisal['confidence']} confidence)")
            if item.get("listing_url"):
                print(f"    {item['listing_url']}")
        return 0


def add_market_parser(sub) -> None:
    market_cmd = sub.add_parser("market", help="price trends, days on market, and per-model stats")
    market_cmd.add_argument("--months", type=int, default=6)
    market_cmd.add_argument("--limit", type=int, default=5, help="how many best deals to list")
    market_cmd.add_argument("--refresh", action="store_true", help="re-appraise every listing first")
    market_cmd.add_argument("--json", action="store_true")
    market_cmd.set_defaults(func=cmd_market)


def add_appraise_parser(sub) -> None:
    appraise = sub.add_parser("appraise", help="is this price good? compare one car to the market")
    appraise.add_argument("--vin", help="appraise a stored listing instead of a hypothetical car")
    appraise.add_argument("--make")
    appraise.add_argument("--model")
    appraise.add_argument("--year", type=int)
    appraise.add_argument("--mileage", type=int)
    appraise.add_argument("--price", type=int, help="asking price to grade")
    appraise.add_argument("--json", action="store_true")
    appraise.set_defaults(func=cmd_appraise)


def add_deals_parser(sub) -> None:
    deals = sub.add_parser("deals", help="active listings ranked by price versus expected")
    deals.add_argument("--limit", type=int, default=10)
    deals.add_argument("--min-sample", type=int, default=3, dest="min_sample")
    deals.add_argument("--json", action="store_true")
    deals.set_defaults(func=cmd_deals)
