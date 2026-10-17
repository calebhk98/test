"""The facade every interface calls. Methods return plain dicts so the CLI can
print them as JSON and the MCP server can return them as tool results."""
from __future__ import annotations

import json
import logging
import os
import time
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path

from .catalog import PRIORITY_BACKFILL, PRIORITY_MANUAL, PRIORITY_NEW, Catalog
from .config import Config
from .index.base import SearchFilters
from .pipeline import STAGES, Pipeline, Skip
from .registry import create, load_plugins
from .wiki.writer import WikiWriter

log = logging.getLogger(__name__)


class Busy(RuntimeError):
    """Another process holds the run lock."""


class SourceBlocked(RuntimeError):
    """The site is rate limiting or bot-checking us. Every later video would fail
    the same way, so `run` stops and leaves the queue as it was."""


_BLOCK_SIGNS = ("HTTP Error 429", "Too Many Requests", "confirm you're not a bot",
                "confirm you\u2019re not a bot", "not a bot")


def _is_block(e: Exception) -> bool:
    s = str(e)
    return any(sign in s for sign in _BLOCK_SIGNS)


ASK_SYSTEM = ("You answer questions from a personal wiki of AI news videos. Use only the "
              "numbered sources. Cite them like [1]. Each source has a date: say when "
              "information is from, and prefer newer sources when they conflict. If the "
              "sources do not answer the question, say so.")


