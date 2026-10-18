"""The enricher that combines swappable taggers, a summarizer and fact extractors.

Config, every part optional:

    [enricher]
    type = "composite"
    taggers = ["title-and-links", "gliner-entities",
               { type = "llm", fallback = ["embedding-categories", "keyphrases"] }]
    summarizer = { type = "llm", fallback = "extractive" }
    fact_extractors = ["patterns", { type = "llm" }]

Each part may name fallbacks. When a part is unavailable (server down, model
missing) its fallbacks run instead and the result is marked degraded; `run`
redoes degraded videos once the part is available again. Several taggers or
fact extractors add up; for the summarizer the first that works is used.

The presets "local", "keyword", "models" and "llm" are composites with
parts already chosen.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ..models import Enrichment
from ..registry import create, register
from .base import EnrichmentPart, Enricher, PartUnavailable, normalize_tags

log = logging.getLogger(__name__)


@dataclass
class PartSlot:
    """One configured part and what to use when it cannot run. Fallbacks are
    slots too, so a fallback can have its own fallback (llm > seq2seq > extractive)."""
    primary: EnrichmentPart
    fallbacks: list["PartSlot"] = field(default_factory=list)

    @property
    def name(self) -> str:
        if not self.fallbacks:
            return self.primary.name
        return f"{self.primary.name}>{'+'.join(fallback.name for fallback in self.fallbacks)}"

    def primaries_available(self) -> bool:
        return self.primary.is_available()

    def call(self, method_name: str, *arguments, cheap: bool = False):
        """Returns (results from each part that ran, degraded). `cheap` goes
        straight to the fallbacks when there are some, for sponsor segments."""
        if cheap and self.fallbacks:
            return self._call_fallbacks(method_name, arguments, cheap=True)
        try:
            return [getattr(self.primary, method_name)(*arguments)], False
        except PartUnavailable as error:
            # Not now. Use the fallbacks (none means: skip this part), and mark
            # the result degraded so `run` redoes it once the part can run.
            log.warning("%s unavailable, %s: %s", self.primary.name,
                        f"using {', '.join(fallback.name for fallback in self.fallbacks)}" if self.fallbacks
                        else "skipping it", error)
            results, _ = self._call_fallbacks(method_name, arguments)
            return results, True
        except Exception:
            # A bad reply or a bug in one part should not lose the whole video.
            log.exception("%s failed on this section, %s", self.primary.name,
                          "using its fallbacks" if self.fallbacks else "skipping it")
            return self._call_fallbacks(method_name, arguments)

    def _call_fallbacks(self, method_name: str, arguments: tuple, cheap: bool = False):
        results, degraded = [], False
        for fallback in self.fallbacks:
            fallback_results, fallback_degraded = fallback.call(method_name, *arguments, cheap=cheap)
            results += fallback_results
            degraded |= fallback_degraded
        return results, degraded


def _build_slot(kind: str, spec, app) -> PartSlot:
    spec = {"type": spec} if isinstance(spec, str) else dict(spec)
    fallback_specs = spec.pop("fallback", [])
    if isinstance(fallback_specs, (str, dict)):
        fallback_specs = [fallback_specs]
    return PartSlot(create(kind, spec, app), [_build_slot(kind, fallback, app) for fallback in fallback_specs])


@register("enricher", "composite")
class CompositeEnricher(Enricher):
    def __init__(self, tagger_slots: list[PartSlot], summarizer_slot: PartSlot | None,
                 fact_slots: list[PartSlot], max_tags: int = 12, label: str = "composite"):
        self.tagger_slots = tagger_slots
        self.summarizer_slot = summarizer_slot
        self.fact_slots = fact_slots
        self.max_tags = max_tags
        self.label = label

    @classmethod
    def from_config(cls, params, app=None):
        params = dict(params)
        return cls(
            tagger_slots=[_build_slot("tagger", spec, app) for spec in params.pop("taggers", [])],
            summarizer_slot=_build_slot("summarizer", params.pop("summarizer"), app)
            if params.get("summarizer") else None,
            fact_slots=[_build_slot("fact_extractor", spec, app) for spec in params.pop("fact_extractors", [])],
            **{key: value for key, value in params.items() if key != "summarizer"})

    @property
    def name(self) -> str:
        parts = [f"tags={'+'.join(slot.name for slot in self.tagger_slots)}",
                 f"summary={self.summarizer_slot.name if self.summarizer_slot else 'none'}",
                 f"facts={'+'.join(slot.name for slot in self.fact_slots)}"]
        return f"{self.label}({', '.join(parts)})"

    def _all_slots(self) -> list[PartSlot]:
        return self.tagger_slots + self.fact_slots + ([self.summarizer_slot] if self.summarizer_slot else [])

    def upgrade_available(self) -> bool:
        upgradable = [slot for slot in self._all_slots() if slot.fallbacks]
        return bool(upgradable) and all(slot.primaries_available() for slot in upgradable)

    def enrich_section(self, video_info, section) -> Enrichment:
        cheap = section.is_sponsor          # no LLM time spent on advertisements
        degraded = False
        tags: list[str] = []
        for slot in self.tagger_slots:
            results, slot_degraded = slot.call("tag_section", video_info, section, cheap=cheap)
            degraded |= slot_degraded
            for result in results:
                tags += result
        summary = ""
        if self.summarizer_slot:
            results, slot_degraded = self.summarizer_slot.call("summarize_section", video_info, section,
                                                               cheap=cheap)
            degraded |= slot_degraded
            summary = next((result for result in results if result), "")
        facts: list[str] = []
        for slot in self.fact_slots:
            results, slot_degraded = slot.call("extract_facts", video_info, section, cheap=cheap)
            degraded |= slot_degraded
            for result in results:
                facts += [fact for fact in result if fact not in facts]
        if section.is_sponsor and "sponsor" not in tags:
            tags.insert(0, "sponsor")
        return Enrichment(summary=summary, tags=normalize_tags(tags, self.max_tags), facts=facts,
                          model=self.name, degraded=degraded)

    def enrich_video(self, video_info, sections, transcript_text) -> Enrichment:
        degraded = False
        tags: list[str] = []
        for slot in self.tagger_slots:
            results, slot_degraded = slot.call("tag_video", video_info, sections)
            degraded |= slot_degraded
            for result in results:
                tags += result
        summary = ""
        if self.summarizer_slot:
            results, slot_degraded = self.summarizer_slot.call("summarize_video", video_info, sections,
                                                               transcript_text)
            degraded |= slot_degraded
            summary = next((result for result in results if result), "")
        return Enrichment(summary=summary, tags=normalize_tags(tags, self.max_tags + 5),
                          model=self.name, degraded=degraded)


# ---- presets -----------------------------------------------------------------

PRESETS: dict[str, dict] = {
    # Only the embedding model that search already loads.
    "local": {"taggers": ["title-and-links", "embedding-categories", "keyphrases"],
              "summarizer": "extractive", "fact_extractors": ["patterns"]},
    # Nothing at all.
    "keyword": {"taggers": ["title-and-links", "word-counts"],
                "summarizer": "first-sentences", "fact_extractors": ["patterns"]},
    # Dedicated small models: GLiNER2 for names and facts, DistilBART for
    # summaries, embeddings for topics (they beat GLiNER and NLI at topics).
    "models": {"taggers": ["title-and-links", "embedding-categories",
                           {"type": "gliner-entities", "fallback": "keyphrases"}],
               "summarizer": {"type": "seq2seq", "fallback": "extractive"},
               "fact_extractors": ["patterns", {"type": "gliner", "fallback": []}]},
}


def _preset_spec(preset_name: str, settings: dict) -> dict:
    """Apply shared settings (categories, max_tags) to the preset's parts."""
    spec = {key: value for key, value in PRESETS[preset_name].items()}
    categories = settings.pop("categories", None)
    if categories:
        spec["taggers"] = [{"type": tagger, "categories": categories}
                           if tagger in ("embedding-categories", "zero-shot-categories") else tagger
                           for tagger in spec["taggers"]]
    spec.update(settings)
    return spec


