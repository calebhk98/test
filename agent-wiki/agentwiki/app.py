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


def _is_block(error: Exception) -> bool:
    message = str(error)
    return any(sign in message for sign in _BLOCK_SIGNS)


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
        lock_file = open(path, "a+")
        try:
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise Busy("another agentwiki run is in progress") from None
            yield
        finally:
            lock_file.close()

    # ---- setup -------------------------------------------------------------

    def init(self) -> dict:
        self.config.wiki_dir.mkdir(parents=True, exist_ok=True)
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self.writer.write_agents_md()
        config_file = self.config.root / "config.toml"
        created = False
        if not config_file.exists():
            example = Path(__file__).resolve().parent.parent / "config.example.toml"
            config_file.write_text(example.read_text(encoding="utf-8") if example.exists() else "",
                                   encoding="utf-8")
            created = True
        return {"root": str(self.config.root), "config": str(config_file), "config_created": created}

    # ---- adding videos -----------------------------------------------------

    def has(self, url_or_id: str) -> dict:
        video_id = self.source.parse_video_id(url_or_id)
        if not video_id:
            return {"error": f"not a video URL or id: {url_or_id}"}
        row = self.catalog.get(video_id)
        return {"video_id": video_id, "known": row is not None, **({"status": row["status"]} if row else {})}

    def add(self, url_or_id: str, process: bool = True, force: bool = False) -> dict:
        video_id = self.source.parse_video_id(url_or_id)
        if not video_id:
            return {"error": f"not a video URL or id: {url_or_id}"}
        row = self.catalog.get(video_id)
        if row and row["status"] == "done" and not force:
            return {"video_id": video_id, "status": "done", "already_added": True, "page": row["page"]}
        self.catalog.enqueue(video_id, priority=PRIORITY_MANUAL)
        if force or (row and row["status"] in ("failed", "skipped")):
            self.catalog.requeue(video_id, PRIORITY_MANUAL)
        if not process:
            return {"video_id": video_id, "status": "queued"}
        try:
            with self.lock():
                return self._process_one(video_id)
        except Busy:
            return {"video_id": video_id, "status": "queued",
                    "note": "a run is in progress; this video is first in the queue"}
        except SourceBlocked as error:
            return {"video_id": video_id, "status": "queued", "blocked": True, "error": str(error)[:300],
                    "note": "YouTube is rate limiting or bot-checking; the video stays queued. "
                            "Wait, or set cookies / player_clients in [source]."}

    def _process_one(self, video_id: str) -> dict:
        self.catalog.update(video_id, status="processing", error=None)
        try:
            result = self.pipeline.process(
                video_id, on_stage=lambda stage_name: self.catalog.update(video_id, stage=stage_name))
        except Skip as error:
            self.catalog.update(video_id, status="skipped", error=str(error))
            return {"video_id": video_id, "status": "skipped", "reason": str(error)}
        except KeyboardInterrupt:
            self.catalog.update(video_id, status="queued")
            raise
        except Exception as error:
            if _is_block(error):
                # Not this video's fault: keep it queued, attempts unchanged.
                self.catalog.update(video_id, status="queued", error=f"blocked: {error}"[:500])
                raise SourceBlocked(str(error)) from error
            log.exception("failed: %s", video_id)
            self.catalog.mark_failed(video_id, f"{type(error).__name__}: {error}")
            return {"video_id": video_id, "status": "failed", "error": f"{type(error).__name__}: {error}"}
        self.catalog.update(video_id, status="done", stage="done", title=result["title"], page=result["page"],
                            published=result["published"], channel_id=result["channel_id"])
        return {**result, "status": "done"}

    # ---- channels ----------------------------------------------------------

    def channel_add(self, url: str, backfill: bool = False) -> dict:
        channel_ref = self.source.resolve_channel(url)
        new = self.catalog.add_channel(channel_ref.channel_id, channel_ref.name, channel_ref.url)
        out = {"channel_id": channel_ref.channel_id, "name": channel_ref.name, "url": channel_ref.url,
               "added": new}
        out["check"] = self.check(channel_ref.channel_id)
        if backfill:
            out["backfill"] = self.backfill(channel_ref.channel_id)
        return out

    def channel_remove(self, key: str) -> dict:
        return {"removed": self.catalog.remove_channel(key)}

    def channel_list(self) -> dict:
        return {"channels": self.catalog.channels()}

    def _resolve_channel(self, key: str) -> dict:
        channel_row = self.catalog.find_channel(key)
        if channel_row:
            return channel_row
        ref = self.source.resolve_channel(key)
        return {"channel_id": ref.channel_id, "name": ref.name, "url": ref.url}

    def _queue_entries(self, channel_row: dict, entries, priority: int) -> list[str]:
        ingest_config = self.config["ingest"]
        new = []
        for entry in entries:
            if ingest_config["skip_live"] and entry.live_status in ("is_live", "is_upcoming"):
                continue
            if entry.duration is not None and entry.duration < ingest_config["min_duration"]:
                continue
            if self.catalog.enqueue(entry.video_id, channel_id=channel_row["channel_id"], title=entry.title,
                                    priority=priority):
                new.append(entry.video_id)
        return new

    def check(self, channel: str | None = None) -> dict:
        """Queue uploads not seen before, from one or every subscribed channel."""
        channel_rows = [self._resolve_channel(channel)] if channel else \
                [channel_row for channel_row in self.catalog.channels() if channel_row["auto_check"]]
        out = {}
        for channel_row in channel_rows:
            try:
                entries = self.source.list_channel(channel_row["url"], self.config["ingest"]["check_recent"])
            except Exception as error:
                out[channel_row["name"]] = {"error": f"{type(error).__name__}: {error}"}
                continue
            out[channel_row["name"]] = {"queued": self._queue_entries(channel_row, entries, PRIORITY_NEW)}
            self.catalog.touch_channel(channel_row["channel_id"])
        return {"channels": out}

    def backfill(self, channel: str, limit: int | None = None) -> dict:
        """Queue a channel's whole upload list at low priority. `run` drains it over time."""
        channel_row = self._resolve_channel(channel)
        entries = self.source.list_channel(channel_row["url"], limit)
        new = self._queue_entries(channel_row, entries, PRIORITY_BACKFILL)
        return {"channel": channel_row["name"], "listed": len(entries), "queued": len(new)}

    # ---- processing --------------------------------------------------------

    def run(self, limit: int | None = None, max_minutes: float | None = None,
            sleep: float | None = None, check_first: bool = False) -> dict:
        ingest_config = self.config["ingest"]
        sleep = ingest_config["sleep_between"] if sleep is None else sleep
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
                row = self.catalog.next_queued(ingest_config["max_attempts"])
                if not row:
                    break
                if results and sleep:
                    time.sleep(sleep)
                try:
                    result = self._process_one(row["video_id"])
                except SourceBlocked as error:
                    stopped = f"source blocked, queue left as is: {str(error)[:200]}"
                    break
                results.append({key: result.get(key)
                                for key in ("video_id", "status", "title", "error", "reason")})
        out = {"processed": results, "queue": self.catalog.counts()}
        if upgraded:
            out["requeued_for_llm"] = upgraded
        if stopped:
            out["stopped"] = stopped
        return out

    def _requeue_degraded(self) -> int:
        """Videos enriched by a fallback while a part was unavailable (LLM down,
        model missing) get redone from the enrich stage, without downloading
        anything, once every part can run again."""
        if not self.enricher.upgrade_available():
            return 0
        requeued_count = 0
        for enrichment_file in (self.config.data_dir / "raw").glob("*/enrichment.json"):
            try:
                degraded = json.loads(enrichment_file.read_text(encoding="utf-8")).get("degraded")
            except (OSError, ValueError):
                continue
            video_id = enrichment_file.parent.name
            row = self.catalog.get(video_id)
            if degraded and row and row["status"] == "done":
                self.pipeline.invalidate(video_id, "enrich")
                self.catalog.requeue(video_id, PRIORITY_BACKFILL)
                requeued_count += 1
        return requeued_count

    def status(self, video_id: str | None = None, list_status: str | None = None,
               limit: int = 20) -> dict:
        if video_id:
            resolved_video_id = self.source.parse_video_id(video_id) or video_id
            return {"video": self.catalog.get(resolved_video_id)}
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
        for video_id in ids:
            self.pipeline.invalidate(video_id, from_stage)
            self.catalog.requeue(video_id)
        return {"requeued": len(ids), "from": from_stage,
                "next": "run `agentwiki run` to process them"}

    def reindex(self) -> dict:
        chunk_count = self.index.reembed(
            self.embedder, progress=lambda embedded, total: log.info("embedded %d/%d", embedded, total))
        # Whole-video vectors from the cached transcripts, single pass where it fits.
        modes = {"single": 0, "mean": 0}
        for video_id in self.catalog.all_ids("done"):
            video_info, transcript = self.pipeline.cached(video_id)
            if video_info and transcript:
                modes[self.pipeline._whole_video_vector(video_info, transcript, self.embedder)] += 1
        return {"embedder": self.embedder.name, "chunks_embedded": chunk_count, "whole_video": modes}

    def refresh_channel_page(self, channel: str, channel_url: str) -> None:
        rows = self.index.database.execute(
            "SELECT published, title, path FROM docs WHERE kind='video' AND channel=?",
            (channel,)).fetchall()
        self.writer.write_channel(channel, channel_url, [tuple(row) for row in rows])

    # ---- reading -----------------------------------------------------------

    def search(self, query: str, top_k: int | None = None, kind: str | None = None,
               tags: list[str] | None = None, channel: str | None = None,
               since: str | None = None, include_sponsor: bool = False) -> dict:
        search_filters = SearchFilters(
            kind=kind, channel=channel, tags=tags or [], since=since,
            exclude_sponsor=not include_sponsor and self.config["search"]["exclude_sponsor"])
        hits = self.index.search(query, self.embedder, top_k or self.config["search"]["k"], search_filters)
        return {"query": query, "hits": [hit.to_dict() for hit in hits]}

    def similar(self, video_id: str, top_k: int = 8) -> dict:
        resolved_video_id = self.source.parse_video_id(video_id) or video_id
        hits = self.index.similar(resolved_video_id, self.embedder, top_k)
        return {"video_id": resolved_video_id, "hits": [hit.to_dict() for hit in hits]}

    def show(self, key: str) -> dict:
        """A page by doc id (`<video_id>` or `<video_id>#<n>`), URL, or wiki path."""
        path = None
        row = self.index.database.execute("SELECT path FROM docs WHERE doc_id=?", (key,)).fetchone()
        if not row:
            resolved_video_id = self.source.parse_video_id(key)
            if resolved_video_id:
                row = self.index.database.execute("SELECT path FROM docs WHERE doc_id=?",
                                                  (resolved_video_id,)).fetchone()
        if row:
            path = row[0]
        else:
            path = key.removesuffix(".md")
        page_file = (self.config.wiki_dir / f"{path}.md").resolve()
        if not page_file.is_relative_to(self.config.wiki_dir.resolve()) or not page_file.exists():
            return {"error": f"no page for {key}"}
        return {"path": path, "content": page_file.read_text(encoding="utf-8")}

    def ask(self, question: str, top_k: int = 8, since: str | None = None,
            max_source_chars: int = 3000) -> dict:
        hits = self.index.search(question, self.embedder, top_k,
                                 SearchFilters(kind="section", since=since))
        sources = []
        for position, hit in enumerate(hits, 1):
            body = self.index.database.execute("SELECT body FROM docs WHERE doc_id=?",
                                               (hit.doc_id,)).fetchone()[0]
            video_title_row = self.index.database.execute("SELECT title FROM docs WHERE doc_id=?",
                                                          (hit.video_id,)).fetchone()
            sources.append({"n": position, "title": hit.title,
                            "video": video_title_row[0] if video_title_row else "",
                            "published": hit.published[:10], "url": hit.url, "path": hit.path,
                            "text": body[:max_source_chars]})
        if not self.llm.available:
            return {"question": question, "answer": None,
                    "note": "no LLM configured; read the sources", "sources": sources}
        context = "\n\n".join(f"[{source['n']}] {source['title']} (from \"{source['video']}\", "
                              f"{source['published']}, {source['url']})\n"
                              f"{source['text']}" for source in sources)
        answer = self.llm.complete(f"Sources:\n\n{context}\n\nQuestion: {question}", ASK_SYSTEM,
                                   max_tokens=1500)
        for source in sources:
            source.pop("text")
        return {"question": question, "answer": answer, "sources": sources}
