from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np

from ..models import Segment, Transcript, VideoInfo
from ..registry import register
from .base import Transcriber, TranscriptionUnavailable


@register("transcriber", "faster-whisper")
class FasterWhisperTranscriber(Transcriber):
    """Local Whisper via CTranslate2. `pip install faster-whisper`."""

    def __init__(self, model: str = "large-v3-turbo", device: str = "auto",
                 compute_type: str = "default", language: str | None = None,
                 beam_size: int = 5, vad_filter: bool = True):
        self.model_name = model
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self._model = None

    @property
    def name(self) -> str:
        return f"faster-whisper:{self.model_name}"

    def _load(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as e:
                raise TranscriptionUnavailable("faster-whisper is not installed") from e
            self._model = WhisperModel(self.model_name, device=self.device,
                                       compute_type=self.compute_type)
        return self._model

    def transcribe(self, info: VideoInfo, audio_path: Path | None) -> Transcript:
        if audio_path is None:
            raise TranscriptionUnavailable("faster-whisper needs audio")
        model = self._load()
        audio = decode_with_ffmpeg(audio_path)
        segments, meta = model.transcribe(
            audio if audio is not None else str(audio_path), language=self.language,
            beam_size=self.beam_size, vad_filter=self.vad_filter)
        segs = [Segment(start=s.start, end=s.end, text=s.text.strip()) for s in segments]
        return Transcript(segments=segs, language=meta.language, model=self.name)


def decode_with_ffmpeg(path: Path, rate: int = 16000):
    """16 kHz mono float32, the input Whisper expects.

    faster-whisper decodes with PyAV by default, and PyAV releases have broken
    it (19.0 dropped an argument it passes). ffmpeg is already required by
    yt-dlp, so use it when present and fall back to PyAV when not.
    """
    if not shutil.which("ffmpeg"):
        return None
    out = subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path), "-f", "s16le",
         "-ac", "1", "-ar", str(rate), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768.0
