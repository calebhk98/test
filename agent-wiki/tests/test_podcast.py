import json

from agentwiki.sources import podcast
from agentwiki.sources.podcast import PodcastSource, episode_id

FEED = b"""<?xml version="1.0"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:podcast="https://podcastindex.org/namespace/1.0"
     xmlns:content="http://purl.org/rss/1.0/modules/content/" version="2.0">
<channel><title>Test Cast</title>
<item><title>Episode one</title><guid>g-1</guid><link>https://ex.com/1</link>
<pubDate>Wed, 01 Oct 2026 10:00:00 +0000</pubDate><itunes:duration>45:10</itunes:duration>
<enclosure url="https://ex.com/1.mp3" length="1" type="audio/mpeg"/>
<podcast:chapters url="https://ex.com/1/chapters.json" type="application/json+chapters"/>
<content:encoded><![CDATA[<p>Intro. See <a href="https://bfl.ai">Flux</a></p>]]></content:encoded>
</item></channel></rss>"""
CHAPTERS = {"chapters": [{"startTime": 0, "title": "Welcome"},
                         {"startTime": 300, "title": "Flux", "url": "https://bfl.ai"},
                         {"startTime": 900, "title": "hidden", "toc": False}]}


def test_podcast_feed_and_chapters(monkeypatch):
    def fake_get(url, timeout=60):
        return FEED if url.endswith("feed") else json.dumps(CHAPTERS).encode()
    monkeypatch.setattr(podcast, "_get", fake_get)
    s = PodcastSource(feeds=["https://ex.com/feed"])
    ents = s.list_channel("https://ex.com/feed")
    assert ents[0].video_id == episode_id("g-1") and ents[0].duration == 2710
    assert s.parse_video_id("https://ex.com/1") == episode_id("g-1")
    info = s.fetch_info(episode_id("g-1"))
    assert info.channel == "Test Cast" and info.published.startswith("2026-10-01")
    assert [c.title for c in info.chapters] == ["Welcome", "Flux"]
    assert info.chapters[1].url == "https://bfl.ai"
    assert "Flux https://bfl.ai" in info.description
    assert info.timestamp_url(300) == "https://ex.com/1#t=300"
