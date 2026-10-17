from agentwiki import hardware
from agentwiki.embed.hashing import HashingEmbedder
from agentwiki.enrich.facts import extract_facts, sentences
from agentwiki.enrich.local import LocalEnricher
from agentwiki.models import Section, Segment, Transcript, VideoInfo
from agentwiki.segment.topics import TopicSegmenter


def test_facts_find_size_hardware_license_censorship():
    text = ("Wan 3 is a new text to video model. It has 14 billion parameters and runs on 24 GB of VRAM. "
            "The weights are open source under Apache 2.0. It is also uncensored, which is rare. "
            "The weather was nice today.")
    facts = extract_facts(text)
    joined = " ".join(facts)
    assert "[size] It has 14 billion" in joined.replace("size, hardware", "size")
    assert "license" in joined and "censorship" in joined
    assert not any("weather" in f for f in facts)


def test_sentences_falls_back_to_windows_for_unpunctuated_captions():
    text = " ".join(["word"] * 100)
    assert len(sentences(text, window_words=25)) == 4


def test_local_enricher_gives_tags_summary_facts_without_llm():
    e = LocalEnricher(HashingEmbedder(256))
    s = Section(1, "Flux 3", 0, 60, text="Flux 3 is an image model. Flux 3 has 12 billion parameters. "
                                         "It is open weights. Black Forest Labs made Flux 3.")
    out = e.enrich_section(VideoInfo("v", "t", "u"), s)
    assert out.tags[0] == "flux-3" and out.summary and out.facts


def test_topic_segmenter_finds_a_topic_change():
    robots = "robot humanoid walking legs balance motors gripper"
    music = "song music melody vocals guitar drums lyrics"
    segs = [Segment(i * 5, i * 5 + 5, robots if i < 36 else music) for i in range(72)]
    secs = TopicSegmenter(HashingEmbedder(256), min_section_seconds=30) \
        .split(VideoInfo("v", "t", "u", duration=360), Transcript(segs))
    assert len(secs) >= 2
    assert any(abs(s.start - 180) <= 20 for s in secs[1:])


def test_hardware_tiers():
    tiers = [(20, 0, "big-gpu"), (4, 0, "small-gpu"), (0, 12, "laptop"), (0, 0, "phone")]
    gpu = hardware.Hardware("cuda", "x", 80, 64, 16, "x86_64")
    small_gpu = hardware.Hardware("cuda", "x", 6, 16, 8, "x86_64")
    laptop = hardware.Hardware("cpu", "", 0, 16, 8, "x86_64")
    phone = hardware.Hardware("cpu", "", 0, 6, 8, "aarch64")
    assert [hardware.pick(tiers, h) for h in (gpu, small_gpu, laptop, phone)] == \
        ["big-gpu", "small-gpu", "laptop", "phone"]
