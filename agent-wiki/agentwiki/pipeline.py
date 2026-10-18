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

    def _dir(self, video_id: str) -> Path:
        video_dir = self.raw_dir / video_id
        video_dir.mkdir(parents=True, exist_ok=True)
        return video_dir

    def _load(self, video_id: str, stage: str):
        cache_path = self.raw_dir / video_id / CACHE_FILES[stage]
        return json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else None

    def _save(self, video_id: str, stage: str, data) -> None:
        cache_path = self._dir(video_id) / CACHE_FILES[stage]
        temp_path = cache_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        temp_path.replace(cache_path)

    def invalidate(self, video_id: str, from_stage: str) -> None:
        if from_stage not in STAGES:
            raise ValueError(f"stage must be one of {STAGES}")
        for stage_name in STAGES[STAGES.index(from_stage):]:
            if stage_name in CACHE_FILES:
                (self.raw_dir / video_id / CACHE_FILES[stage_name]).unlink(missing_ok=True)

    def cached(self, video_id: str) -> tuple[VideoInfo | None, Transcript | None]:
        cached_info, cached_transcript = self._load(video_id, "info"), self._load(video_id, "transcript")
        return (VideoInfo.from_dict(cached_info) if cached_info else None,
                Transcript.from_dict(cached_transcript) if cached_transcript else None)

    # ---- stages ------------------------------------------------------------

    def _info(self, video_id: str, refresh: bool = False) -> VideoInfo:
        cached = self._load(video_id, "info")
        if cached and not refresh:
            return VideoInfo.from_dict(cached)
        video_info = self.app.source.fetch_info(video_id)
        self._save(video_id, "info", video_info.to_dict())
        return video_info

    def _check_wanted(self, video_info: VideoInfo) -> None:
        ingest_config = self.app.config["ingest"]
        if ingest_config["skip_live"] and video_info.live_status in ("is_live", "is_upcoming"):
            raise Skip(f"live status {video_info.live_status}")
        if video_info.duration and video_info.duration < ingest_config["min_duration"]:
            raise Skip(f"shorter than {ingest_config['min_duration']}s")

    def _transcript(self, video_id: str, video_info: VideoInfo) -> tuple[VideoInfo, Transcript]:
        cached = self._load(video_id, "transcript")
        if cached:
            return video_info, Transcript.from_dict(cached)
        info_file = self.raw_dir / video_id / CACHE_FILES["info"]
        if time.time() - info_file.stat().st_mtime > INFO_MAX_AGE:
            # Only caption URLs expire; titles, chapters and descriptions do not.
            # If the refresh fails (rate limit), carry on with the cached copy:
            # audio from a local folder or a fresh download does not need it.
            try:
                video_info = self._info(video_id, refresh=True)
            except Exception as error:
                log.warning("%s: could not refresh metadata, using the cached copy: %s", video_id, error)
        transcriber = self.app.transcriber
        audio_dir = self.tmp_dir / video_id
        audio = None
        try:
            if transcriber.needs_audio:
                audio = self.app.source.download_audio(video_id, audio_dir)
            transcript = transcriber.transcribe(video_info, audio)
        finally:
            # The audio is never kept unless asked: it is the only large file.
            if audio and self.app.config["ingest"]["keep_audio"]:
                keep = self._dir(video_id) / audio.name
                shutil.move(str(audio), keep)
            shutil.rmtree(audio_dir, ignore_errors=True)
        if not transcript.segments:
            raise RuntimeError("transcript is empty")
        self._save(video_id, "transcript", transcript.to_dict())
        return video_info, transcript

    def _sections(self, video_id: str, video_info: VideoInfo, transcript: Transcript) -> list[Section]:
        cached = self._load(video_id, "sections")
        if cached is not None:
            return [Section.from_dict(section) for section in cached]
        sections = self.app.segmenter.split(video_info, transcript)
        self._save(video_id, "sections", [section.to_dict() for section in sections])
        return sections

    def _enrich(self, video_id: str, video_info: VideoInfo, transcript: Transcript,
                sections: list[Section]) -> Enrichment:
        cached = self._load(video_id, "enrich")
        if cached is None:
            enricher = self.app.enricher
            per_section, degraded = [], False
            for section in sections:
                enrichment = enricher.enrich_section(video_info, section)
                section.summary, section.tags, section.facts = (
                    enrichment.summary, enrichment.tags, enrichment.facts)
                per_section.append({"summary": enrichment.summary, "tags": enrichment.tags,
                                    "facts": enrichment.facts})
                degraded |= enrichment.degraded
            video_enrichment = enricher.enrich_video(video_info, sections, transcript.text)
            # degraded: the LLM was unreachable and a fallback filled in; `run`
            # redoes this stage once the LLM is back.
            cached = {"model": enricher.name, "degraded": degraded or video_enrichment.degraded,
                      "sections": per_section,
                      "video": {"summary": video_enrichment.summary, "tags": video_enrichment.tags}}
            self._save(video_id, "enrich", cached)
        for section, section_data in zip(sections, cached["sections"]):
            section.summary, section.tags, section.facts = (
                section_data["summary"], section_data["tags"], section_data["facts"])
        video_data = cached["video"]
        return Enrichment(summary=video_data["summary"], tags=video_data["tags"], model=cached["model"])

    def _index_docs(self, video_info: VideoInfo, sections: list[Section],
                    video_enrichment: Enrichment, video_page_path: str) -> list[IndexDoc]:
        writer = self.app.writer
        chapters = "\n".join(f"- {section.title}" for section in sections)
        docs = [IndexDoc(
            doc_id=video_info.video_id, kind="video", video_id=video_info.video_id, title=video_info.title,
            path=video_page_path, url=video_info.url, channel=video_info.channel,
            published=video_info.published, tags=video_enrichment.tags,
            text=(f"{video_info.title}\n\n{video_enrichment.summary}\n\nSections:\n{chapters}"
                  f"\n\n{video_info.description}"))]
        for section in sections:
            facts = "\n".join(f"- {fact}" for fact in section.facts)
            links = " ".join(link.label for link in section.links)
            docs.append(IndexDoc(
                doc_id=f"{video_info.video_id}#{section.index}", kind="section", video_id=video_info.video_id,
                title=section.title, path=writer.section_path(video_info, section),
                url=video_info.timestamp_url(section.start),
                channel=video_info.channel, published=video_info.published, tags=section.tags,
                is_sponsor=section.is_sponsor,
                text=f"{section.title}. {links}\n\n{section.summary}\n\n{facts}\n\n{section.text}".strip()))
        return docs

    # ---- driver ------------------------------------------------------------

    def process(self, video_id: str, on_stage: Callable[[str], None] | None = None) -> dict:
        def stage(name):
            if on_stage:
                on_stage(name)
            log.info("%s: %s", video_id, name)

        stage("info")
        video_info = self._info(video_id)
        self._check_wanted(video_info)
        stage("transcript")
        video_info, transcript = self._transcript(video_id, video_info)
        stage("sections")
        sections = self._sections(video_id, video_info, transcript)
        stage("enrich")
        video_enrichment = self._enrich(video_id, video_info, transcript, sections)
        stage("pages")
        writer = self.app.writer
        video_page_path = writer.write_video(video_info, transcript, sections, video_enrichment,
                                             transcriber=transcript.model, enricher=video_enrichment.model)
        stage("index")
        index, embedder = self.app.index, self.app.embedder
        index.delete_video(video_id)
        index.upsert(self._index_docs(video_info, sections, video_enrichment, video_page_path), embedder)
        whole = self._whole_video_vector(video_info, transcript, embedder)
        self.app.refresh_channel_page(video_info.channel, video_info.channel_url)
        return {"video_id": video_id, "title": video_info.title, "page": video_page_path,
                "sections": len(sections),
                "published": video_info.published, "channel_id": video_info.channel_id, "whole_video": whole}

    def _whole_video_vector(self, video_info: VideoInfo, transcript: Transcript, embedder) -> str:
        """Encode the whole transcript in one pass when it fits the encoder's
        window (Qwen3-Embedding takes 32K tokens, about 3 hours of speech);
        otherwise average the section vectors. Returns which was used."""
        mode = self.app.config["index"].get("whole_video", "auto")
        text = f"{video_info.title}\n\n{transcript.text}"
        if mode != "mean":
            fits = embedder.count_tokens(text) <= embedder.max_tokens
            if fits or mode == "single":   # "single" lets the model truncate
                self.app.index.set_doc_vector(video_info.video_id, embedder,
                                              embedder.embed_documents([text])[0])
                return "single"
        self.app.index.pool_video(video_info.video_id, embedder)
        return "mean"
