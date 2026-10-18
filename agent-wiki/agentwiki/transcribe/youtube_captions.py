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
    def from_config(cls, params, app=None):
        transcriber = cls(**params)
        transcriber.source = getattr(app, "source", None)
        return transcriber

    def _pick(self, video_info: VideoInfo) -> tuple[str, str] | None:
        pools = [video_info.raw.get("subtitles") or {}, video_info.raw.get("automatic_captions") or {}]
        if not self.prefer_manual:
            pools.reverse()
        for pool in pools:
            for language in self.languages:
                for caption_format in pool.get(language) or []:
                    if caption_format.get("ext") == "json3" and caption_format.get("url"):
                        return language, caption_format["url"]
        return None

    def transcribe(self, video_info: VideoInfo, audio_path: Path | None) -> Transcript:
        picked = self._pick(video_info)
        if not picked:
            raise TranscriptionUnavailable("no captions in a configured language")
        if self.source is None:
            raise TranscriptionUnavailable("no source to fetch captions with")
        language, url = picked
        segments = parse_json3(json.loads(self.source.fetch_text(url)))
        if not segments:
            raise TranscriptionUnavailable("captions were empty")
        return Transcript(segments=segments, language=language, model=self.name)


def parse_json3(data: dict) -> list[Segment]:
    segments = []
    for event in data.get("events", []):
        text = "".join(segment.get("utf8", "")
                       for segment in event.get("segs") or []).replace("\n", " ").strip()
        if not text:
            continue
        start = event.get("tStartMs", 0) / 1000
        segments.append(Segment(start=start, end=start + event.get("dDurationMs", 0) / 1000, text=text))
    return segments
