from agentwiki.enrich.base import normalize_tags
from agentwiki.index.sqlite_index import chunk_text
from agentwiki.segment.chapters import description_links, sponsor_names
from agentwiki.sources.youtube import YtDlpSource
from agentwiki.transcribe.youtube_captions import parse_json3


def test_parse_video_id():
    parse_video_id = YtDlpSource().parse_video_id
    for url_or_id in ["lHmZoRHMZyM", "https://www.youtube.com/watch?v=lHmZoRHMZyM&t=5s",
                      "https://youtu.be/lHmZoRHMZyM", "https://www.youtube.com/shorts/lHmZoRHMZyM",
                      "https://www.youtube.com/live/lHmZoRHMZyM?si=x"]:
        assert parse_video_id(url_or_id) == "lHmZoRHMZyM", url_or_id
    assert parse_video_id("https://www.youtube.com/@theAIsearch") is None


def test_uploads_url():
    uploads_url = YtDlpSource._uploads_url
    assert uploads_url("@theAIsearch") == "https://www.youtube.com/@theAIsearch/videos"
    assert uploads_url("https://www.youtube.com/@theAIsearch/") == \
        "https://www.youtube.com/@theAIsearch/videos"
    assert uploads_url("https://www.youtube.com/@theAIsearch/streams").endswith("/streams")


def test_description_links_continue_label_on_bare_url_line():
    description = ("Plasma conjecture https://a.example/1\nhttps://b.example/2\n\n00:00 intro\n"
                   "https://c.example")
    links = description_links(description)
    assert [(link.label, link.url) for link in links] == [("Plasma conjecture", "https://a.example/1"),
                                                          ("Plasma conjecture", "https://b.example/2")]


def test_sponsor_names():
    assert sponsor_names("Thanks to our sponsor Luma. Try it today") == ["Luma"]
    assert sponsor_names("This video is sponsored by Eleven Labs!") == ["Eleven Labs"]
    assert sponsor_names("no sponsor here") == []


def test_parse_json3():
    data = {"events": [{"tStartMs": 0, "dDurationMs": 1500, "segs": [{"utf8": "hello "}, {"utf8": "world"}]},
                       {"tStartMs": 1500, "dDurationMs": 10, "segs": [{"utf8": "\n"}]},
                       {"tStartMs": 2000, "dDurationMs": 1000}]}
    segments = parse_json3(data)
    assert len(segments) == 1 and segments[0].text == "hello world" and segments[0].end == 1.5


def test_chunk_text_covers_everything_with_overlap():
    text = " ".join(f"Sentence number {number} is here." for number in range(300))
    chunks = chunk_text(text, 500, 100)
    assert all(len(chunk) <= 500 for chunk in chunks)
    assert chunks[0].startswith("Sentence number 0") and chunks[-1].endswith("number 299 is here.")
    assert all(not chunk.startswith(("entence", "umber")) for chunk in chunks)
    assert chunk_text("short", 500, 100) == ["short"]


def test_normalize_tags():
    assert normalize_tags(["Text to Video", "#Flux 3", "GPT 6.1", "2026", "flux-3"]) == \
        ["text-to-video", "flux-3", "gpt-6-1"]
