"""Podcasts (or any RSS feed with audio enclosures) as a source.

A "channel" is a feed URL; an episode id is a hash of its guid. Podcasting
2.0 chapter files (`<podcast:chapters>`) become chapters, so episodes split
the same way YouTube videos with chapters do.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

from ..models import Chapter, VideoInfo
from ..registry import register
from .base import ChannelEntry, ChannelRef, VideoSource

NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
      "podcast": "https://podcastindex.org/namespace/1.0",
      "content": "http://purl.org/rss/1.0/modules/content/"}
_ID_RE = re.compile(r"^pod-[0-9a-f]{12}$")
UA = {"User-Agent": "agent-wiki/0.1 (+podcast source)"}


def episode_id(guid: str) -> str:
    return "pod-" + hashlib.sha1(guid.encode()).hexdigest()[:12]


def _text(el, path: str) -> str:
    x = el.find(path, NS)
    return (x.text or "").strip() if x is not None and x.text else ""


def _strip_html(s: str) -> str:
    s = re.sub(r"<br\s*/?>|</p>|</li>", "\n", s, flags=re.I)
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>([^<]*)</a>', r"\2 \1", s, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def _duration(s: str) -> float:
    if not s:
        return 0.0
    parts = [float(p) for p in s.split(":")]
    total = 0.0
    for p in parts:
        total = total * 60 + p
    return total


def _get(url: str, timeout: float = 60) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


@register("source", "podcast")
class PodcastSource(VideoSource):
    def __init__(self, feeds: list[str] | None = None):
        self.feeds = list(feeds or [])
        self.ctx = None
        self._parsed: dict[str, tuple[ET.Element, list[ET.Element]]] = {}

    @classmethod
    def from_config(cls, params, ctx=None):
        obj = cls(**params)
        obj.ctx = ctx
        return obj

    def _feed(self, url: str):
        if url not in self._parsed:
            root = ET.fromstring(_get(url))
            chan = root.find("channel")
            self._parsed[url] = (chan, chan.findall("item"))
        return self._parsed[url]

    def _known_feeds(self) -> list[str]:
        urls = list(self.feeds)
        if self.ctx is not None:
            urls += [c["url"] for c in self.ctx.catalog.channels() if c["url"] not in urls]
        return urls

    def parse_video_id(self, url_or_id: str) -> str | None:
        s = url_or_id.strip()
        if _ID_RE.match(s):
            return s
        for feed in self._known_feeds():          # an episode's page or audio URL
            for item in self._feed(feed)[1]:
                enc = item.find("enclosure")
                if s in (_text(item, "link"), enc.get("url") if enc is not None else None):
                    return episode_id(_text(item, "guid") or _text(item, "link"))
        return None

    def resolve_channel(self, url: str) -> ChannelRef:
        chan, _ = self._feed(url)
        return ChannelRef(channel_id="feed-" + hashlib.sha1(url.encode()).hexdigest()[:12],
                          name=_text(chan, "title") or url, url=url)

    def list_channel(self, channel_url: str, limit: int | None = None) -> list[ChannelEntry]:
        _, items = self._feed(channel_url)
        out = [ChannelEntry(video_id=episode_id(_text(i, "guid") or _text(i, "link")),
                            title=_text(i, "title"),
                            duration=_duration(_text(i, "itunes:duration")) or None)
               for i in items]
        return out[:limit] if limit else out

    def _find(self, vid: str):
        for feed in self._known_feeds():
            chan, items = self._feed(feed)
            for item in items:
                if episode_id(_text(item, "guid") or _text(item, "link")) == vid:
                    return feed, chan, item
        raise KeyError(f"{vid} is not in any configured or subscribed feed")

    def fetch_info(self, video_id: str) -> VideoInfo:
        feed, chan, item = self._find(video_id)
        enc = item.find("enclosure")
        published = ""
        if _text(item, "pubDate"):
            published = parsedate_to_datetime(_text(item, "pubDate")).isoformat()
        chapters = []
        ch = item.find("podcast:chapters", NS)
        if ch is not None and ch.get("url"):
            try:
                data = json.loads(_get(ch.get("url"), 30))
                chapters = [Chapter(title=c.get("title", "").strip(), start=float(c["startTime"]),
                                    end=float(c["endTime"]) if c.get("endTime") else None,
                                    url=c.get("url"))
                            for c in data.get("chapters", []) if c.get("toc", True) is not False]
            except Exception:
                chapters = []
        desc = _text(item, "content:encoded") or _text(item, "description")
        return VideoInfo(
            video_id=video_id, title=_text(item, "title"),
            url=_text(item, "link") or (enc.get("url") if enc is not None else feed),
            channel=_text(chan, "title"), channel_id="feed-" + hashlib.sha1(feed.encode()).hexdigest()[:12],
            channel_url=feed, description=_strip_html(desc), published=published,
            duration=_duration(_text(item, "itunes:duration")), chapters=chapters,
            source_tags=[c.text for c in item.findall("category") if c.text],
            raw={"audio_url": enc.get("url") if enc is not None else ""})

    def download_audio(self, video_id: str, out_dir: Path) -> Path:
        info = self.fetch_info(video_id)
        url = info.raw.get("audio_url")
        if not url:
            raise RuntimeError(f"{video_id} has no audio enclosure")
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(url.split("?")[0]).suffix or ".mp3"
        path = out_dir / f"{video_id}{ext}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, \
                open(path, "wb") as f:
            shutil.copyfileobj(r, f)
        return path

    def fetch_text(self, url: str) -> str:
        return _get(url).decode("utf-8", "replace")
