"""Pull searchable facts out of a transcript with patterns, no model needed.

Each fact is the sentence that states it, labelled with what kind of fact it
is, so "is it censored" or "how many parameters" finds the sentence that says.
"""
from __future__ import annotations

import re

_NUM = r"\d+(?:[.,]\d+)?"
PATTERNS: dict[str, re.Pattern] = {
    "size": re.compile(
        rf"\b{_NUM}\s*(?:billion|million|trillion)\s+(?:active\s+)?param|"
        rf"\b{_NUM}\s?[BMT]\b(?!-?\w)|\bparameters?\b|\bmixture of experts\b|\bMoE\b", re.I),
    "hardware": re.compile(
        rf"\b{_NUM}\s*(?:gb|gigs?|gigabytes?)\b|\bv?ram\b|\bconsumer (?:gpu|graphics card)s?\b|"
        r"\b(?:rtx|gtx)\s?\d{3,4}\b|\b(?:h100|a100|b200|4090|5090|3090)\b|\bquantiz", re.I),
    "license": re.compile(
        r"\bopen[- ]?(?:source|sourced|weights?)\b|\bclosed[- ]?(?:source|weights?)\b|\bproprietary\b|"
        r"\bapache\b|\bmit licen[cs]e\b|\bnon[- ]?commercial\b|\bhugging ?face\b|\bgithub\b|"
        r"\bweights\b|\bapi only\b|\bonly (?:available )?(?:via|through|on) (?:their|the|an) api\b", re.I),
    "censorship": re.compile(
        r"\buncensored\b|\bcensor(?:ed|ship|s)?\b|\bnsfw\b|\bnot safe for work\b|\bnudity\b|"
        r"\bcontent (?:filter|moderation|restrictions?|policy)\b|\bguardrails?\b|\bsafety filter\b|"
        r"\brefuses?\b|\bspicy\b", re.I),
    "speed": re.compile(
        rf"\breal[- ]?time\b|\b{_NUM}\s*(?:fps|frames per second|tokens? per second|it/s)\b|"
        rf"\b{_NUM}\s*(?:x|times) faster\b|\bin (?:just|under|about)?\s*{_NUM}\s*seconds\b|"
        r"\blatency\b|\bfastest\b", re.I),
    "output": re.compile(
        rf"\b\d{{3,4}}p\b|\b[48]k\b|\b{_NUM}\s*(?:seconds?|minutes?) (?:long|of (?:video|audio|footage))\b|"
        rf"\bup to {_NUM}\s*(?:seconds?|minutes?)\b|\bresolution\b", re.I),
    "price": re.compile(rf"\$\s?{_NUM}|\bfree to use\b|\bfor free\b|\bpricing\b|\bper month\b|"
                        r"\bsubscription\b|\bpaid\b", re.I),
    "benchmark": re.compile(r"\bbenchmarks?\b|\boutperform|\bbeats\b|\bstate of the art\b|\bsota\b|"
                            r"\bleaderboard\b|\belo\b|\bscores?\b", re.I),
}


def sentences(text: str, window_words: int = 28) -> list[str]:
    """Sentences, or fixed word windows when the text has no punctuation (auto-captions)."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    words = len(text.split())
    if len(parts) * 60 < words:      # fewer than one sentence end per 60 words: captions
        w = text.split()
        parts = [" ".join(w[i:i + window_words]) for i in range(0, len(w), window_words)]
    return parts


def extract_facts(text: str, max_facts: int = 12, max_len: int = 260) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for s in sentences(text):
        kinds = [k for k, p in PATTERNS.items() if p.search(s)]
        if not kinds:
            continue
        s = s if len(s) <= max_len else s[: max_len - 3] + "..."
        if s.lower() in seen:
            continue
        seen.add(s.lower())
        out.append(f"[{', '.join(kinds)}] {s}")
        if len(out) >= max_facts:
            break
    return out
