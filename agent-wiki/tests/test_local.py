import pytest

from agentwiki import hardware
from agentwiki.embed.hashing import HashingEmbedder
from agentwiki.enrich.base import PartUnavailable, Tagger
from agentwiki.enrich.fact_extractors import PatternFactExtractor
from agentwiki.enrich.text_tools import split_sentences
from agentwiki.models import Section, Segment, Transcript, VideoInfo
from agentwiki.registry import create, register
from agentwiki.segment.topics import TopicSegmenter

FLUX_TEXT = ("Flux 3 is an image model. Flux 3 has 12 billion parameters. "
             "It is open weights. Black Forest Labs made Flux 3.")


class FakeApp:
    """Only what the enrichment parts read from the App."""
    embedder = HashingEmbedder(256)
    llm = None


def test_pattern_facts_find_size_hardware_license_censorship():
    text = ("Wan 3 is a new text to video model. It has 14 billion parameters and runs on 24 GB of VRAM. "
            "The weights are open source under Apache 2.0. It is also uncensored, which is rare. "
            "The weather was nice today.")
    facts = PatternFactExtractor().extract_from_text(text)
    joined = " ".join(facts)
    assert "It has 14 billion" in joined and "size" in joined
    assert "license" in joined and "censorship" in joined
    assert not any("weather" in fact for fact in facts)


def test_pattern_facts_are_configurable():
    extractor = PatternFactExtractor(extra_patterns={"release": r"\breleased\b"})
    assert extractor.extract_from_text("They released it on Monday.") == ["[release] They released it on Monday."]
    only_custom = PatternFactExtractor(patterns={"weather": r"\bsunny\b"})
    assert only_custom.extract_from_text("It has 7B parameters. It was sunny.") == ["[weather] It was sunny."]


def test_sentences_fall_back_to_windows_for_unpunctuated_captions():
    assert len(split_sentences(" ".join(["word"] * 100), window_words=25)) == 4


def test_local_preset_gives_tags_summary_facts_without_llm():
    enricher = create("enricher", {"type": "local"}, FakeApp())
    section = Section(1, "Flux 3", 0, 60, text=FLUX_TEXT)
    result = enricher.enrich_section(VideoInfo("v", "t", "u"), section)
    assert result.tags[0] == "flux-3" and result.summary and result.facts
    assert result.model.startswith("local(")


@register("tagger", "always-unavailable")
class UnavailableTagger(Tagger):
    def tag_section(self, video_info, section):
        raise PartUnavailable("server is down")


def test_composite_mixes_parts_and_falls_back_when_one_is_unavailable():
    enricher = create("enricher", {
        "type": "composite",
        "taggers": ["title-and-links", {"type": "always-unavailable", "fallback": "word-counts"}],
        "summarizer": "first-sentences",
        "fact_extractors": [{"type": "patterns", "extra_patterns": {"maker": r"\bmade\b"}}],
    }, FakeApp())
    result = enricher.enrich_section(VideoInfo("v", "t", "u"), Section(1, "Flux 3", 0, 60, text=FLUX_TEXT))
    assert result.degraded is True
    assert result.tags[0] == "flux-3" and "flux" in result.tags      # word counts filled in
    assert result.summary.startswith("Flux 3 is an image model.")
    assert any(fact.startswith("[maker]") for fact in result.facts)


def test_unavailable_part_without_fallback_is_skipped_not_fatal():
    enricher = create("enricher", {"type": "composite", "taggers": ["always-unavailable"]}, FakeApp())
    result = enricher.enrich_section(VideoInfo("v", "t", "u"), Section(1, "X", 0, 60, text=FLUX_TEXT))
    assert result.tags == [] and result.degraded is True


def test_unknown_part_setting_names_the_accepted_ones():
    with pytest.raises(ValueError, match="Settings it accepts"):
        create("enricher", {"type": "composite", "summarizer": {"type": "first-sentences", "lenght": 3}},
               FakeApp())


def test_topic_segmenter_finds_a_topic_change():
    robots = "robot humanoid walking legs balance motors gripper"
    music = "song music melody vocals guitar drums lyrics"
    segments = [Segment(block * 5, block * 5 + 5, robots if block < 36 else music) for block in range(72)]
    sections = TopicSegmenter(HashingEmbedder(256), min_section_seconds=30) \
        .split(VideoInfo("v", "t", "u", duration=360), Transcript(segments))
    assert len(sections) >= 2
    assert any(abs(section.start - 180) <= 20 for section in sections[1:])


def test_hardware_tiers():
    tiers = [(20, 0, "big-gpu"), (4, 0, "small-gpu"), (0, 12, "laptop"), (0, 0, "phone")]
    workstation = hardware.Hardware("cuda", "x", 80, 64, 16, "x86_64")
    small_gpu = hardware.Hardware("cuda", "x", 6, 16, 8, "x86_64")
    laptop = hardware.Hardware("cpu", "", 0, 16, 8, "x86_64")
    phone = hardware.Hardware("cpu", "", 0, 6, 8, "aarch64")
    assert [hardware.pick(tiers, machine) for machine in (workstation, small_gpu, laptop, phone)] == \
        ["big-gpu", "small-gpu", "laptop", "phone"]


def test_llm_preset_builds_on_every_fallback_preset_with_nested_fallbacks():
    from agentwiki.llm.null import NullLLM

    class AppWithoutLLM(FakeApp):
        llm = NullLLM()
    for fallback in ("local", "keyword"):            # "models" would download GLiNER2 and BART
        enricher = create("enricher", {"type": "llm", "fallback": fallback}, AppWithoutLLM())
        result = enricher.enrich_section(VideoInfo("v", "t", "u"), Section(1, "Flux 3", 0, 60, text=FLUX_TEXT))
        assert result.degraded is True and result.tags[0] == "flux-3", fallback
    assert "llm[null]>seq2seq" in create("enricher", {"type": "llm", "fallback": "models"}, AppWithoutLLM()).name
