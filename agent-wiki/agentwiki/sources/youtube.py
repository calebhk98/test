"""YouTube through yt-dlp, used as a library."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..models import VideoInfo
from ..registry import register
from .base import ChannelEntry, ChannelRef, VideoSource

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_URL_ID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/live/|/embed/)([A-Za-z0-9_-]{11})")


@register("source", "yt-dlp")
class YtDlpSource(VideoSource):
    def __init__(self, cookies_file: str = "", cookies_from_browser: str = "",
                 js_runtimes: list[str] | None = None, audio_format: str = "bestaudio/best",
                 player_clients: list[str] | None = None,
                 extra_options: dict[str, Any] | None = None):
        self.cookies_file = cookies_file
        self.cookies_from_browser = cookies_from_browser
        self.js_runtimes = js_runtimes
        self.audio_format = audio_format
        # Which YouTube app yt-dlp pretends to be. When one is blocked ("confirm
        # you're not a bot") another often is not; see config.example.toml.
        self.player_clients = player_clients
        self.extra_options = extra_options or {}

    def _opts(self, **over) -> dict:
        ydl_options: dict[str, Any] = {"quiet": True, "no_warnings": True, "noprogress": True}
        if self.cookies_file:
            ydl_options["cookiefile"] = self.cookies_file
        if self.cookies_from_browser:
            ydl_options["cookiesfrombrowser"] = (self.cookies_from_browser,)
        if self.js_runtimes:
            ydl_options["js_runtimes"] = {runtime: {} for runtime in self.js_runtimes}
        if self.player_clients:
            ydl_options["extractor_args"] = {"youtube": {"player_client": list(self.player_clients)}}
        ydl_options.update(self.extra_options)
        ydl_options.update(over)
        return ydl_options

    def _ydl(self, **overrides):
        import yt_dlp
        return yt_dlp.YoutubeDL(self._opts(**overrides))

    def parse_video_id(self, url_or_id: str) -> str | None:
        text = url_or_id.strip()
        if _ID_RE.match(text):
            return text
        match = _URL_ID_RE.search(text)
        return match.group(1) if match else None

    @staticmethod
    def _uploads_url(url: str) -> str:
        url = url.strip().rstrip("/")
        if url.startswith("@"):
            url = f"https://www.youtube.com/{url}"
        if re.search(r"/(videos|streams|shorts|playlists|featured)$", url) or "list=" in url:
            return url
        return url + "/videos"

    def resolve_channel(self, url: str) -> ChannelRef:
        with self._ydl(extract_flat="in_playlist", playlistend=1) as downloader:
            channel_data = downloader.extract_info(self._uploads_url(url), download=False)
        channel_id = channel_data.get("channel_id") or channel_data.get("id")
        return ChannelRef(channel_id=channel_id,
                          name=channel_data.get("channel") or channel_data.get("uploader") or channel_id,
                          url=channel_data.get("channel_url") or url)

    def list_channel(self, channel_url: str, limit: int | None = None) -> list[ChannelEntry]:
        options: dict[str, Any] = {"extract_flat": "in_playlist"}
        if limit:
            options["playlistend"] = limit
        with self._ydl(**options) as downloader:
            channel_data = downloader.extract_info(self._uploads_url(channel_url), download=False)
        out = []
        for entry in channel_data.get("entries") or []:
            if not entry or not entry.get("id"):
                continue
            out.append(ChannelEntry(video_id=entry["id"], title=entry.get("title") or "",
                                    duration=entry.get("duration"),
                                    live_status=entry.get("live_status")))
        return out

    def fetch_info(self, video_id: str) -> VideoInfo:
        with self._ydl() as downloader:
            video_data = downloader.extract_info(f"https://www.youtube.com/watch?v={video_id}",
                                                 download=False)
        return VideoInfo.from_ytdlp(downloader.sanitize_info(video_data))

    def download_audio(self, video_id: str, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        # No re-encode: faster-whisper reads webm/m4a through ffmpeg/PyAV directly.
        options = {"format": self.audio_format, "outtmpl": str(out_dir / "%(id)s.%(ext)s")}
        with self._ydl(**options) as downloader:
            video_data = downloader.extract_info(f"https://www.youtube.com/watch?v={video_id}",
                                                 download=True)
            path = Path(downloader.prepare_filename(video_data))
        if not path.exists():
            matches = list(out_dir.glob(f"{video_id}.*"))
            if not matches:
                raise RuntimeError(f"yt-dlp reported success but no audio file for {video_id}")
            path = matches[0]
        return path

    def fetch_text(self, url: str) -> str:
        with self._ydl() as downloader:
            return downloader.urlopen(url).read().decode("utf-8", "replace")
