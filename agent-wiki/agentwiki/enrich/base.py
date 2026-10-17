from __future__ import annotations

import re
from abc import ABC, abstractmethod

from ..models import Enrichment, Section, VideoInfo
from ..registry import Component


class Enricher(Component, ABC):
    @abstractmethod
    def enrich_section(self, info: VideoInfo, section: Section) -> Enrichment: ...

    @abstractmethod
    def enrich_video(self, info: VideoInfo, sections: list[Section], transcript_text: str) -> Enrichment:
        """Called after every section is enriched, so section summaries can be reused."""


def normalize_tag(tag: str) -> str:
    """Obsidian tags: no spaces, no leading digits-only, kebab-case."""
    t = re.sub(r"[^\w/-]+", "-", tag.strip().lower().lstrip("#"))
    t = re.sub(r"-{2,}", "-", t).strip("-")
    if not t or t.isdigit():
        return ""
    return t


def normalize_tags(tags, limit: int = 20) -> list[str]:
    out: list[str] = []
    for t in tags:
        n = normalize_tag(str(t))
        if n and n not in out:
            out.append(n)
    return out[:limit]
