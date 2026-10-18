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
        self.needs_audio = any(transcriber.needs_audio for transcriber in transcribers)

    @classmethod
    def from_config(cls, params, app=None):
        return cls([create("transcriber", transcriber_spec, app)
                    for transcriber_spec in params["transcribers"]])

    @property
    def name(self) -> str:
        return "chain(" + ",".join(transcriber.name for transcriber in self.transcribers) + ")"

    def transcribe(self, video_info: VideoInfo, audio_path: Path | None) -> Transcript:
        errors = []
        for transcriber in self.transcribers:
            try:
                return transcriber.transcribe(video_info, audio_path)
            except TranscriptionUnavailable as error:
                errors.append(f"{transcriber.name}: {error}")
        raise TranscriptionUnavailable("; ".join(errors))
