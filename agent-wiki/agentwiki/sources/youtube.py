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
                 extra_options: dict[str, Any] | None = None):
        self.cookies_file = cookies_file
        self.cookies_from_browser = cookies_from_browser
        self.js_runtimes = js_runtimes
        self.audio_format = audio_format
        self.extra_options = extra_options or {}

    def _opts(self, **over) -> dict:
        o: dict[str, Any] = {"quiet": True, "no_warnings": True, "noprogress": True}
        if self.cookies_file:
            o["cookiefile"] = self.cookies_file
        if self.cookies_from_browser:
            o["cookiesfrombrowser"] = (self.cookies_from_browser,)
        if self.js_runtimes:
            o["js_runtimes"] = {r: {} for r in self.js_runtimes}
        o.update(self.extra_options)
        o.update(over)
        return o

    def _ydl(self, **over):
        import yt_dlp
        return yt_dlp.YoutubeDL(self._opts(**over))

    def parse_video_id(self, url_or_id: str) -> str | None:
        s = url_or_id.strip()
        if _ID_RE.match(s):
            return s
        m = _URL_ID_RE.search(s)
        return m.group(1) if m else None

    @staticmethod
    def _uploads_url(url: str) -> str:
        url = url.strip().rstrip("/")
        if url.startswith("@"):
            url = f"https://www.youtube.com/{url}"
        if re.search(r"/(videos|streams|shorts|playlists|featured)$", url) or "list=" in url:
            return url
        return url + "/videos"

    def resolve_channel(self, url: str) -> ChannelRef:
        with self._ydl(extract_flat="in_playlist", playlistend=1) as ydl:
            d = ydl.extract_info(self._uploads_url(url), download=False)
        cid = d.get("channel_id") or d.get("id")
        return ChannelRef(channel_id=cid, name=d.get("channel") or d.get("uploader") or cid,
                          url=d.get("channel_url") or url)

    def list_channel(self, channel_url: str, limit: int | None = None) -> list[ChannelEntry]:
        opts: dict[str, Any] = {"extract_flat": "in_playlist"}
        if limit:
            opts["playlistend"] = limit
        with self._ydl(**opts) as ydl:
            d = ydl.extract_info(self._uploads_url(channel_url), download=False)
        out = []
        for e in d.get("entries") or []:
            if not e or not e.get("id"):
                continue
            out.append(ChannelEntry(video_id=e["id"], title=e.get("title") or "",
                                    duration=e.get("duration"), live_status=e.get("live_status")))
        return out

    def fetch_info(self, video_id: str) -> VideoInfo:
        with self._ydl() as ydl:
            d = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        return VideoInfo.from_ytdlp(ydl.sanitize_info(d))

    def download_audio(self, video_id: str, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        # No re-encode: faster-whisper reads webm/m4a through ffmpeg/PyAV directly.
        opts = {"format": self.audio_format, "outtmpl": str(out_dir / "%(id)s.%(ext)s")}
        with self._ydl(**opts) as ydl:
            d = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
            path = Path(ydl.prepare_filename(d))
        if not path.exists():
            matches = list(out_dir.glob(f"{video_id}.*"))
            if not matches:
                raise RuntimeError(f"yt-dlp reported success but no audio file for {video_id}")
            path = matches[0]
        return path

    def fetch_text(self, url: str) -> str:
        with self._ydl() as ydl:
            return ydl.urlopen(url).read().decode("utf-8", "replace")
