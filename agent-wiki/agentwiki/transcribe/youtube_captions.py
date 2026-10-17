from __future__ import annotations

import json
from pathlib import Path

from ..models import Segment, Transcript, VideoInfo
from ..registry import register
from .base import Transcriber, TranscriptionUnavailable


@register("transcriber", "youtube-captions")
class YouTubeCaptionsTranscriber(Transcriber):
    """Use the captions YouTube already has. No audio download, no GPU.

    Auto-captions have no punctuation and garble product names more than
    Whisper does, so this is best as a fallback or for fast bulk backfills.
    """

    needs_audio = False

    def __init__(self, languages: list[str] | None = None, prefer_manual: bool = True):
        self.languages = languages or ["en", "en-US", "en-GB", "en-orig"]
        self.prefer_manual = prefer_manual
        self.source = None          # set by from_config

    @classmethod
    def from_config(cls, params, ctx=None):
        obj = cls(**params)
        obj.source = getattr(ctx, "source", None)
        return obj

    def _pick(self, info: VideoInfo) -> tuple[str, str] | None:
        pools = [info.raw.get("subtitles") or {}, info.raw.get("automatic_captions") or {}]
        if not self.prefer_manual:
            pools.reverse()
        for pool in pools:
            for lang in self.languages:
                for fmt in pool.get(lang) or []:
                    if fmt.get("ext") == "json3" and fmt.get("url"):
                        return lang, fmt["url"]
        return None

    def transcribe(self, info: VideoInfo, audio_path: Path | None) -> Transcript:
        picked = self._pick(info)
        if not picked:
            raise TranscriptionUnavailable("no captions in a configured language")
        if self.source is None:
            raise TranscriptionUnavailable("no source to fetch captions with")
        lang, url = picked
        segs = parse_json3(json.loads(self.source.fetch_text(url)))
        if not segs:
            raise TranscriptionUnavailable("captions were empty")
        return Transcript(segments=segs, language=lang, model=self.name)


def parse_json3(data: dict) -> list[Segment]:
    segs = []
    for ev in data.get("events", []):
        text = "".join(s.get("utf8", "") for s in ev.get("segs") or []).replace("\n", " ").strip()
        if not text:
            continue
        start = ev.get("tStartMs", 0) / 1000
        segs.append(Segment(start=start, end=start + ev.get("dDurationMs", 0) / 1000, text=text))
    return segs
