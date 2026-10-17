"""Fakes for the network-bound components, so tests run offline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentwiki.app import App
from agentwiki.config import Config
from agentwiki.models import Segment, Transcript, VideoInfo
from agentwiki.registry import register
from agentwiki.sources.base import ChannelEntry, ChannelRef, VideoSource
from agentwiki.sources.youtube import YtDlpSource
from agentwiki.transcribe.base import Transcriber

FIXTURES = Path(__file__).parent / "fixtures"
REAL_ID = "lHmZoRHMZyM"

# Lines spoken in some chapters of the fixture video, invented for the tests.
SPOKEN = {
    "Flux 3": "Flux 3 is a new open weights image model from Black Forest Labs with 12 billion "
              "parameters. It needs about 24 gigabytes of VRAM. It is uncensored.",
    "Inspatio World 1.5": "Inspatio World is a text to world model that generates a consistent "
                          "3D world you can walk around in real time.",
    "Elevenlabs V4": "ElevenLabs V4 is a text to speech model with better emotion. It is closed "
                     "source and only available through their API.",
    "Luma": "This video is sponsored by Luma. Try Luma today, it makes videos.",
}


@register("source", "fake")
class FakeSource(VideoSource):
    """Serves the saved metadata of a real AI Search video, plus synthetic ones."""

    def __init__(self):
        self.downloads: list[str] = []
        self.channel_videos = [REAL_ID, "aaaaaaaaaaa", "bbbbbbbbbbb"]

    def parse_video_id(self, s):
        return YtDlpSource().parse_video_id(s)

    def resolve_channel(self, url):
        return ChannelRef("UCIgnGlGkVRhd4qNFcEwLL4A", "AI Search", "https://www.youtube.com/@theAIsearch")

    def list_channel(self, url, limit=None):
        out = [ChannelEntry(v, f"video {v}", 600.0) for v in self.channel_videos]
        out.append(ChannelEntry("shortshort1", "a short", 30.0))
        return out[:limit] if limit else out

    def fetch_info(self, vid):
        if vid == REAL_ID:
            return VideoInfo.from_ytdlp(json.loads((FIXTURES / f"{REAL_ID}.info.json").read_text()))
        if vid == "shortshort1":
            return VideoInfo(video_id=vid, title="short", url="u", duration=30)
        return VideoInfo(video_id=vid, title=f"Video {vid} about robots", url=f"https://youtu.be/{vid}",
                         channel="AI Search", published="2026-09-01", duration=600,
                         description="Robots and humanoid news.")

    def download_audio(self, vid, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / f"{vid}.webm"
        p.write_bytes(b"fake audio")
        self.downloads.append(vid)
        return p


@register("transcriber", "fake")
class FakeTranscriber(Transcriber):
    def __init__(self):
        self.seen_audio: list[Path] = []

    def transcribe(self, info, audio_path):
        assert audio_path is not None and audio_path.exists()
        self.seen_audio.append(audio_path)
        segs = []
        if info.chapters:
            for c in info.chapters:
                text = SPOKEN.get(c.title, f"This part covers {c.title}. It is interesting news.")
                segs.append(Segment(c.start, c.start + 5, text))
        else:
            for i in range(0, int(info.duration), 30):
                segs.append(Segment(i, i + 30, f"Humanoid robots segment {i}. Robots walk."))
        return Transcript(segs, "en", "fake")


@pytest.fixture
def app(tmp_path) -> App:
    cfg = Config.load(tmp_path)
    cfg.data["source"] = {"type": "fake"}
    cfg.data["transcriber"] = {"type": "fake"}
    cfg.data["embedder"] = {"type": "hashing", "dim": 256}
    cfg.data["ingest"]["sleep_between"] = 0
    a = App(cfg)
    a.init()
    return a
