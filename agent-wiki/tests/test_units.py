from agentwiki.enrich.base import normalize_tags
from agentwiki.index.sqlite_index import chunk_text
from agentwiki.segment.chapters import description_links, sponsor_names
from agentwiki.sources.youtube import YtDlpSource
from agentwiki.transcribe.youtube_captions import parse_json3


def test_parse_video_id():
    p = YtDlpSource().parse_video_id
    for s in ["lHmZoRHMZyM", "https://www.youtube.com/watch?v=lHmZoRHMZyM&t=5s",
              "https://youtu.be/lHmZoRHMZyM", "https://www.youtube.com/shorts/lHmZoRHMZyM",
              "https://www.youtube.com/live/lHmZoRHMZyM?si=x"]:
        assert p(s) == "lHmZoRHMZyM", s
    assert p("https://www.youtube.com/@theAIsearch") is None


def test_uploads_url():
    u = YtDlpSource._uploads_url
    assert u("@theAIsearch") == "https://www.youtube.com/@theAIsearch/videos"
    assert u("https://www.youtube.com/@theAIsearch/") == "https://www.youtube.com/@theAIsearch/videos"
    assert u("https://www.youtube.com/@theAIsearch/streams").endswith("/streams")


def test_description_links_continue_label_on_bare_url_line():
    d = "Plasma conjecture https://a.example/1\nhttps://b.example/2\n\n00:00 intro\nhttps://c.example"
    links = description_links(d)
    assert [(l.label, l.url) for l in links] == [("Plasma conjecture", "https://a.example/1"),
                                                ("Plasma conjecture", "https://b.example/2")]


def test_sponsor_names():
    assert sponsor_names("Thanks to our sponsor Luma. Try it today") == ["Luma"]
    assert sponsor_names("This video is sponsored by Eleven Labs!") == ["Eleven Labs"]
    assert sponsor_names("no sponsor here") == []


def test_parse_json3():
    data = {"events": [{"tStartMs": 0, "dDurationMs": 1500, "segs": [{"utf8": "hello "}, {"utf8": "world"}]},
                       {"tStartMs": 1500, "dDurationMs": 10, "segs": [{"utf8": "\n"}]},
                       {"tStartMs": 2000, "dDurationMs": 1000}]}
    segs = parse_json3(data)
    assert len(segs) == 1 and segs[0].text == "hello world" and segs[0].end == 1.5


def test_chunk_text_covers_everything_with_overlap():
    text = " ".join(f"Sentence number {i} is here." for i in range(300))
    chunks = chunk_text(text, 500, 100)
    assert all(len(c) <= 500 for c in chunks)
    assert chunks[0].startswith("Sentence number 0") and chunks[-1].endswith("number 299 is here.")
    assert all(not c.startswith(("entence", "umber")) for c in chunks)
    assert chunk_text("short", 500, 100) == ["short"]


def test_normalize_tags():
    assert normalize_tags(["Text to Video", "#Flux 3", "GPT 6.1", "2026", "flux-3"]) == \
        ["text-to-video", "flux-3", "gpt-6-1"]
