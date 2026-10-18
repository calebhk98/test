"""Plain data types passed between pipeline stages.

Everything here round-trips through JSON so each stage can be cached on disk.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Chapter:
    title: str
    start: float
    end: float | None = None
    url: str | None = None       # podcast chapter files can link each chapter


@dataclass
class VideoInfo:
    video_id: str
    title: str
    url: str
    channel: str = ""
    channel_id: str = ""
    channel_url: str = ""
    description: str = ""
    published: str = ""          # ISO date or datetime
    duration: float = 0.0
    chapters: list[Chapter] = field(default_factory=list)
    source_tags: list[str] = field(default_factory=list)
    live_status: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def timestamp_url(self, seconds: float) -> str:
        if "youtube.com/" in self.url or "youtu.be/" in self.url:
            return f"https://www.youtube.com/watch?v={self.video_id}&t={int(seconds)}s"
        # Media fragments: browsers seek audio and video links to #t=seconds.
        return f"{self.url}#t={int(seconds)}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VideoInfo":
        data = dict(data)
        data["chapters"] = [Chapter(**chapter_data) for chapter_data in data.get("chapters", [])]
        return cls(**data)

    @classmethod
    def from_ytdlp(cls, ytdlp_data: dict) -> "VideoInfo":
        published = ""
        if ytdlp_data.get("timestamp"):
            published = datetime.fromtimestamp(ytdlp_data["timestamp"], timezone.utc).isoformat()
        elif ytdlp_data.get("upload_date"):
            upload_date = ytdlp_data["upload_date"]
            published = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
        chapters = [
            Chapter(title=(chapter.get("title") or "").strip(), start=float(chapter["start_time"]),
                    end=float(chapter["end_time"]) if chapter.get("end_time") is not None else None)
            for chapter in ytdlp_data.get("chapters") or []
        ]
        # Keep only what later stages read; the full yt-dlp dict is huge. Auto
        # captions alone list every translated language in every format: 10.7 MB
        # for one 40 minute video. Keep English and the video's own language, json3 only.
        spoken_language = (ytdlp_data.get("language") or "en").split("-")[0]
        raw = {"language": ytdlp_data.get("language")} if ytdlp_data.get("language") else {}
        for caption_kind in ("subtitles", "automatic_captions"):
            tracks = {
                language: [track for track in formats if track.get("ext") == "json3"]
                for language, formats in (ytdlp_data.get(caption_kind) or {}).items()
                if language.split("-")[0] in ("en", spoken_language)
            }
            tracks = {language: formats for language, formats in tracks.items() if formats}
            if tracks:
                raw[caption_kind] = tracks
        return cls(
            video_id=ytdlp_data["id"],
            title=ytdlp_data.get("title") or ytdlp_data["id"],
            url=ytdlp_data.get("webpage_url") or f"https://www.youtube.com/watch?v={ytdlp_data['id']}",
            channel=ytdlp_data.get("channel") or ytdlp_data.get("uploader") or "",
            channel_id=ytdlp_data.get("channel_id") or "",
            channel_url=ytdlp_data.get("channel_url") or "",
            description=ytdlp_data.get("description") or "",
            published=published,
            duration=float(ytdlp_data.get("duration") or 0),
            chapters=chapters,
            source_tags=list(ytdlp_data.get("tags") or []),
            live_status=ytdlp_data.get("live_status"),
            raw=raw,
        )


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    segments: list[Segment]
    language: str = ""
    model: str = ""              # which transcriber produced it

    @property
    def text(self) -> str:
        return " ".join(segment.text.strip() for segment in self.segments if segment.text.strip())

    def between(self, start: float, end: float | None) -> list[Segment]:
        """Segments whose midpoint falls in [start, end)."""
        matching = []
        for segment in self.segments:
            midpoint = (segment.start + segment.end) / 2
            if midpoint >= start and (end is None or midpoint < end):
                matching.append(segment)
        return matching

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Transcript":
        return cls(segments=[Segment(**segment_data) for segment_data in data["segments"]],
                   language=data.get("language", ""), model=data.get("model", ""))


@dataclass
class Link:
    label: str
    url: str


@dataclass
class Section:
    index: int
    title: str
    start: float
    end: float
    text: str = ""
    links: list[Link] = field(default_factory=list)
    is_sponsor: bool = False
    # Filled by the enricher
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Section":
        data = dict(data)
        data["links"] = [Link(**link_data) for link_data in data.get("links", [])]
        return cls(**data)


@dataclass
class Enrichment:
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    model: str = ""
    #: Produced by a fallback because the configured LLM was unreachable.
    degraded: bool = False


@dataclass
class SearchHit:
    doc_id: str
    kind: str                    # "video" or "section"
    title: str
    path: str                    # wiki-relative markdown path
    video_id: str
    url: str                     # timestamped YouTube link
    score: float
    snippet: str
    tags: list[str] = field(default_factory=list)
    published: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
