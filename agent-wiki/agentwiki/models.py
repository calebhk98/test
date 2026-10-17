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
    def from_dict(cls, d: dict) -> "VideoInfo":
        d = dict(d)
        d["chapters"] = [Chapter(**c) for c in d.get("chapters", [])]
        return cls(**d)

    @classmethod
    def from_ytdlp(cls, d: dict) -> "VideoInfo":
        published = ""
        if d.get("timestamp"):
            published = datetime.fromtimestamp(d["timestamp"], timezone.utc).isoformat()
        elif d.get("upload_date"):
            u = d["upload_date"]
            published = f"{u[:4]}-{u[4:6]}-{u[6:8]}"
        chapters = [
            Chapter(title=(c.get("title") or "").strip(), start=float(c["start_time"]),
                    end=float(c["end_time"]) if c.get("end_time") is not None else None)
            for c in d.get("chapters") or []
        ]
        # Keep only what later stages read; the full yt-dlp dict is huge.
        raw = {k: d.get(k) for k in ("subtitles", "automatic_captions", "language") if d.get(k)}
        return cls(
            video_id=d["id"],
            title=d.get("title") or d["id"],
            url=d.get("webpage_url") or f"https://www.youtube.com/watch?v={d['id']}",
            channel=d.get("channel") or d.get("uploader") or "",
            channel_id=d.get("channel_id") or "",
            channel_url=d.get("channel_url") or "",
            description=d.get("description") or "",
            published=published,
            duration=float(d.get("duration") or 0),
            chapters=chapters,
            source_tags=list(d.get("tags") or []),
            live_status=d.get("live_status"),
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
        return " ".join(s.text.strip() for s in self.segments if s.text.strip())

    def between(self, start: float, end: float | None) -> list[Segment]:
        """Segments whose midpoint falls in [start, end)."""
        out = []
        for s in self.segments:
            mid = (s.start + s.end) / 2
            if mid >= start and (end is None or mid < end):
                out.append(s)
        return out

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Transcript":
        return cls(segments=[Segment(**s) for s in d["segments"]],
                   language=d.get("language", ""), model=d.get("model", ""))


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
    def from_dict(cls, d: dict) -> "Section":
        d = dict(d)
        d["links"] = [Link(**l) for l in d.get("links", [])]
        return cls(**d)


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
