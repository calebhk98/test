from __future__ import annotations

import logging

from ..llm.base import LLMUnavailable
from ..models import Enrichment, Section, VideoInfo
from ..registry import register
from .base import Enricher, normalize_tags
from .keyword import KeywordEnricher

log = logging.getLogger(__name__)

SYSTEM = ("You index video transcripts for a searchable wiki. Be concrete and factual. "
          "Only state what the transcript says. Reply with JSON only.")

SECTION_PROMPT = """Video: {video_title}
Section: {title}
Links given for this section: {links}

Transcript of this section (auto-generated, may misspell names):
\"\"\"{text}\"\"\"

Return JSON with:
- "summary": 2-4 sentences on what this section covers.
- "tags": 3-{max_tags} short topic tags, lowercase, e.g. "text-to-video", "open-source",
  "image-editing", plus the names of the main tools or models, e.g. "flux-3".
- "facts": a list of short factual statements a reader might search for. Include
  every one the transcript states: the name of each model or tool, what it does,
  model size (parameters), VRAM or hardware needs, speed, licence, whether weights
  are open or closed, whether it is censored or has content restrictions, price,
  release status, and benchmark claims. Use "unknown" for nothing; just omit it.
"""

VIDEO_PROMPT = """Video title: {title}
Channel: {channel}
Description (first part):
\"\"\"{description}\"\"\"

{body_label}:
\"\"\"{body}\"\"\"

Return JSON with:
- "summary": 3-6 sentences summarising the whole video.
- "tags": 5-{max_tags} lowercase topic tags for the whole video.
"""


@register("enricher", "llm")
class LLMEnricher(Enricher):
    def __init__(self, llm, max_tags: int = 12, max_section_chars: int = 12000,
                 max_video_chars: int = 16000, skip_sponsor: bool = True):
        self.llm = llm
        self.max_tags = max_tags
        self.max_section_chars = max_section_chars
        self.max_video_chars = max_video_chars
        self.skip_sponsor = skip_sponsor
        self.fallback = KeywordEnricher(max_tags=max_tags)

    @classmethod
    def from_config(cls, params, ctx=None):
        return cls(llm=ctx.llm, **params)

    @property
    def name(self) -> str:
        return f"llm[{self.llm.name}]"

    def enrich_section(self, info: VideoInfo, section: Section) -> Enrichment:
        if section.is_sponsor and self.skip_sponsor:
            e = self.fallback.enrich_section(info, section)
            e.tags = normalize_tags(["sponsor"] + e.tags, self.max_tags)
            return e
        links = ", ".join(f"{l.label} <{l.url}>" for l in section.links) or "none"
        prompt = SECTION_PROMPT.format(video_title=info.title, title=section.title, links=links,
                                       text=section.text[: self.max_section_chars],
                                       max_tags=self.max_tags)
        try:
            d = self.llm.complete_json(prompt, SYSTEM, max_tokens=1200)
        except LLMUnavailable:
            raise           # fail the video so `run` retries it once the server is up
        except Exception as e:  # a bad reply should not stop the whole video
            log.warning("LLM enrichment failed for %s §%s: %s", info.video_id, section.index, e)
            return self.fallback.enrich_section(info, section)
        return Enrichment(summary=str(d.get("summary", "")).strip(),
                          tags=normalize_tags(d.get("tags", []), self.max_tags),
                          facts=[str(f).strip() for f in d.get("facts", []) if str(f).strip()],
                          model=self.name)

    def enrich_video(self, info, sections, transcript_text) -> Enrichment:
        summaries = [f"- {s.title}: {s.summary}" for s in sections if s.summary and not s.is_sponsor]
        if summaries:
            body_label, body = "Section summaries", "\n".join(summaries)
        else:
            body_label, body = "Transcript", transcript_text
        prompt = VIDEO_PROMPT.format(title=info.title, channel=info.channel,
                                     description=info.description[:2000], body_label=body_label,
                                     body=body[: self.max_video_chars], max_tags=self.max_tags)
        try:
            d = self.llm.complete_json(prompt, SYSTEM, max_tokens=800)
        except LLMUnavailable:
            raise
        except Exception as e:
            log.warning("LLM video enrichment failed for %s: %s", info.video_id, e)
            return self.fallback.enrich_video(info, sections, transcript_text)
        return Enrichment(summary=str(d.get("summary", "")).strip(),
                          tags=normalize_tags(d.get("tags", []), self.max_tags), model=self.name)
