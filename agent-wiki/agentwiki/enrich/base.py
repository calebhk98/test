"""Enrichment: tags, summaries and facts for each section and video.

An Enricher produces all three. The usual one, CompositeEnricher, does not do
the work itself: it holds three swappable kinds of part, each chosen in
config, each with optional fallbacks:

    Tagger          section -> tags          ("tagger" in the registry)
    Summarizer      section -> summary       ("summarizer")
    FactExtractor   section -> fact lines    ("fact_extractor")

So LLM summaries, entity tags from a dedicated model and pattern-matched
facts can be mixed freely, and any one of them replaced by a new class.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import Counter

from ..models import Enrichment, Section, VideoInfo
from ..registry import Component


class Enricher(Component, ABC):
    @abstractmethod
    def enrich_section(self, video_info: VideoInfo, section: Section) -> Enrichment: ...

    @abstractmethod
    def enrich_video(self, video_info: VideoInfo, sections: list[Section],
                     transcript_text: str) -> Enrichment:
        """Called after every section is enriched, so section results can be reused."""

    def upgrade_available(self) -> bool:
        """True when a part that was unavailable earlier (and was replaced by a
        fallback) could run now. `run` then redoes degraded videos."""
        return False


class PartUnavailable(RuntimeError):
    """A part cannot run right now (server down, model not downloadable, missing
    package). Its fallbacks run instead and the result is marked degraded."""


class EnrichmentPart(Component):
    def is_available(self) -> bool:
        return True


class Tagger(EnrichmentPart, ABC):
    @abstractmethod
    def tag_section(self, video_info: VideoInfo, section: Section) -> list[str]: ...

    def tag_video(self, video_info: VideoInfo, sections: list[Section]) -> list[str]:
        """Default: the tags most sections share, after the creator's own tags."""
        counts = Counter(tag for section in sections if not section.is_sponsor for tag in section.tags)
        return list(video_info.source_tags) + [tag for tag, _ in counts.most_common(12)]


class Summarizer(EnrichmentPart, ABC):
    @abstractmethod
    def summarize_section(self, video_info: VideoInfo, section: Section) -> str: ...

    def summarize_video(self, video_info: VideoInfo, sections: list[Section],
                        transcript_text: str) -> str:
        """Default: the description's first line and the list of topics."""
        first_line = video_info.description.strip().split("\n")[0][:300] if video_info.description else ""
        topics = [section.title for section in sections if not section.is_sponsor]
        topic_sentence = f"Covers {len(topics)} topics: {', '.join(topics)}." if topics else ""
        return " ".join(part for part in (first_line, topic_sentence) if part)


class FactExtractor(EnrichmentPart, ABC):
    @abstractmethod
    def extract_facts(self, video_info: VideoInfo, section: Section) -> list[str]: ...


def normalize_tag(tag: str) -> str:
    """Obsidian tags: lowercase kebab-case, no spaces, not only digits."""
    normalized = re.sub(r"[^\w/-]+", "-", tag.strip().lower().lstrip("#"))
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized or normalized.isdigit():
        return ""
    return normalized


def normalize_tags(tags, limit: int = 20) -> list[str]:
    unique_tags: list[str] = []
    for tag in tags:
        normalized = normalize_tag(str(tag))
        if normalized and normalized not in unique_tags:
            unique_tags.append(normalized)
    return unique_tags[:limit]
