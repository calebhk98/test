"""Use audio files you already have, with metadata from another source.

For when downloads from a site are blocked, or you fetched the audio some
other way (a converter website, a podcast app). Name each file after the
video id, e.g. `lHmZoRHMZyM.mp3`, and put it in `folder`:

    [source]
    type = "local-audio"
    folder = "~/agent-wiki-audio"
    source = { type = "yt-dlp" }      # titles, chapters, descriptions come from here
    download_missing = true           # videos with no file are downloaded as usual
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from ..registry import create, register
from .base import VideoSource

log = logging.getLogger(__name__)

AUDIO_EXTENSIONS = (".mp3", ".m4a", ".webm", ".opus", ".ogg", ".wav", ".flac", ".aac", ".mp4", ".mkv")


@register("source", "local-audio")
class LocalAudioSource(VideoSource):
    def __init__(self, inner_source: VideoSource, folder: str, download_missing: bool = True,
                 delete_after_use: bool = False):
        self.inner_source = inner_source
        self.folder = Path(folder).expanduser()
        self.download_missing = download_missing
        self.delete_after_use = delete_after_use

    @classmethod
    def from_config(cls, params, app=None):
        params = dict(params)
        inner_spec = params.pop("source", {"type": "yt-dlp"})
        return cls(inner_source=create("source", inner_spec, app), **params)

    @property
    def name(self) -> str:
        return f"local-audio[{self.inner_source.name}]"

    def local_file(self, video_id: str) -> Path | None:
        for extension in AUDIO_EXTENSIONS:
            candidate = self.folder / f"{video_id}{extension}"
            if candidate.is_file():
                return candidate
        return None

    def download_audio(self, video_id: str, out_dir: Path) -> Path:
        local_file = self.local_file(video_id)
        if local_file is None:
            if not self.download_missing:
                raise FileNotFoundError(f"no audio file for {video_id} in {self.folder}")
            return self.inner_source.download_audio(video_id, out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        working_copy = out_dir / local_file.name
        # The pipeline deletes its working copy after transcribing; the
        # original stays unless delete_after_use is set.
        if self.delete_after_use:
            shutil.move(str(local_file), working_copy)
        else:
            shutil.copy2(local_file, working_copy)
        log.info("using local audio %s", local_file)
        return working_copy

    # Everything else comes from the wrapped source.
    def parse_video_id(self, url_or_id):
        return self.inner_source.parse_video_id(url_or_id)

    def resolve_channel(self, url):
        return self.inner_source.resolve_channel(url)

    def list_channel(self, channel_url, limit=None):
        return self.inner_source.list_channel(channel_url, limit)

    def fetch_info(self, video_id):
        return self.inner_source.fetch_info(video_id)

    def fetch_text(self, url):
        return self.inner_source.fetch_text(url)
