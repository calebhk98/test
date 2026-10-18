"""Fact extractors: section -> searchable fact lines ("[size] Flux 2 was a 32B model")."""
from __future__ import annotations

import re

from ..registry import register
from .base import FactExtractor
from .gliner_model import DEFAULT_GLINER_MODEL, gliner_installed, load_gliner
from .text_tools import split_sentences, text_windows

_NUMBER = r"\d+(?:[.,]\d+)?"
# kind -> regular expression. Replace with `patterns = {...}` in config, or add
# to them with `extra_patterns = {...}`.
DEFAULT_PATTERNS: dict[str, str] = {
    "size": (rf"\b{_NUMBER}\s*(?:billion|million|trillion)\s+(?:active\s+)?param|"
             rf"\b{_NUMBER}\s?[BMT]\b(?!-?\w)|\bparameters?\b|\bmixture of experts\b|\bMoE\b"),
    "hardware": (rf"\b{_NUMBER}\s*(?:gb|gigs?|gigabytes?)\b|\bv?ram\b|\bconsumer (?:gpu|graphics card)s?\b|"
                 r"\b(?:rtx|gtx)\s?\d{3,4}\b|\b(?:h100|a100|b200|4090|5090|3090)\b|\bquantiz"),
    "license": (r"\bopen[- ]?(?:source|sourced|weights?)\b|\bclosed[- ]?(?:source|weights?)\b|\bproprietary\b|"
                r"\bapache\b|\bmit licen[cs]e\b|\bnon[- ]?commercial\b|\bhugging ?face\b|\bgithub\b|"
                r"\bweights\b|\bapi only\b|\bonly (?:available )?(?:via|through|on) (?:their|the|an) api\b"),
    "censorship": (r"\buncensored\b|\bcensor(?:ed|ship|s)?\b|\bnsfw\b|\bnot safe for work\b|\bnudity\b|"
                   r"\bcontent (?:filter|moderation|restrictions?|policy)\b|\bguardrails?\b|"
                   r"\bsafety filter\b|\brefuses?\b|\bspicy\b"),
    "speed": (rf"\breal[- ]?time\b|\b{_NUMBER}\s*(?:fps|frames per second|tokens? per second|it/s)\b|"
              rf"\b{_NUMBER}\s*(?:x|times) faster\b|\bin (?:just|under|about)?\s*{_NUMBER}\s*seconds\b|"
              r"\blatency\b|\bfastest\b"),
    "output": (rf"\b\d{{3,4}}p\b|\b[48]k\b|\b{_NUMBER}\s*(?:seconds?|minutes?) "
               rf"(?:long|of (?:video|audio|footage))\b|\bup to {_NUMBER}\s*(?:seconds?|minutes?)\b|\bresolution\b"),
    "price": (rf"\$\s?{_NUMBER}|\bfree to use\b|\bfor free\b|\bpricing\b|\bper month\b|"
              r"\bsubscription\b|\bpaid\b"),
    "benchmark": (r"\bbenchmarks?\b|\boutperform|\bbeats\b|\bstate of the art\b|\bsota\b|"
                  r"\bleaderboard\b|\belo\b|\bscores?\b"),
}


def _shorten(sentence: str, max_length: int) -> str:
    return sentence if len(sentence) <= max_length else sentence[: max_length - 3] + "..."


