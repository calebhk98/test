from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import Transcript, VideoInfo
from ..registry import Component


class TranscriptionUnavailable(RuntimeError):
    """This transcriber cannot handle this video; a fallback may."""


class Transcriber(Component, ABC):
    #: When False the pipeline skips the audio download entirely.
    needs_audio: bool = True

    @abstractmethod
    def transcribe(self, info: VideoInfo, audio_path: Path | None) -> Transcript: ...
