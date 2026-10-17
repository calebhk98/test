from __future__ import annotations

from pathlib import Path

from ..models import Transcript, VideoInfo
from ..registry import create, register
from .base import Transcriber, TranscriptionUnavailable


@register("transcriber", "chain")
class ChainTranscriber(Transcriber):
    """Try each transcriber in order until one succeeds."""

    def __init__(self, transcribers: list[Transcriber]):
        self.transcribers = transcribers
        self.needs_audio = any(t.needs_audio for t in transcribers)

    @classmethod
    def from_config(cls, params, ctx=None):
        return cls([create("transcriber", s, ctx) for s in params["transcribers"]])

    @property
    def name(self) -> str:
        return "chain(" + ",".join(t.name for t in self.transcribers) + ")"

    def transcribe(self, info: VideoInfo, audio_path: Path | None) -> Transcript:
        errors = []
        for t in self.transcribers:
            try:
                return t.transcribe(info, audio_path)
            except TranscriptionUnavailable as e:
                errors.append(f"{t.name}: {e}")
        raise TranscriptionUnavailable("; ".join(errors))
