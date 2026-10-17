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

XML_NAMESPACES = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
                  "podcast": "https://podcastindex.org/namespace/1.0",
                  "content": "http://purl.org/rss/1.0/modules/content/"}
_ID_RE = re.compile(r"^pod-[0-9a-f]{12}$")
REQUEST_HEADERS = {"User-Agent": "agent-wiki/0.1 (+podcast source)"}


def episode_id(guid: str) -> str:
    return "pod-" + hashlib.sha1(guid.encode()).hexdigest()[:12]


def _text(element, path: str) -> str:
    found = element.find(path, XML_NAMESPACES)
    return (found.text or "").strip() if found is not None and found.text else ""


def _strip_html(html_text: str) -> str:
    html_text = re.sub(r"<br\s*/?>|</p>|</li>", "\n", html_text, flags=re.I)
    html_text = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>([^<]*)</a>', r"\2 \1", html_text, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", html_text)).strip()


def _duration(duration_text: str) -> float:
    if not duration_text:
        return 0.0
    parts = [float(part) for part in duration_text.split(":")]
    total = 0.0
    for part in parts:
        total = total * 60 + part
    return total


def _get(url: str, timeout: float = 60) -> bytes:
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


@register("source", "podcast")
class PodcastSource(VideoSource):
    def __init__(self, feeds: list[str] | None = None):
        self.feeds = list(feeds or [])
        self.app = None
        self._parsed: dict[str, tuple[ET.Element, list[ET.Element]]] = {}

    @classmethod
    def from_config(cls, params, app=None):
        source = cls(**params)
        source.app = app
        return source

    def _feed(self, url: str):
        if url not in self._parsed:
            root = ET.fromstring(_get(url))
            channel_element = root.find("channel")
            self._parsed[url] = (channel_element, channel_element.findall("item"))
        return self._parsed[url]

    def _known_feeds(self) -> list[str]:
        urls = list(self.feeds)
        if self.app is not None:
            urls += [channel["url"] for channel in self.app.catalog.channels() if channel["url"] not in urls]
        return urls

    def parse_video_id(self, url_or_id: str) -> str | None:
        text = url_or_id.strip()
        if _ID_RE.match(text):
            return text
        for feed in self._known_feeds():          # an episode's page or audio URL
            for item in self._feed(feed)[1]:
                enclosure = item.find("enclosure")
                if text in (_text(item, "link"), enclosure.get("url") if enclosure is not None else None):
                    return episode_id(_text(item, "guid") or _text(item, "link"))
        return None

    def resolve_channel(self, url: str) -> ChannelRef:
        channel_element, _ = self._feed(url)
        return ChannelRef(channel_id="feed-" + hashlib.sha1(url.encode()).hexdigest()[:12],
                          name=_text(channel_element, "title") or url, url=url)

    def list_channel(self, channel_url: str, limit: int | None = None) -> list[ChannelEntry]:
        _, items = self._feed(channel_url)
        out = [ChannelEntry(video_id=episode_id(_text(item, "guid") or _text(item, "link")),
                            title=_text(item, "title"),
                            duration=_duration(_text(item, "itunes:duration")) or None)
               for item in items]
        return out[:limit] if limit else out

    def _find(self, video_id: str):
        for feed in self._known_feeds():
            channel_element, items = self._feed(feed)
            for item in items:
                if episode_id(_text(item, "guid") or _text(item, "link")) == video_id:
                    return feed, channel_element, item
        raise KeyError(f"{video_id} is not in any configured or subscribed feed")

    def fetch_info(self, video_id: str) -> VideoInfo:
        feed, channel_element, item = self._find(video_id)
        enclosure = item.find("enclosure")
        published = ""
        if _text(item, "pubDate"):
            published = parsedate_to_datetime(_text(item, "pubDate")).isoformat()
        chapters = []
        chapters_element = item.find("podcast:chapters", XML_NAMESPACES)
        if chapters_element is not None and chapters_element.get("url"):
            try:
                data = json.loads(_get(chapters_element.get("url"), 30))
                chapters = [Chapter(title=entry.get("title", "").strip(), start=float(entry["startTime"]),
                                    end=float(entry["endTime"]) if entry.get("endTime") else None,
                                    url=entry.get("url"))
                            for entry in data.get("chapters", []) if entry.get("toc", True) is not False]
            except Exception:
                chapters = []
        description = _text(item, "content:encoded") or _text(item, "description")
        return VideoInfo(
            video_id=video_id, title=_text(item, "title"),
            url=_text(item, "link") or (enclosure.get("url") if enclosure is not None else feed),
            channel=_text(channel_element, "title"),
            channel_id="feed-" + hashlib.sha1(feed.encode()).hexdigest()[:12],
            channel_url=feed, description=_strip_html(description), published=published,
            duration=_duration(_text(item, "itunes:duration")), chapters=chapters,
            source_tags=[category.text for category in item.findall("category") if category.text],
            raw={"audio_url": enclosure.get("url") if enclosure is not None else ""})

    def download_audio(self, video_id: str, out_dir: Path) -> Path:
        video_info = self.fetch_info(video_id)
        url = video_info.raw.get("audio_url")
        if not url:
            raise RuntimeError(f"{video_id} has no audio enclosure")
        out_dir.mkdir(parents=True, exist_ok=True)
        extension = Path(url.split("?")[0]).suffix or ".mp3"
        path = out_dir / f"{video_id}{extension}"
        request = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(request, timeout=120) as response, \
                open(path, "wb") as audio_file:
            shutil.copyfileobj(response, audio_file)
        return path

    def fetch_text(self, url: str) -> str:
        return _get(url).decode("utf-8", "replace")
