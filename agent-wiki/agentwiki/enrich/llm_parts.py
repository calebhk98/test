"""Tagger, summarizer and fact extractor backed by the configured LLM.

All three read one shared analysis per section, so using them together costs
one LLM call per section, not three. Prompts are configurable: pass
`section_prompt`, `video_prompt` or `system_prompt` to any of them (the first
one built for an LLM sets them for all three).
"""
from __future__ import annotations

import logging

from ..llm.base import LLMUnavailable
from ..models import Section, VideoInfo
from ..registry import register
from .base import FactExtractor, PartUnavailable, Summarizer, Tagger

log = logging.getLogger(__name__)

SYSTEM_PROMPT = ("You index video transcripts for a searchable wiki. Be concrete and factual. "
                 "Only state what the transcript says. Reply with JSON only.")

SECTION_PROMPT = """Video: {video_title}
Section: {section_title}
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

VIDEO_PROMPT = """Video title: {video_title}
Channel: {channel}
Description (first part):
\"\"\"{description}\"\"\"

{body_label}:
\"\"\"{body}\"\"\"

Return JSON with:
- "summary": 3-6 sentences summarising the whole video.
- "tags": 5-{max_tags} lowercase topic tags for the whole video.
"""

# Failures that mean "not now" rather than "bad reply": the server is down,
# weights cannot be downloaded, or the model does not fit in memory.
_UNAVAILABLE_ERRORS = (LLMUnavailable, OSError, ImportError, MemoryError)


class LLMAnalyzer:
    """Asks the LLM once per section and once per video, and remembers the answers."""

    def __init__(self, llm, section_prompt: str, video_prompt: str, system_prompt: str,
                 max_tags: int, max_section_characters: int, max_video_characters: int):
        self.llm = llm
        self.section_prompt = section_prompt
        self.video_prompt = video_prompt
        self.system_prompt = system_prompt
        self.max_tags = max_tags
        self.max_section_characters = max_section_characters
        self.max_video_characters = max_video_characters
        self._answers: dict[tuple, dict] = {}

    def _ask(self, cache_key: tuple, prompt: str, max_tokens: int) -> dict:
        if cache_key in self._answers:
            answer = self._answers[cache_key]
            if isinstance(answer, Exception):     # the tagger, summarizer and fact
                raise answer                      # extractor share one failed reply
            return answer
        if not self.llm.available:
            raise PartUnavailable(f"{self.llm.name} is not reachable")
        try:
            reply = self.llm.complete_json(prompt, self.system_prompt, max_tokens=max_tokens)
            if not isinstance(reply, dict):
                raise ValueError(f"LLM reply was not a JSON object: {reply!r}"[:300])
        except _UNAVAILABLE_ERRORS as error:
            self.llm.mark_unavailable()
            raise PartUnavailable(f"{self.llm.name}: {error}") from error
        except Exception as error:
            self._answers[cache_key] = error
            raise
        self._answers[cache_key] = reply
        return reply

    def analyze_section(self, video_info: VideoInfo, section: Section) -> dict:
        links = ", ".join(f"{link.label} <{link.url}>" for link in section.links) or "none"
        prompt = self.section_prompt.format(
            video_title=video_info.title, section_title=section.title, links=links,
            text=section.text[: self.max_section_characters], max_tags=self.max_tags)
        cache_key = ("section", video_info.video_id, section.index, hash(section.text))
        return self._ask(cache_key, prompt, max_tokens=1200)

    def analyze_video(self, video_info: VideoInfo, sections: list[Section], transcript_text: str) -> dict:
        summaries = [f"- {section.title}: {section.summary}" for section in sections
                     if section.summary and not section.is_sponsor]
        if summaries:
            body_label, body = "Section summaries", "\n".join(summaries)
        else:
            body_label, body = "Transcript", transcript_text
        prompt = self.video_prompt.format(
            video_title=video_info.title, channel=video_info.channel,
            description=video_info.description[:2000], body_label=body_label,
            body=body[: self.max_video_characters], max_tags=self.max_tags)
        cache_key = ("video", video_info.video_id, hash(body))
        return self._ask(cache_key, prompt, max_tokens=800)


_analyzers: dict[int, LLMAnalyzer] = {}


def _analyzer_for(llm, section_prompt=None, video_prompt=None, system_prompt=None, max_tags=12,
                  max_section_characters=12000, max_video_characters=16000) -> LLMAnalyzer:
    if id(llm) not in _analyzers:
        _analyzers[id(llm)] = LLMAnalyzer(
            llm, section_prompt or SECTION_PROMPT, video_prompt or VIDEO_PROMPT,
            system_prompt or SYSTEM_PROMPT, max_tags, max_section_characters, max_video_characters)
    return _analyzers[id(llm)]


class _LLMPart:
    def __init__(self, llm, **analyzer_settings):
        self.llm = llm
        self.analyzer = _analyzer_for(llm, **analyzer_settings)

    @classmethod
    def from_config(cls, params, app=None):
        return cls(llm=app.llm, **params)

    @property
    def name(self) -> str:
        return f"llm[{self.llm.name}]"

    def is_available(self) -> bool:
        return self.llm.available


@register("tagger", "llm")
class LLMTagger(_LLMPart, Tagger):
    def tag_section(self, video_info, section):
        return list(self.analyzer.analyze_section(video_info, section).get("tags", []))

    def tag_video(self, video_info, sections):
        transcript_text = " ".join(section.text for section in sections)
        return list(self.analyzer.analyze_video(video_info, sections, transcript_text).get("tags", []))


@register("summarizer", "llm")
class LLMSummarizer(_LLMPart, Summarizer):
    def summarize_section(self, video_info, section):
        return str(self.analyzer.analyze_section(video_info, section).get("summary", "")).strip()

    def summarize_video(self, video_info, sections, transcript_text):
        return str(self.analyzer.analyze_video(video_info, sections, transcript_text)
                   .get("summary", "")).strip()


@register("fact_extractor", "llm")
class LLMFactExtractor(_LLMPart, FactExtractor):
    def extract_facts(self, video_info, section):
        facts = self.analyzer.analyze_section(video_info, section).get("facts", [])
        return [str(fact).strip() for fact in facts if str(fact).strip()]