def _register_preset(preset_name: str):
    @register("enricher", preset_name)
    class PresetEnricher(CompositeEnricher):
        __doc__ = f"The {preset_name!r} preset: {PRESETS[preset_name]}"

        @classmethod
        def from_config(cls, params, app=None):
            enricher = CompositeEnricher.from_config(_preset_spec(preset_name, dict(params)), app)
            enricher.label = preset_name
            return enricher

    PresetEnricher.__name__ = f"{preset_name.title()}Enricher"
    return PresetEnricher


for _preset_name in PRESETS:
    _register_preset(_preset_name)


@register("enricher", "llm")
class LLMEnricher(CompositeEnricher):
    """LLM tags, summary and facts (one call per section), falling back to
    another preset's parts while the LLM is unavailable. Pattern facts are
    always kept as well: small models drop numbers the patterns catch.

        [enricher]
        type = "llm"
        fallback = "local"            # or "models", "keyword"
        section_prompt = "..."        # optional, see enrich/llm_parts.py
    """

    @classmethod
    def from_config(cls, params, app=None):
        params = dict(params)
        fallback = params.pop("fallback", "local")
        if isinstance(fallback, dict):        # older configs: fallback = { type = "local" }
            fallback = fallback.get("type", "local")
        max_tags = params.pop("max_tags", 12)
        params.pop("skip_sponsor", None)      # sponsors always use the cheap parts now
        llm_settings = {key: params.pop(key) for key in list(params)
                        if key in ("section_prompt", "video_prompt", "system_prompt",
                                   "max_section_characters", "max_video_characters")}
        if params:
            raise TypeError(f"unexpected argument(s) {sorted(params)}")
        llm_part = {"type": "llm", **llm_settings, "max_tags": max_tags}
        preset = PRESETS[fallback]
        fallback_taggers = [tagger for tagger in preset["taggers"] if tagger != "title-and-links"]
        spec = {
            "taggers": ["title-and-links", {**llm_part, "fallback": fallback_taggers}],
            "summarizer": {**llm_part, "fallback": preset["summarizer"]},
            "fact_extractors": [{**llm_part, "fallback": []}] + list(preset["fact_extractors"]),
            "max_tags": max_tags,
        }
        enricher = CompositeEnricher.from_config(spec, app)
        enricher.label = f"llm[{app.llm.name}]"
        return enricher
