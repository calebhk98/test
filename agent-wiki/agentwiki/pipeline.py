"""Run one video through every stage, caching each so a rerun resumes."""
from __future__ import annotations

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Callable

from .index.base import IndexDoc
from .models import Enrichment, Section, Transcript, VideoInfo

log = logging.getLogger(__name__)

STAGES = ["info", "transcript", "sections", "enrich", "pages", "index"]
CACHE_FILES = {"info": "info.json", "transcript": "transcript.json",
               "sections": "sections.json", "enrich": "enrichment.json"}
# Caption and audio URLs inside info.json expire after a few hours.
INFO_MAX_AGE = 3 * 3600


class Skip(Exception):
    """The video is valid but should not be in the wiki (Short, live stream...)."""


class Pipeline:
    def __init__(self, app):
        self.app = app
        self.raw_dir: Path = app.config.data_dir / "raw"
        self.tmp_dir: Path = app.config.data_dir / "tmp"

    # ---- cache helpers -----------------------------------------------------

    def _dir(self, vid: str) -> Path:
        d = self.raw_dir / vid
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _load(self, vid: str, stage: str):
        p = self.raw_dir / vid / CACHE_FILES[stage]
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def _save(self, vid: str, stage: str, data) -> None:
        p = self._dir(vid) / CACHE_FILES[stage]
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(p)

    def invalidate(self, vid: str, from_stage: str) -> None:
        if from_stage not in STAGES:
            raise ValueError(f"stage must be one of {STAGES}")
        for st in STAGES[STAGES.index(from_stage):]:
            if st in CACHE_FILES:
                (self.raw_dir / vid / CACHE_FILES[st]).unlink(missing_ok=True)

    # ---- stages ------------------------------------------------------------

    def _info(self, vid: str, refresh: bool = False) -> VideoInfo:
        cached = self._load(vid, "info")
        if cached and not refresh:
            return VideoInfo.from_dict(cached)
        info = self.app.source.fetch_info(vid)
        self._save(vid, "info", info.to_dict())
        return info

    def _check_wanted(self, info: VideoInfo) -> None:
        cfg = self.app.config["ingest"]
        if cfg["skip_live"] and info.live_status in ("is_live", "is_upcoming"):
            raise Skip(f"live status {info.live_status}")
        if info.duration and info.duration < cfg["min_duration"]:
            raise Skip(f"shorter than {cfg['min_duration']}s")

    def _transcript(self, vid: str, info: VideoInfo) -> tuple[VideoInfo, Transcript]:
        cached = self._load(vid, "transcript")
        if cached:
            return info, Transcript.from_dict(cached)
        info_file = self.raw_dir / vid / CACHE_FILES["info"]
        if time.time() - info_file.stat().st_mtime > INFO_MAX_AGE:
            info = self._info(vid, refresh=True)
        t = self.app.transcriber
        audio_dir = self.tmp_dir / vid
        audio = None
        try:
            if t.needs_audio:
                audio = self.app.source.download_audio(vid, audio_dir)
            transcript = t.transcribe(info, audio)
        finally:
            # The audio is never kept unless asked: it is the only large file.
            if audio and self.app.config["ingest"]["keep_audio"]:
                keep = self._dir(vid) / audio.name
                shutil.move(str(audio), keep)
            shutil.rmtree(audio_dir, ignore_errors=True)
        if not transcript.segments:
            raise RuntimeError("transcript is empty")
        self._save(vid, "transcript", transcript.to_dict())
        return info, transcript

    def _sections(self, vid: str, info: VideoInfo, transcript: Transcript) -> list[Section]:
        cached = self._load(vid, "sections")
        if cached is not None:
            return [Section.from_dict(s) for s in cached]
        sections = self.app.segmenter.split(info, transcript)
        self._save(vid, "sections", [s.to_dict() for s in sections])
        return sections

    def _enrich(self, vid: str, info: VideoInfo, transcript: Transcript,
                sections: list[Section]) -> Enrichment:
        cached = self._load(vid, "enrich")
        if cached is None:
            enr = self.app.enricher
            per_section = []
            for s in sections:
                e = enr.enrich_section(info, s)
                s.summary, s.tags, s.facts = e.summary, e.tags, e.facts
                per_section.append({"summary": e.summary, "tags": e.tags, "facts": e.facts})
            v = enr.enrich_video(info, sections, transcript.text)
            cached = {"model": enr.name, "sections": per_section,
                      "video": {"summary": v.summary, "tags": v.tags}}
            self._save(vid, "enrich", cached)
        for s, e in zip(sections, cached["sections"]):
            s.summary, s.tags, s.facts = e["summary"], e["tags"], e["facts"]
        v = cached["video"]
        return Enrichment(summary=v["summary"], tags=v["tags"], model=cached["model"])

    def _index_docs(self, info: VideoInfo, sections: list[Section], ve: Enrichment,
                    vpath: str) -> list[IndexDoc]:
        w = self.app.writer
        chapters = "\n".join(f"- {s.title}" for s in sections)
        docs = [IndexDoc(
            doc_id=info.video_id, kind="video", video_id=info.video_id, title=info.title,
            path=vpath, url=info.url, channel=info.channel, published=info.published,
            tags=ve.tags, text=f"{info.title}\n\n{ve.summary}\n\nSections:\n{chapters}\n\n{info.description}")]
        for s in sections:
            facts = "\n".join(f"- {f}" for f in s.facts)
            links = " ".join(l.label for l in s.links)
            docs.append(IndexDoc(
                doc_id=f"{info.video_id}#{s.index}", kind="section", video_id=info.video_id,
                title=s.title, path=w.section_path(info, s), url=info.timestamp_url(s.start),
                channel=info.channel, published=info.published, tags=s.tags,
                is_sponsor=s.is_sponsor,
                text=f"{s.title}. {links}\n\n{s.summary}\n\n{facts}\n\n{s.text}".strip()))
        return docs

    # ---- driver ------------------------------------------------------------

    def process(self, vid: str, on_stage: Callable[[str], None] | None = None) -> dict:
        def stage(name):
            if on_stage:
                on_stage(name)
            log.info("%s: %s", vid, name)

        stage("info")
        info = self._info(vid)
        self._check_wanted(info)
        stage("transcript")
        info, transcript = self._transcript(vid, info)
        stage("sections")
        sections = self._sections(vid, info, transcript)
        stage("enrich")
        ve = self._enrich(vid, info, transcript, sections)
        stage("pages")
        w = self.app.writer
        vpath = w.write_video(info, transcript, sections, ve,
                              transcriber=transcript.model, enricher=ve.model)
        stage("index")
        idx, emb = self.app.index, self.app.embedder
        idx.delete_video(vid)
        idx.upsert(self._index_docs(info, sections, ve, vpath), emb)
        idx.pool_video(vid, emb)
        self.app.refresh_channel_page(info.channel, info.channel_url)
        return {"video_id": vid, "title": info.title, "page": vpath, "sections": len(sections),
                "published": info.published, "channel_id": info.channel_id}
