from __future__ import annotations

import json

import pytest

from agentwiki.cli import main
from agentwiki.llm.base import LLM, extract_json
from agentwiki.registry import available, register

from .conftest import REAL_ID


def test_add_writes_linked_pages_and_deletes_audio(app):
    r = app.add(REAL_ID)
    assert r["status"] == "done", r
    assert r["sections"] == 28

    video_md = (app.config.wiki_dir / f"{r['page']}.md").read_text()
    assert video_md.startswith("---\ntitle: ")
    assert '"video_id": ' not in video_md and f'video_id: "{REAL_ID}"' in video_md
    assert "https://www.youtube.com/watch?v=lHmZoRHMZyM&t=1054s" in video_md   # Flux 3 chapter

    secs = sorted((app.config.wiki_dir / "sections" / REAL_ID).glob("*.md"))
    assert len(secs) == 28
    flux = next(p for p in secs if "flux-3" in p.name).read_text()
    assert f"[[{r['page']}|" in flux                       # links up to the video
    assert "https://bfl.ai/models/flux-3-image" in flux     # link from the description
    assert "prev: [[sections/" in flux and "next: [[sections/" in flux
    assert f"[[sections/{REAL_ID}/14-flux-3\\|Flux 3]]" in video_md  # and the video links down

    luma = next(p for p in secs if p.name.endswith("-luma.md")).read_text()
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
    assert all(h["title"] != "Luma" for h in hits)
    assert any(h["title"] == "Luma" for h in app.search("Luma", include_sponsor=True)["hits"])
    world = app.search("text to world model consistent", kind="section")["hits"]
    assert world[0]["title"] == "Inspatio World 1.5"


def test_channel_check_backfill_and_run(app):
    r = app.channel_add("https://www.youtube.com/@theAIsearch")
    queued = r["check"]["channels"]["AI Search"]["queued"]
    assert set(queued) == {REAL_ID, "aaaaaaaaaaa", "bbbbbbbbbbb"}    # the Short is filtered
    assert app.check()["channels"]["AI Search"]["queued"] == []      # nothing new the second time
    out = app.run(limit=2)
    assert [p["status"] for p in out["processed"]] == ["done", "done"]
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
    app.__dict__["embedder"] = create("embedder", {"type": "hashing", "dim": 128})
    assert app.search("Flux")["hits"]          # BM25 still works before the reindex
    n = app.reindex()["chunks_embedded"]
    assert n > 0
    stats = app.index.stats()["vectors_by_embedder"]
    assert set(stats) == {old, "hashing:128"}


@register("llm", "scripted")
class ScriptedLLM(LLM):
    model = "test"

    def complete(self, prompt, system=None, **kw):
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
    r = app.add(REAL_ID)
    flux = app.show(f"{REAL_ID}#14")["content"]
    assert "About Flux 3." in flux and "- Flux 3 was covered" in flux and '"flux-3"' in flux
    assert "sponsor" in app.show(f"{REAL_ID}#10")["content"]
    assert "Weekly AI news." in app.show(REAL_ID)["content"]
    ans = app.ask("how big is flux 3")
    assert "12B" in ans["answer"] and ans["sources"][0]["title"] == "Flux 3"


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


def test_unreachable_llm_fails_video_instead_of_caching_fallback(app):
    from agentwiki.registry import create
    app.__dict__["llm"] = create("llm", {"type": "ollama", "model": "x", "host": "http://127.0.0.1:9"})
    app.__dict__["enricher"] = create("enricher", {"type": "llm"}, app)
    r = app.add(REAL_ID)
    assert r["status"] == "failed" and "LLMUnavailable" in r["error"]
    assert not (app.config.data_dir / "raw" / REAL_ID / "enrichment.json").exists()
    assert (app.config.data_dir / "raw" / REAL_ID / "transcript.json").exists()
