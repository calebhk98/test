from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from ..models import VideoInfo
from ..registry import Component


@dataclass
class ChannelEntry:
    """A video seen in a channel listing, before full metadata is fetched."""
    video_id: str
    title: str = ""
    duration: float | None = None
    live_status: str | None = None


@dataclass
class ChannelRef:
    channel_id: str
    name: str
    url: str


class VideoSource(Component, ABC):
    @abstractmethod
    def parse_video_id(self, url_or_id: str) -> str | None: ...

    @abstractmethod
    def resolve_channel(self, url: str) -> ChannelRef: ...

    @abstractmethod
    def list_channel(self, channel_url: str, limit: int | None = None) -> list[ChannelEntry]:
        """Newest first. `limit=None` means the whole upload list."""

    @abstractmethod
    def fetch_info(self, video_id: str) -> VideoInfo: ...

    @abstractmethod
    def download_audio(self, video_id: str, out_dir: Path) -> Path: ...

    def fetch_text(self, url: str) -> str:
        """Fetch a URL with the source's session (cookies, headers)."""
        raise NotImplementedError
