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

    def parse_video_id(self, url_or_id):
        return YtDlpSource().parse_video_id(url_or_id)

    def resolve_channel(self, url):
        return ChannelRef("UCIgnGlGkVRhd4qNFcEwLL4A", "AI Search", "https://www.youtube.com/@theAIsearch")

    def list_channel(self, url, limit=None):
        out = [ChannelEntry(video_id, f"video {video_id}", 600.0) for video_id in self.channel_videos]
        out.append(ChannelEntry("shortshort1", "a short", 30.0))
        return out[:limit] if limit else out

    def fetch_info(self, video_id):
        if video_id == REAL_ID:
            return VideoInfo.from_ytdlp(json.loads((FIXTURES / f"{REAL_ID}.info.json").read_text()))
        if video_id == "shortshort1":
            return VideoInfo(video_id=video_id, title="short", url="u", duration=30)
        return VideoInfo(video_id=video_id, title=f"Video {video_id} about robots",
                         url=f"https://youtu.be/{video_id}",
                         channel="AI Search", published="2026-09-01", duration=600,
                         description="Robots and humanoid news.")

    def download_audio(self, video_id, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        audio_file = out_dir / f"{video_id}.webm"
        audio_file.write_bytes(b"fake audio")
        self.downloads.append(video_id)
        return audio_file


@register("transcriber", "fake")
class FakeTranscriber(Transcriber):
    def __init__(self):
        self.seen_audio: list[Path] = []

    def transcribe(self, video_info, audio_path):
        assert audio_path is not None and audio_path.exists()
        self.seen_audio.append(audio_path)
        segments = []
        if video_info.chapters:
            for chapter in video_info.chapters:
                text = SPOKEN.get(chapter.title, f"This part covers {chapter.title}. It is interesting news.")
                segments.append(Segment(chapter.start, chapter.start + 5, text))
        else:
            for second in range(0, int(video_info.duration), 30):
                segments.append(Segment(second, second + 30,
                                        f"Humanoid robots segment {second}. Robots walk."))
        return Transcript(segments, "en", "fake")


@pytest.fixture
def app(tmp_path) -> App:
    config = Config.load(tmp_path)
    config.data["source"] = {"type": "fake"}
    config.data["transcriber"] = {"type": "fake"}
    config.data["embedder"] = {"type": "hashing", "dimensions": 256}
    config.data["ingest"]["sleep_between"] = 0
    wiki_app = App(config)
    wiki_app.init()
    return wiki_app
