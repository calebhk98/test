"""Lazy-import helpers for optional/heavier dependency chains.

Several tool handlers only need a carmon submodule at call time -- either
because the dependency is genuinely optional (scrapers, the NHTSA client) or
because eagerly importing it would slow down server startup for tools that
never touch it. That used to mean a 'try: from .x import y, z / except
ImportError: ...' block repeated with small variations in half a dozen
handlers; these two helpers cover both variations that actually occurred:
silently falling back to None, or failing the tool with a clear message.
"""

from __future__ import annotations

import importlib
from typing import Tuple

from .protocol import ToolError


def try_import(module_name: str, *names: str) -> Tuple:
    """Best-effort import of `names` from carmon.<module_name>.

    Returns a tuple the same length as `names`: the imported objects, or all
    None if the module can't be imported. Never raises.
    """
    try:
        module = importlib.import_module(f"carmon.{module_name}")
    except ImportError:
        return tuple(None for _ in names)
    return tuple(getattr(module, name) for name in names)


def import_required(module_name: str, label: str, *names: str):
    """Import `names` from carmon.<module_name> or raise a ToolError.

    For the tools that genuinely can't do their job without the module (e.g.
    'refresh_reliability' needs the NHTSA client) -- ToolError is caught by
    the tools/call dispatcher and turned into an isError result carrying this
    exact message, matching what each handler used to build by hand. Returns
    the single imported object directly if only one name was requested,
    otherwise a tuple in the order given.
    """
    try:
        module = importlib.import_module(f"carmon.{module_name}")
    except ImportError as exc:
        raise ToolError(f"{label} is not available: {exc}") from exc
    values = tuple(getattr(module, name) for name in names)
    return values[0] if len(values) == 1 else values
