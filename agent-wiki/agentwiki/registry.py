"""Component registry: config names a `type`, the registry finds the class.

To add a backend, subclass the relevant base class and decorate it:

    @register("embedder", "my-embedder")
    class MyEmbedder(Embedder): ...

then set `type = "my-embedder"` in config.toml. Classes in other packages are
picked up by listing their module under `plugins = [...]` in config.
"""
from __future__ import annotations

import importlib
from typing import Any, TypeVar

T = TypeVar("T")

_REGISTRY: dict[str, dict[str, type]] = {}


def register(kind: str, name: str):
    def decorator(cls):
        _REGISTRY.setdefault(kind, {})[name] = cls
        cls.registry_name = name
        return cls
    return decorator


def available(kind: str) -> list[str]:
    _load_builtins()
    return sorted(_REGISTRY.get(kind, {}))


def create(kind: str, spec: dict[str, Any] | str, app: Any = None):
    """Build a component from `{"type": name, **params}` (or just a name)."""
    _load_builtins()
    if isinstance(spec, str):
        spec = {"type": spec}
    spec = dict(spec)
    name = spec.pop("type", None)
    if not name:
        raise ValueError(f"{kind} config needs a 'type' (one of {available(kind)})")
    try:
        cls = _REGISTRY[kind][name]
    except KeyError:
        raise ValueError(f"unknown {kind} type {name!r}; known: {available(kind)}") from None
    try:
        return cls.from_config(spec, app)
    except TypeError as error:
        if "argument" not in str(error):
            raise
        import inspect
        params = [parameter_name for parameter_name in inspect.signature(cls.__init__).parameters
                  if parameter_name != "self"]
        raise ValueError(f"[{kind}] type = {name!r}: {error}. Settings it accepts: {params}") from None


def load_plugins(modules: list[str]) -> None:
    for module_name in modules:
        importlib.import_module(module_name)


class Component:
    """Base for everything built from config.

    Override `from_config` when a component needs other components (for
    example an enricher that needs the configured LLM).
    """

    registry_name = ""

    @classmethod
    def from_config(cls, params: dict[str, Any], app: Any = None):
        return cls(**params)

    @property
    def name(self) -> str:
        """Identifier recorded next to anything this component produced."""
        return self.registry_name


_loaded = False


def _load_builtins() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    for module_name in (
        "agentwiki.sources.youtube",
        "agentwiki.sources.podcast",
        "agentwiki.sources.local_audio",
        "agentwiki.transcribe.faster_whisper",
        "agentwiki.transcribe.youtube_captions",
        "agentwiki.transcribe.chain",
        "agentwiki.segment.chapters",
        "agentwiki.segment.fixed_window",
        "agentwiki.segment.chain",
        "agentwiki.segment.topics",
        "agentwiki.llm.ollama",
        "agentwiki.llm.openai_compat",
        "agentwiki.llm.anthropic",
        "agentwiki.llm.null",
        "agentwiki.llm.transformers_local",
        "agentwiki.enrich.taggers",
        "agentwiki.enrich.summarizers",
        "agentwiki.enrich.fact_extractors",
        "agentwiki.enrich.llm_parts",
        "agentwiki.enrich.composite",
        "agentwiki.embed.sentence_transformers",
        "agentwiki.embed.ollama",
        "agentwiki.embed.openai_compat",
        "agentwiki.embed.hashing",
        "agentwiki.index.sqlite_index",
    ):
        importlib.import_module(module_name)
