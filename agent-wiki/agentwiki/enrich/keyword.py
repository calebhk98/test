"""Model-free enrichment: frequent words as tags, opening sentences as summary.

Crude, but it means the pipeline produces a usable wiki with no LLM at all.
"""
from __future__ import annotations

import re
from collections import Counter

from ..models import Enrichment, Section, VideoInfo
from ..registry import register
from .base import Enricher, normalize_tags
from .facts import extract_facts

_STOP = set("""a about above after again against all also am an and any are as at be because been
before being below between both but by can could did do does doing down during each few for from
further had has have having he her here hers him his how i if in into is it its itself just like
me more most my no nor not now of off on once only or other our out over own really right same
says she should so some such than that the their them then there these they this those through
to too under until up very was way we were what when where which while who whom why will with
would you your yours gonna wanna yeah okay ok um uh let lets thing things going get got go see
one two three new also basically actually here's it's that's there's you're we're they're i'm
don't can't isn't won't just video videos look looks pretty much even still know make makes
want well super quite every given instead kind maybe lot bit stuff something anything
everything someone people person able around always another back being better big called
come comes coming different done enough far first give good great guess huh hey human idea
important interesting last little long lot made many mean means mm need needs never next
nice part probably put rather said say saying sense show since sort start sure take talk
talking tell thank thanks think thinking thought time today together try trying turn use
used uses using whether work working works world yes yet year years""".split()) - {"world"}


def _sentences(text: str, n: int) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = " ".join(parts[:n]).strip()
    return out if len(out) < 600 else out[:597] + "..."


@register("enricher", "keyword")
class KeywordEnricher(Enricher):
    def __init__(self, max_tags: int = 10):
        self.max_tags = max_tags

    def _tags(self, *texts: str) -> list[str]:
        words = re.findall(r"[a-z][a-z0-9-]{2,}", " ".join(texts).lower())
        counts = Counter(w for w in words if w not in _STOP)
        return normalize_tags([w for w, _ in counts.most_common(self.max_tags)], self.max_tags)

    def enrich_section(self, info: VideoInfo, section: Section) -> Enrichment:
        title_tags = normalize_tags([section.title])
        tags = title_tags + [t for t in self._tags(section.title, section.text) if t not in title_tags]
        if section.is_sponsor:
            tags = ["sponsor"] + tags
        return Enrichment(summary=_sentences(section.text, 2), tags=tags[: self.max_tags],
                          facts=extract_facts(section.text), model=self.name)

    def enrich_video(self, info, sections, transcript_text) -> Enrichment:
        tags = normalize_tags(info.source_tags) + self._tags(info.title, transcript_text)
        return Enrichment(summary=_sentences(info.description, 2) or _sentences(transcript_text, 3),
                          tags=normalize_tags(tags, self.max_tags), model=self.name)
