"""The "build a WHERE clause from optional filters" pattern, factored out once.

`db.search_listings`, `market.comparables`, `market.price_trend`, `market.days_on_market`,
`market.price_cut_stats`, `db.recent_scrape_events` and `db.scrape_usage_*` all did the same
thing by hand: start a list of SQL fragments and a matching list of bound parameters, append
to both only when an optional argument was actually supplied, then join everything into
``WHERE a AND b AND c``. `Filters` holds that accumulator so each call site only has to say
what makes it different — the column, the comparison, the value.
"""

from __future__ import annotations

from typing import Any, List, Optional


class Filters:
    """Accumulates SQL clauses and their bound parameters for one query."""

    def __init__(self, *always: str) -> None:
        self.clauses: List[str] = list(always)
        self.params: List[Any] = []

    def add(self, clause: str, *values: Any) -> "Filters":
        """Add a clause unconditionally — for callers that already checked."""
        self.clauses.append(clause)
        self.params.extend(values)
        return self

    def where(self) -> str:
        return f"WHERE {' AND '.join(self.clauses)}" if self.clauses else ""


def eq(filters: Filters, column: str, value: Any) -> None:
    """`column = ?`, added only when `value` is truthy (case-sensitive match)."""
    if value:
        filters.add(f"{column} = ?", value)


def eq_lower(filters: Filters, column: str, value: Optional[str]) -> None:
    """`LOWER(column) = LOWER(?)`, added only when `value` is truthy."""
    if value:
        filters.add(f"LOWER({column}) = LOWER(?)", value)


def prefix_lower(filters: Filters, column: str, value: Optional[str]) -> None:
    """`LOWER(column) LIKE LOWER('value%')`, added only when `value` is truthy."""
    if value:
        filters.add(f"LOWER({column}) LIKE LOWER(?)", f"{value}%")


def compare(filters: Filters, column: str, op: str, value: Any) -> None:
    """`column <op> ?`, added only when `value` is not None (0 and False are real values)."""
    if value is not None:
        filters.add(f"{column} {op} ?", value)
