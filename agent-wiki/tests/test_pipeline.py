from __future__ import annotations

import json

import pytest

from agentwiki.cli import main
from agentwiki.llm.base import LLM, extract_json
from agentwiki.registry import available, register

from .conftest import REAL_ID


def test_add_writes_linked_pages_and_deletes_audio(app):
    result = app.add(REAL_ID)
    assert result["status"] == "done", result
    assert result["sections"] == 28

    video_md = (app.config.wiki_dir / f"{result['page']}.md").read_text()
    assert video_md.startswith("---\ntitle: ")
    assert '"video_id": ' not in video_md and f'video_id: "{REAL_ID}"' in video_md
    assert "https://www.youtube.com/watch?v=lHmZoRHMZyM&t=1054s" in video_md   # Flux 3 chapter

    section_files = sorted((app.config.wiki_dir / "sections" / REAL_ID).glob("*.md"))
    assert len(section_files) == 28
    flux = next(page_path for page_path in section_files if "flux-3" in page_path.name).read_text()
    assert f"[[{result['page']}|" in flux                       # links up to the video
    assert "https://bfl.ai/models/flux-3-image" in flux     # link from the description
    assert "prev: [[sections/" in flux and "next: [[sections/" in flux
    assert f"[[sections/{REAL_ID}/14-flux-3\\|Flux 3]]" in video_md  # and the video links down

    luma = next(page_path for page_path in section_files if page_path.name.endswith("-luma.md")).read_text()
    assert "sponsor: true" in luma

    # Audio is gone; the transcript cache stays.
    assert not any((app.config.data_dir / "tmp").glob("**/*.webm"))
    assert (app.config.data_dir / "raw" / REAL_ID / "transcript.json").exists()
    assert (app.config.wiki_dir / "channels" / "ai-search.md").exists()


def test_dedupe(app):
    app.add(REAL_ID)
    assert app.has(f"https://www.youtube.com/watch?v={REAL_ID}")["known"]
    again = app.add(f"https://youtu.be/{REAL_ID}")
    assert again["already_added"]
    assert app.source.downloads == [REAL_ID]
    assert app.has("zzzzzzzzzzz")["known"] is False


def test_search_finds_section_and_hides_sponsor(app):
    app.add(REAL_ID)
    hits = app.search("open weights image model VRAM", kind="section")["hits"]
    assert hits[0]["title"] == "Flux 3"
    assert hits[0]["url"].endswith("&t=1054s")
    hits = app.search("Luma")["hits"]
    assert all(hit["title"] != "Luma" for hit in hits)
    assert any(hit["title"] == "Luma" for hit in app.search("Luma", include_sponsor=True)["hits"])
    world = app.search("text to world model consistent", kind="section")["hits"]
    assert world[0]["title"] == "Inspatio World 1.5"


def test_channel_check_backfill_and_run(app):
    result = app.channel_add("https://www.youtube.com/@theAIsearch")
    queued = result["check"]["channels"]["AI Search"]["queued"]
    assert set(queued) == {REAL_ID, "aaaaaaaaaaa", "bbbbbbbbbbb"}    # the Short is filtered
    assert app.check()["channels"]["AI Search"]["queued"] == []      # nothing new the second time
    out = app.run(limit=2)
    assert [processed_video["status"] for processed_video in out["processed"]] == ["done", "done"]
    out = app.run()
    assert out["queue"]["done"] == 3 and out["queue"]["queued"] == 0
    # Fixed-window fallback for videos without chapters
    assert len(list((app.config.wiki_dir / "sections" / "aaaaaaaaaaa").glob("*.md"))) == 3
    assert app.similar("aaaaaaaaaaa")["hits"][0]["video_id"] == "bbbbbbbbbbb"


def test_reprocess_and_reindex_with_new_embedder(app):
    app.add(REAL_ID)
    old = app.embedder.name
    app.reprocess(None, "enrich")
    assert app.catalog.get(REAL_ID)["status"] == "queued"
    assert not (app.config.data_dir / "raw" / REAL_ID / "enrichment.json").exists()
    app.run()
    assert app.source.downloads == [REAL_ID]   # transcript came from cache

    from agentwiki.registry import create
    app.__dict__["embedder"] = create("embedder", {"type": "hashing", "dimensions": 128})
    assert app.search("Flux")["hits"]          # BM25 still works before the reindex
    chunk_count = app.reindex()["chunks_embedded"]
    assert chunk_count > 0
    stats = app.index.stats()["vectors_by_embedder"]
    assert set(stats) == {old, "hashing:128"}


@register("llm", "scripted")
class ScriptedLLM(LLM):
    model = "test"

    def complete(self, prompt, system=None, **options):
        if "Sources:" in prompt:
            return "Flux 3 has 12B parameters and is uncensored [1]."
        if "Section:" in prompt:
            title = prompt.split("Section: ")[1].split("\n")[0]
            return "```json\n" + json.dumps({"summary": f"About {title}.", "tags": [title, "AI News"],
                                             "facts": [f"{title} was covered"]}) + "\n```"
        return json.dumps({"summary": "Weekly AI news.", "tags": ["ai news", "weekly"]})


