"""Split on the creator's chapters and attach the links from the description.

Many AI news channels list one link per topic in the description
("Flux 3 https://bfl.ai/...") and one chapter per topic ("17:34 Flux 3").
Matching them gives each section page its primary source.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from ..models import Link, Section, Transcript, VideoInfo
from ..registry import register
from .base import Segmenter, fill_text

_URL_RE = re.compile(r"https?://\S+")
_SPONSOR_RE = re.compile(
    r"(?i:thanks to (?:our|my|today's) sponsor|sponsored by)\s+"
    r"([A-Z][\w&-]*(?: [A-Z][\w&-]*)?)")
_TIMESTAMP_LINE = re.compile(r"^\s*\(?\d{1,2}:\d{2}(?::\d{2})?\)?\s")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def description_links(description: str) -> list[Link]:
    """Lines shaped like 'Label https://url'. A bare URL line continues the label above."""
    links: list[Link] = []
    last_label = ""
    for line in description.splitlines():
        line = line.strip()
        if not line or _TIMESTAMP_LINE.match(line):
            last_label = ""
            continue
        urls = _URL_RE.findall(line)
        if not urls:
            last_label = ""
            continue
        label = _URL_RE.sub("", line).strip(" :-|")
        if not label and last_label:
            label = last_label
        if not label or len(label) > 80:
            continue
        for u in urls:
            links.append(Link(label=label, url=u.rstrip(").,")))
        last_label = label
    return links


def sponsor_names(description: str) -> list[str]:
    return [m.group(1).strip() for m in _SPONSOR_RE.finditer(description)]


def _match_tier(title: str, label: str, threshold: float) -> int:
    """3 exact, 2 one name's words contain the other's, 1 fuzzy, 0 no match."""
    if title == label or title.replace(" ", "") == label.replace(" ", ""):
        return 3
    tw, lw = set(title.split()), set(label.split())
    if lw <= tw or tw <= lw:
        return 2
    if SequenceMatcher(None, title, label).ratio() >= threshold:
        return 1
    return 0


def match_links(title: str, links: list[Link], threshold: float = 0.85) -> list[Link]:
    """Links whose label best matches the chapter title. Only the best tier is
    kept, so 'PDMD' does not also pick up 'DMAD' by spelling similarity."""
    t = _norm(title)
    if not t:
        return []
    scored = [(_match_tier(t, _norm(l.label), threshold), l) for l in links if _norm(l.label)]
    best = max((s for s, _ in scored), default=0)
    return [l for s, l in scored if s == best] if best else []


@register("segmenter", "chapters")
class ChapterSegmenter(Segmenter):
    def __init__(self, min_chapters: int = 2, drop_empty: bool = True):
        self.min_chapters = min_chapters
        self.drop_empty = drop_empty

    def split(self, info: VideoInfo, transcript: Transcript) -> list[Section]:
        chapters = sorted(info.chapters, key=lambda c: c.start)
        if len(chapters) < self.min_chapters:
            return []
        links = description_links(info.description)
        sponsors = [_norm(s) for s in sponsor_names(info.description)]
        end_of_video = info.duration or (transcript.segments[-1].end if transcript.segments else 0)
        sections = []
        for i, c in enumerate(chapters):
            end = chapters[i + 1].start if i + 1 < len(chapters) else (c.end or end_of_video)
            title = c.title or f"Part {i + 1}"
            is_sponsor = any(s and (_norm(title) == s or s in _norm(title).split()) for s in sponsors)
            sections.append(Section(index=i + 1, title=title, start=c.start, end=end,
                                    links=match_links(title, links), is_sponsor=is_sponsor))
        fill_text(sections, transcript)
        if self.drop_empty:
            sections = [s for s in sections if s.text]
            for i, s in enumerate(sections, 1):
                s.index = i
        return sections