class App:
    def __init__(self, config: Config):
        self.config = config
        load_plugins(config["plugins"])
        self.catalog = Catalog(config.data_dir / "catalog.sqlite")
        self.writer = WikiWriter(config.wiki_dir)
        self.pipeline = Pipeline(self)

    @classmethod
    def open(cls, root=None, config_path=None) -> "App":
        return cls(Config.load(root, config_path))

    # Components are built on first use, so `search` never loads Whisper.
    @cached_property
    def source(self):
        return create("source", self.config["source"], self)

    @cached_property
    def transcriber(self):
        return create("transcriber", self.config["transcriber"], self)

    @cached_property
    def segmenter(self):
        return create("segmenter", self.config["segmenter"], self)

    @cached_property
    def llm(self):
        return create("llm", self.config["llm"], self)

    @cached_property
    def enricher(self):
        return create("enricher", self.config["enricher"], self)

    @cached_property
    def embedder(self):
        return create("embedder", self.config["embedder"], self)

    @cached_property
    def index(self):
        return create("index", self.config["index"], self)

    # ---- locking -----------------------------------------------------------

    @contextmanager
    def lock(self):
        path = self.config.data_dir / "run.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        f = open(path, "a+")
        try:
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise Busy("another agentwiki run is in progress") from None
            yield
        finally:
            f.close()

    # ---- setup -------------------------------------------------------------

    def init(self) -> dict:
        self.config.wiki_dir.mkdir(parents=True, exist_ok=True)
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self.writer.write_agents_md()
        cfg = self.config.root / "config.toml"
        created = False
        if not cfg.exists():
            example = Path(__file__).resolve().parent.parent / "config.example.toml"
            cfg.write_text(example.read_text(encoding="utf-8") if example.exists() else "",
                           encoding="utf-8")
            created = True
        return {"root": str(self.config.root), "config": str(cfg), "config_created": created}

    # ---- adding videos -----------------------------------------------------

    def has(self, url_or_id: str) -> dict:
        vid = self.source.parse_video_id(url_or_id)
        if not vid:
            return {"error": f"not a video URL or id: {url_or_id}"}
        row = self.catalog.get(vid)
        return {"video_id": vid, "known": row is not None, **({"status": row["status"]} if row else {})}

    def add(self, url_or_id: str, process: bool = True, force: bool = False) -> dict:
        vid = self.source.parse_video_id(url_or_id)
        if not vid:
            return {"error": f"not a video URL or id: {url_or_id}"}
        row = self.catalog.get(vid)
        if row and row["status"] == "done" and not force:
            return {"video_id": vid, "status": "done", "already_added": True, "page": row["page"]}
        self.catalog.enqueue(vid, priority=PRIORITY_MANUAL)
        if force or (row and row["status"] in ("failed", "skipped")):
            self.catalog.requeue(vid, PRIORITY_MANUAL)
        if not process:
            return {"video_id": vid, "status": "queued"}
        try:
            with self.lock():
                return self._process_one(vid)
        except Busy:
            return {"video_id": vid, "status": "queued",
                    "note": "a run is in progress; this video is first in the queue"}
        except SourceBlocked as e:
            return {"video_id": vid, "status": "queued", "blocked": True, "error": str(e)[:300],
                    "note": "YouTube is rate limiting or bot-checking; the video stays queued. "
                            "Wait, or set cookies / player_clients in [source]."}

    def _process_one(self, vid: str) -> dict:
        self.catalog.update(vid, status="processing", error=None)
        try:
            r = self.pipeline.process(vid, on_stage=lambda s: self.catalog.update(vid, stage=s))
        except Skip as e:
            self.catalog.update(vid, status="skipped", error=str(e))
            return {"video_id": vid, "status": "skipped", "reason": str(e)}
        except KeyboardInterrupt:
            self.catalog.update(vid, status="queued")
            raise
        except Exception as e:
            if _is_block(e):
                # Not this video's fault: keep it queued, attempts unchanged.
                self.catalog.update(vid, status="queued", error=f"blocked: {e}"[:500])
                raise SourceBlocked(str(e)) from e
            log.exception("failed: %s", vid)
            self.catalog.mark_failed(vid, f"{type(e).__name__}: {e}")
            return {"video_id": vid, "status": "failed", "error": f"{type(e).__name__}: {e}"}
        self.catalog.update(vid, status="done", stage="done", title=r["title"], page=r["page"],
                            published=r["published"], channel_id=r["channel_id"])
        return {**r, "status": "done"}

    # ---- channels ----------------------------------------------------------

    def channel_add(self, url: str, backfill: bool = False) -> dict:
        ch = self.source.resolve_channel(url)
        new = self.catalog.add_channel(ch.channel_id, ch.name, ch.url)
        out = {"channel_id": ch.channel_id, "name": ch.name, "url": ch.url, "added": new}
        out["check"] = self.check(ch.channel_id)
        if backfill:
            out["backfill"] = self.backfill(ch.channel_id)
        return out

    def channel_remove(self, key: str) -> dict:
        return {"removed": self.catalog.remove_channel(key)}

    def channel_list(self) -> dict:
        return {"channels": self.catalog.channels()}

    def _resolve_channel(self, key: str) -> dict:
        ch = self.catalog.find_channel(key)
        if ch:
            return ch
        ref = self.source.resolve_channel(key)
        return {"channel_id": ref.channel_id, "name": ref.name, "url": ref.url}

    def _queue_entries(self, ch: dict, entries, priority: int) -> list[str]:
        cfg = self.config["ingest"]
        new = []
        for e in entries:
            if cfg["skip_live"] and e.live_status in ("is_live", "is_upcoming"):
                continue
            if e.duration is not None and e.duration < cfg["min_duration"]:
                continue
            if self.catalog.enqueue(e.video_id, channel_id=ch["channel_id"], title=e.title,
                                    priority=priority):
                new.append(e.video_id)
        return new

    def check(self, channel: str | None = None) -> dict:
        """Queue uploads not seen before, from one or every subscribed channel."""
        chans = [self._resolve_channel(channel)] if channel else \
                [c for c in self.catalog.channels() if c["auto_check"]]
        out = {}
        for ch in chans:
            try:
                entries = self.source.list_channel(ch["url"], self.config["ingest"]["check_recent"])
            except Exception as e:
                out[ch["name"]] = {"error": f"{type(e).__name__}: {e}"}
                continue
            out[ch["name"]] = {"queued": self._queue_entries(ch, entries, PRIORITY_NEW)}
            self.catalog.touch_channel(ch["channel_id"])
        return {"channels": out}

    def backfill(self, channel: str, limit: int | None = None) -> dict:
        """Queue a channel's whole upload list at low priority. `run` drains it over time."""
        ch = self._resolve_channel(channel)
        entries = self.source.list_channel(ch["url"], limit)
        new = self._queue_entries(ch, entries, PRIORITY_BACKFILL)
        return {"channel": ch["name"], "listed": len(entries), "queued": len(new)}

    # ---- processing --------------------------------------------------------

    def run(self, limit: int | None = None, max_minutes: float | None = None,
            sleep: float | None = None, check_first: bool = False) -> dict:
        cfg = self.config["ingest"]
        sleep = cfg["sleep_between"] if sleep is None else sleep
        deadline = time.time() + max_minutes * 60 if max_minutes else None
        results, stopped = [], None
        with self.lock():
            self.catalog.reset_stuck()
            upgraded = self._requeue_degraded()
            if check_first:
                self.check()
            while limit is None or len(results) < limit:
                if deadline and time.time() > deadline:
                    break
                row = self.catalog.next_queued(cfg["max_attempts"])
                if not row:
                    break
                if results and sleep:
                    time.sleep(sleep)
                try:
                    r = self._process_one(row["video_id"])
                except SourceBlocked as e:
                    stopped = f"source blocked, queue left as is: {str(e)[:200]}"
                    break
                results.append({k: r.get(k) for k in ("video_id", "status", "title", "error", "reason")})
        out = {"processed": results, "queue": self.catalog.counts()}
        if upgraded:
            out["requeued_for_llm"] = upgraded
        if stopped:
            out["stopped"] = stopped
        return out

    def _requeue_degraded(self) -> int:
        """Videos enriched by the fallback while the LLM was down get redone
        from the enrich stage (no download) once the LLM answers again."""
        llm = getattr(self.enricher, "llm", None)
        if llm is None or not llm.available:
            return 0
        n = 0
        for f in (self.config.data_dir / "raw").glob("*/enrichment.json"):
            try:
                degraded = json.loads(f.read_text(encoding="utf-8")).get("degraded")
            except (OSError, ValueError):
                continue
            vid = f.parent.name
            row = self.catalog.get(vid)
            if degraded and row and row["status"] == "done":
                self.pipeline.invalidate(vid, "enrich")
                self.catalog.requeue(vid, PRIORITY_BACKFILL)
                n += 1
        return n

    def status(self, video_id: str | None = None, list_status: str | None = None,
               limit: int = 20) -> dict:
        if video_id:
            vid = self.source.parse_video_id(video_id) or video_id
            return {"video": self.catalog.get(vid)}
        from . import hardware
        out = {"queue": self.catalog.counts(), "channels": len(self.catalog.channels()),
               "index": self.index.stats(), "embedder": self.embedder.name,
               "hardware": hardware.detect().to_dict()}
        if list_status:
            out["videos"] = self.catalog.list(list_status, limit)
        return out

    def reprocess(self, ids: list[str] | None, from_stage: str = "enrich") -> dict:
        if from_stage not in STAGES:
            return {"error": f"stage must be one of {STAGES}"}
        ids = ids or self.catalog.all_ids("done")
        for vid in ids:
            self.pipeline.invalidate(vid, from_stage)
            self.catalog.requeue(vid)
        return {"requeued": len(ids), "from": from_stage,
                "next": "run `agentwiki run` to process them"}

    def reindex(self) -> dict:
        n = self.index.reembed(self.embedder,
                               progress=lambda a, b: log.info("embedded %d/%d", a, b))
        # Whole-video vectors from the cached transcripts, single pass where it fits.
        modes = {"single": 0, "mean": 0}
        for vid in self.catalog.all_ids("done"):
            info, tr = self.pipeline.cached(vid)
            if info and tr:
                modes[self.pipeline._whole_video_vector(info, tr, self.embedder)] += 1
        return {"embedder": self.embedder.name, "chunks_embedded": n, "whole_video": modes}

    def refresh_channel_page(self, channel: str, channel_url: str) -> None:
        rows = self.index.db.execute(
            "SELECT published, title, path FROM docs WHERE kind='video' AND channel=?",
            (channel,)).fetchall()
        self.writer.write_channel(channel, channel_url, [tuple(r) for r in rows])

    # ---- reading -----------------------------------------------------------

    def search(self, query: str, k: int | None = None, kind: str | None = None,
               tags: list[str] | None = None, channel: str | None = None,
               since: str | None = None, include_sponsor: bool = False) -> dict:
        f = SearchFilters(kind=kind, channel=channel, tags=tags or [], since=since,
                          exclude_sponsor=not include_sponsor and self.config["search"]["exclude_sponsor"])
        hits = self.index.search(query, self.embedder, k or self.config["search"]["k"], f)
        return {"query": query, "hits": [h.to_dict() for h in hits]}

    def similar(self, video_id: str, k: int = 8) -> dict:
        vid = self.source.parse_video_id(video_id) or video_id
        return {"video_id": vid, "hits": [h.to_dict() for h in self.index.similar(vid, self.embedder, k)]}

    def show(self, key: str) -> dict:
        """A page by doc id (`<video_id>` or `<video_id>#<n>`), URL, or wiki path."""
        path = None
        row = self.index.db.execute("SELECT path FROM docs WHERE doc_id=?", (key,)).fetchone()
        if not row:
            vid = self.source.parse_video_id(key)
            if vid:
                row = self.index.db.execute("SELECT path FROM docs WHERE doc_id=?", (vid,)).fetchone()
        if row:
            path = row[0]
        else:
            path = key.removesuffix(".md")
        p = (self.config.wiki_dir / f"{path}.md").resolve()
        if not p.is_relative_to(self.config.wiki_dir.resolve()) or not p.exists():
            return {"error": f"no page for {key}"}
        return {"path": path, "content": p.read_text(encoding="utf-8")}

    def ask(self, question: str, k: int = 8, since: str | None = None,
            max_source_chars: int = 3000) -> dict:
        hits = self.index.search(question, self.embedder, k,
                                 SearchFilters(kind="section", since=since))
        sources = []
        for i, h in enumerate(hits, 1):
            body = self.index.db.execute("SELECT body FROM docs WHERE doc_id=?",
                                         (h.doc_id,)).fetchone()[0]
            vt = self.index.db.execute("SELECT title FROM docs WHERE doc_id=?",
                                       (h.video_id,)).fetchone()
            sources.append({"n": i, "title": h.title, "video": vt[0] if vt else "",
                            "published": h.published[:10], "url": h.url, "path": h.path,
                            "text": body[:max_source_chars]})
        if not self.llm.available:
            return {"question": question, "answer": None,
                    "note": "no LLM configured; read the sources", "sources": sources}
        ctx = "\n\n".join(f"[{s['n']}] {s['title']} (from \"{s['video']}\", {s['published']}, {s['url']})\n"
                          f"{s['text']}" for s in sources)
        answer = self.llm.complete(f"Sources:\n\n{ctx}\n\nQuestion: {question}", ASK_SYSTEM,
                                   max_tokens=1500)
        for s in sources:
            s.pop("text")
        return {"question": question, "answer": answer, "sources": sources}
