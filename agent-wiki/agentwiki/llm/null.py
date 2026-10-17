from __future__ import annotations

from ..registry import register
from .base import LLM, LLMError


@register("llm", "null")
class NullLLM(LLM):
    """No LLM configured. Enrichers fall back to keywords; `ask` returns search hits only."""

    def _ping(self) -> bool:
        return False

    def complete(self, prompt, system=None, **kw):
        raise LLMError("no LLM configured; set [llm] in config.toml")
