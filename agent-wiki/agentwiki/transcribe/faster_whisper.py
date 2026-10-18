from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

import numpy as np

from .. import hardware
from ..models import Segment, Transcript, VideoInfo
from ..registry import register
from .base import Transcriber, TranscriptionUnavailable

log = logging.getLogger(__name__)

# (min VRAM GB, min RAM GB, model). large-v3-turbo is near large-v3 accuracy at
# a fraction of the cost, so it is the top tier even on an 80 GB card.
AUTO_TIERS = [
    (4, 0, "large-v3-turbo"),
    (2, 0, "small"),
    (0, 12, "small"),      # CPU, desktop or laptop
    (0, 4, "base"),        # CPU, small machine
    (0, 0, "tiny"),        # phones, Raspberry Pi
]


@register("transcriber", "faster-whisper")
class FasterWhisperTranscriber(Transcriber):
    """Local Whisper via CTranslate2. `pip install faster-whisper`.

    Every hardware choice defaults to "auto": the model size from the tiers
    above, the device from CUDA availability, the precision from what that
    device supports. Apple GPUs are not supported by CTranslate2, so Macs run
    on CPU here (still fast on Apple Silicon).
    """

    def __init__(self, model: str = "auto", device: str = "auto",
                 compute_type: str = "auto", language: str | None = None,
                 beam_size: int = 5, vad_filter: bool = True, batch_size: int | str = "auto"):
        self.model_name = hardware.pick(AUTO_TIERS) if model == "auto" else model
        hardware_info = hardware.detect()
        self.device = ("cuda" if hardware_info.device == "cuda" else "cpu") if device == "auto" else device
        self.compute_type = compute_type     # CTranslate2 resolves "auto" per device
        self.language = language
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        # Batched decoding is much faster on a GPU and slower on a CPU.
        self.batch_size = (16 if self.device == "cuda" else 1) if batch_size == "auto" else int(batch_size)
        self._model = None

    @property
    def name(self) -> str:
        return f"faster-whisper:{self.model_name}"

    def _load(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as error:
                raise TranscriptionUnavailable("faster-whisper is not installed") from error
            log.info("loading whisper %s on %s (%s)", self.model_name, self.device, self.compute_type)
            model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
            if self.batch_size > 1:
                from faster_whisper import BatchedInferencePipeline
                model = BatchedInferencePipeline(model=model)
            self._model = model
        return self._model

    def transcribe(self, video_info: VideoInfo, audio_path: Path | None) -> Transcript:
        if audio_path is None:
            raise TranscriptionUnavailable("faster-whisper needs audio")
        model = self._load()
        audio = decode_with_ffmpeg(audio_path)
        options = {"language": self.language, "beam_size": self.beam_size, "vad_filter": self.vad_filter}
        if self.batch_size > 1:
            options["batch_size"] = self.batch_size
        segments, transcription_info = model.transcribe(
            audio if audio is not None else str(audio_path), **options)
        transcript_segments = [Segment(start=segment.start, end=segment.end, text=segment.text.strip())
                               for segment in segments]
        return Transcript(segments=transcript_segments, language=transcription_info.language, model=self.name)


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
