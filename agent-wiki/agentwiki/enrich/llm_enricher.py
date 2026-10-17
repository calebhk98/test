from __future__ import annotations

import logging

from ..llm.base import LLMUnavailable
from ..models import Enrichment, Section, VideoInfo
from ..registry import create, register
from .base import Enricher, normalize_tags
from .facts import extract_facts

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
  release status, and benchmark claims. Leave out anything the transcript does not say.
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
    """Tags, summaries and facts from an LLM, with a model-free fallback.

    The LLM is an upgrade, never a requirement: when it is unreachable or
    gives an unusable reply, the fallback enricher (default "local") does the
    work and the result is marked degraded. `run` re-enriches degraded videos
    once the LLM is reachable again.
    """

    def __init__(self, llm, fallback: Enricher, max_tags: int = 12, max_section_chars: int = 12000,
                 max_video_chars: int = 16000, skip_sponsor: bool = True):
        self.llm = llm
        self.fallback = fallback
        self.max_tags = max_tags
        self.max_section_chars = max_section_chars
        self.max_video_chars = max_video_chars
        self.skip_sponsor = skip_sponsor

    @classmethod
    def from_config(cls, params, ctx=None):
        params = dict(params)
        fb = create("enricher", params.pop("fallback", {"type": "local"}), ctx)
        return cls(llm=ctx.llm, fallback=fb, **params)

    @property
    def name(self) -> str:
        return f"llm[{self.llm.name}]"

    def _fallback(self, e: Enrichment, degraded: bool) -> Enrichment:
        e.degraded = degraded
        return e

    def _ask(self, prompt: str, max_tokens: int) -> dict | None:
        """The parsed reply, None for an unusable reply. Raises nothing."""
        if not self.llm.available:
            return None
        try:
            d = self.llm.complete_json(prompt, SYSTEM, max_tokens=max_tokens)
            return d if isinstance(d, dict) else None
        except (LLMUnavailable, OSError, ImportError, MemoryError) as e:
            # Server down, weights not downloadable, or too big for this machine:
            # all "not now", so the result is marked degraded and retried later.
            log.warning("LLM unavailable, using %s: %s", self.fallback.name, e)
            self.llm.mark_unavailable()
        except Exception as e:
            log.warning("unusable LLM reply, using %s for this part: %s", self.fallback.name, e)
        return None

    def enrich_section(self, info: VideoInfo, section: Section) -> Enrichment:
        if section.is_sponsor and self.skip_sponsor:
            return self.fallback.enrich_section(info, section)
        links = ", ".join(f"{l.label} <{l.url}>" for l in section.links) or "none"
        d = self._ask(SECTION_PROMPT.format(video_title=info.title, title=section.title, links=links,
                                            text=section.text[: self.max_section_chars],
                                            max_tags=self.max_tags), 1200)
        if d is None:
            return self._fallback(self.fallback.enrich_section(info, section),
                                  degraded=not self.llm.available)
        facts = [str(f).strip() for f in d.get("facts", []) if str(f).strip()]
        # Keep the verbatim sentences the patterns find too. Small models drop
        # or garble numbers (a 1.5B model left out "Flux 2 was a 32B model");
        # the quoted sentence is evidence an agent can check.
        facts += [f for f in extract_facts(section.text, max_facts=6) if f not in facts]
        return Enrichment(summary=str(d.get("summary", "")).strip(),
                          tags=normalize_tags(d.get("tags", []), self.max_tags),
                          facts=facts, model=self.name)

    def enrich_video(self, info, sections, transcript_text) -> Enrichment:
        summaries = [f"- {s.title}: {s.summary}" for s in sections if s.summary and not s.is_sponsor]
        if summaries:
            body_label, body = "Section summaries", "\n".join(summaries)
        else:
            body_label, body = "Transcript", transcript_text
        d = self._ask(VIDEO_PROMPT.format(title=info.title, channel=info.channel,
                                          description=info.description[:2000], body_label=body_label,
                                          body=body[: self.max_video_chars], max_tags=self.max_tags), 800)
        if d is None:
            return self._fallback(self.fallback.enrich_video(info, sections, transcript_text),
                                  degraded=not self.llm.available)
        return Enrichment(summary=str(d.get("summary", "")).strip(),
                          tags=normalize_tags(d.get("tags", []), self.max_tags), model=self.name)