@register("fact_extractor", "patterns")
class PatternFactExtractor(FactExtractor):
    """The sentences that state a size, hardware need, licence, censorship,
    speed, output length, price or benchmark, found by regular expression and
    quoted with what kind of fact they are."""

    def __init__(self, patterns: dict[str, str] | None = None, extra_patterns: dict[str, str] | None = None,
                 max_facts: int = 12, max_length: int = 260):
        merged = dict(patterns or DEFAULT_PATTERNS)
        merged.update(extra_patterns or {})
        self.compiled_patterns = {kind: re.compile(expression, re.I) for kind, expression in merged.items()}
        self.max_facts = max_facts
        self.max_length = max_length

    def extract_from_text(self, text: str) -> list[str]:
        facts: list[str] = []
        seen: set[str] = set()
        for sentence in split_sentences(text):
            kinds = [kind for kind, pattern in self.compiled_patterns.items() if pattern.search(sentence)]
            if not kinds:
                continue
            shortened = _shorten(sentence, self.max_length)
            if shortened.lower() in seen:
                continue
            seen.add(shortened.lower())
            facts.append(f"[{', '.join(kinds)}] {shortened}")
            if len(facts) >= self.max_facts:
                break
        return facts

    def extract_facts(self, video_info, section):
        return self.extract_from_text(section.text)


DEFAULT_FACT_LABELS = {
    "model size": "number of parameters of an AI model, such as 7B, 32B or 400 billion parameters",
    "hardware requirement": "GPU, VRAM, memory or computer needed, such as 24 GB of VRAM, RTX 4090, a laptop CPU",
    "licence": "licence or openness, such as open weights, open source, Apache 2.0, non-commercial, API only",
    "content restriction": "whether outputs are censored, uncensored, filtered or restricted",
    "speed": "how fast it runs, such as real time, 30 fps, 2x faster, a few seconds",
    "price": "cost to use, such as free, $20 per month, price per image",
}


@register("fact_extractor", "gliner")
class GlinerFactExtractor(FactExtractor):
    """Facts found by a dedicated extraction model (GLiNER2), each quoted with
    the sentence it came from so an agent can check it. Labels and their
    descriptions are configurable. Asking GLiNER2 for whole JSON records
    returned run-on fragments on unpunctuated speech, so this uses its entity
    extraction and quotes the surrounding sentence instead."""

    def __init__(self, model: str = DEFAULT_GLINER_MODEL, labels: dict[str, str] | None = None,
                 min_confidence: float = 0.6, max_facts: int = 10, max_length: int = 260,
                 device: str = "auto"):
        self.model_name = model
        self.labels = labels or DEFAULT_FACT_LABELS
        self.min_confidence = min_confidence
        self.max_facts = max_facts
        self.max_length = max_length
        self.device = device

    @property
    def name(self) -> str:
        return f"gliner-facts[{self.model_name}]"

    def is_available(self) -> bool:
        return gliner_installed()

    def extract_facts(self, video_info, section):
        if section.is_sponsor:
            return []
        model = load_gliner(self.model_name, self.device)
        facts: list[str] = []
        seen_sentences: set[str] = set()
        for window in text_windows(section.text):
            result = model.extract_entities(window, self.labels, include_confidence=True, include_spans=True)
            for label, found in result.get("entities", {}).items():
                for entity in found:
                    if entity["confidence"] < self.min_confidence:
                        continue
                    sentence = _sentence_around(window, entity["start"], entity["end"])
                    if sentence.lower() in seen_sentences:
                        continue
                    seen_sentences.add(sentence.lower())
                    facts.append(f"[{label}: {entity['text']}] {_shorten(sentence, self.max_length)}")
        return facts[: self.max_facts]


def _sentence_around(text: str, start: int, end: int, context_words: int = 18) -> str:
    """The sentence containing a span, or a window of words around it when the
    text has no punctuation."""
    left = max(text.rfind(". ", 0, start), text.rfind("? ", 0, start), text.rfind("! ", 0, start))
    right_candidates = [position for position in (text.find(". ", end), text.find("? ", end),
                                                  text.find("! ", end)) if position != -1]
    right = min(right_candidates) if right_candidates else len(text)
    sentence = text[left + 2 if left != -1 else 0: right + 1].strip()
    if len(sentence.split()) <= 60:
        return sentence
    before = text[:start].split()[-context_words:]
    after = text[end:].split()[:context_words]
    return " ".join(before + [text[start:end]] + after)