def test_llm_enricher_and_ask(app):
    from agentwiki.registry import create
    app.__dict__["llm"] = create("llm", {"type": "scripted"})
    app.__dict__["enricher"] = create("enricher", {"type": "llm"}, app)
    result = app.add(REAL_ID)
    flux = app.show(f"{REAL_ID}#14")["content"]
    assert "About Flux 3." in flux and "- Flux 3 was covered" in flux and '"flux-3"' in flux
    assert "sponsor" in app.show(f"{REAL_ID}#10")["content"]
    assert "Weekly AI news." in app.show(REAL_ID)["content"]
    answer_result = app.ask("how big is flux 3")
    assert "12B" in answer_result["answer"] and answer_result["sources"][0]["title"] == "Flux 3"


def test_show_rejects_paths_outside_wiki(app):
    assert "error" in app.show("../config")


def test_extract_json_handles_escapes_and_chatter():
    assert extract_json('Sure! {"a": "he said \\"hi\\" }", "b": [1]} hope that helps') == \
        {"a": 'he said "hi" }', "b": [1]}


def test_registry_lists_builtins():
    assert {"faster-whisper", "youtube-captions", "chain"} <= set(available("transcriber"))
    assert {"sentence-transformers", "ollama", "openai-compatible", "hashing"} <= set(available("embedder"))


def test_cli_json(app, capsys):
    root = str(app.config.root)
    (app.config.root / "config.toml").write_text(
        '[source]\ntype = "fake"\n[transcriber]\ntype = "fake"\n'
        '[embedder]\ntype = "hashing"\n[ingest]\nsleep_between = 0\n')
    assert main(["--root", root, "--json", "has", REAL_ID]) == 4
    capsys.readouterr()
    assert main(["--root", root, "--json", "add", REAL_ID]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "done"
    assert main(["--root", root, "--json", "search", "Flux 3", "-k", "3"]) == 0
    hits = json.loads(capsys.readouterr().out)["hits"]
    assert hits[0]["title"] == "Flux 3"


def test_unreachable_llm_degrades_then_upgrades_when_back(app):
    from agentwiki.registry import create
    down = create("llm", {"type": "ollama", "model": "x", "host": "http://127.0.0.1:9"})
    app.__dict__["llm"] = down
    app.__dict__["enricher"] = create("enricher", {"type": "llm"}, app)
    result = app.add(REAL_ID)
    assert result["status"] == "done"                          # the video is not held back
    enrichment_data = json.loads((app.config.data_dir / "raw" / REAL_ID / "enrichment.json").read_text())
    assert enrichment_data["degraded"] is True
    assert "[size" in app.show(f"{REAL_ID}#14")["content"]   # local facts filled in

    app.run()                                            # LLM still down: nothing requeued
    assert app.catalog.get(REAL_ID)["status"] == "done"

    llm_back = create("llm", {"type": "scripted"})
    app.__dict__["llm"] = llm_back
    app.__dict__["enricher"] = create("enricher", {"type": "llm"}, app)
    out = app.run()
    assert out["requeued_for_llm"] == 1
    assert "About Flux 3." in app.show(f"{REAL_ID}#14")["content"]
    enrichment_data = json.loads((app.config.data_dir / "raw" / REAL_ID / "enrichment.json").read_text())
    assert enrichment_data["degraded"] is False
    assert app.source.downloads == [REAL_ID]             # upgrade reused the transcript


def test_youtube_block_stops_run_and_keeps_queue(app, monkeypatch):
    app.channel_add("@theAIsearch")
    calls = []

    def blocked(video_id):
        calls.append(video_id)
        raise RuntimeError("ERROR: [youtube] x: Sign in to confirm you\u2019re not a bot.")
    monkeypatch.setattr(app.source, "fetch_info", blocked)
    out = app.run()
    assert len(calls) == 1 and "stopped" in out          # did not burn through the queue
    assert out["queue"]["queued"] == 3 and out["queue"]["failed"] == 0
    assert app.catalog.get(calls[0])["attempts"] == 0


def test_whole_video_vector_single_pass_when_it_fits(app):
    result = app.add(REAL_ID)
    assert result["whole_video"] == "single"      # short fake transcript fits 512 tokens
    app.config.data["index"]["whole_video"] = "mean"
    assert app.reindex()["whole_video"] == {"single": 0, "mean": 1}


@register("llm", "cannot-load")
class CannotLoadLLM(LLM):
    model = "x"

    def complete(self, prompt, system=None, **options):
        raise OSError("couldn't connect to huggingface.co to download weights")


def test_llm_that_cannot_load_counts_as_unavailable(app):
    from agentwiki.registry import create
    app.__dict__["llm"] = create("llm", {"type": "cannot-load"})
    app.__dict__["enricher"] = create("enricher", {"type": "llm"}, app)
    assert app.add(REAL_ID)["status"] == "done"
    enrichment_data = json.loads((app.config.data_dir / "raw" / REAL_ID / "enrichment.json").read_text())
    assert enrichment_data["degraded"] is True


def test_local_audio_source_uses_dropped_file_and_keeps_it(app, tmp_path):
    from agentwiki.registry import create
    drop_folder = tmp_path / "drop"
    drop_folder.mkdir()
    (drop_folder / f"{REAL_ID}.mp3").write_bytes(b"audio from a converter website")
    inner_source = app.source
    app.__dict__["source"] = create("source", {"type": "local-audio", "folder": str(drop_folder),
                                              "source": {"type": "fake"}}, app)
    app.source.inner_source = inner_source
    assert app.add(REAL_ID)["status"] == "done"
    assert inner_source.downloads == []                       # nothing was downloaded
    assert (drop_folder / f"{REAL_ID}.mp3").exists()          # the original is kept
    assert not any((app.config.data_dir / "tmp").glob("**/*.mp3"))   # the working copy is gone
