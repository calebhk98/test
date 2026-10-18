"""SQLite index: FTS5 for keywords, numpy cosine for vectors, merged with RRF."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import numpy as np

from ..embed.base import Embedder, normalize
from ..models import SearchHit
from ..registry import register
from .base import IndexDoc, SearchFilters, VectorIndex

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
  doc_id TEXT PRIMARY KEY, kind TEXT, video_id TEXT, channel TEXT, path TEXT, title TEXT,
  url TEXT, published TEXT, tags TEXT, is_sponsor INTEGER, body TEXT);
CREATE INDEX IF NOT EXISTS docs_video ON docs(video_id);
CREATE TABLE IF NOT EXISTS chunks (
  chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT, ord INTEGER, text TEXT);
CREATE INDEX IF NOT EXISTS chunks_doc ON chunks(doc_id);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  title, text, chunk_id UNINDEXED, tokenize='porter unicode61');
CREATE TABLE IF NOT EXISTS vectors (
  chunk_id INTEGER, embedder TEXT, vec BLOB, PRIMARY KEY (chunk_id, embedder));
CREATE TABLE IF NOT EXISTS doc_vectors (
  doc_id TEXT, embedder TEXT, vec BLOB, PRIMARY KEY (doc_id, embedder));
"""

RRF_K = 60


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split on sentence ends where possible, else on whitespace."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= size:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind(". "), window.rfind("? "), window.rfind("! "))
            if cut < size // 2:
                cut = window.rfind(" ")
            if cut > size // 4:
                end = start + cut + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        # Do not start a chunk mid-word.
        space_position = text.find(" ", start)
        if 0 <= space_position < end:
            start = space_position + 1
    return [chunk for chunk in chunks if chunk]


def fts_query(query_text: str) -> str:
    terms = re.findall(r"\w+", query_text.lower())
    return " OR ".join(f'"{term}"' for term in terms)


@register("index", "sqlite")
class SQLiteIndex(VectorIndex):
    def __init__(self, path: str | Path, chunk_chars: int | str = "auto", chunk_overlap: int = 200,
                 candidates: int = 200, whole_video: str = "auto"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.database = sqlite3.connect(self.path)
        self.database.executescript(SCHEMA)
        self.chunk_chars = chunk_chars
        self.chunk_overlap = chunk_overlap
        self.candidates = candidates
        self._cache: dict[str, tuple[int, np.ndarray, np.ndarray, list[str]]] = {}

    @classmethod
    def from_config(cls, params, app=None):
        params = dict(params)
        params.setdefault("path", app.config.data_dir / "index.sqlite")
        return cls(**params)

    # ---- writing -----------------------------------------------------------

    def _delete_docs(self, where: str, args: tuple) -> None:
        ids = [row[0] for row in self.database.execute(f"SELECT doc_id FROM docs WHERE {where}", args)]
        for doc_id in ids:
            chunk_ids = [row[0] for row in self.database.execute(
                "SELECT chunk_id FROM chunks WHERE doc_id=?", (doc_id,))]
            self.database.executemany("DELETE FROM vectors WHERE chunk_id=?",
                                      [(chunk_id,) for chunk_id in chunk_ids])
            self.database.executemany("DELETE FROM chunks_fts WHERE chunk_id=?",
                                      [(chunk_id,) for chunk_id in chunk_ids])
            self.database.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
            self.database.execute("DELETE FROM doc_vectors WHERE doc_id=?", (doc_id,))
            self.database.execute("DELETE FROM docs WHERE doc_id=?", (doc_id,))

    def upsert(self, docs: list[IndexDoc], embedder: Embedder) -> None:
        pending: list[tuple[int, str]] = []
        with self.database:
            for doc in docs:
                self._delete_docs("doc_id=?", (doc.doc_id,))
                self.database.execute(
                    "INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (doc.doc_id, doc.kind, doc.video_id, doc.channel, doc.path, doc.title, doc.url,
                     doc.published, " " + " ".join(doc.tags) + " ", int(doc.is_sponsor), doc.text))
                chunks = chunk_text(doc.text, self._chunk_size(embedder), self.chunk_overlap)
                for chunk_index, chunk in enumerate(chunks):
                    chunk_id = self.database.execute("INSERT INTO chunks (doc_id, ord, text) VALUES (?,?,?)",
                                                     (doc.doc_id, chunk_index, chunk)).lastrowid
                    self.database.execute("INSERT INTO chunks_fts (title, text, chunk_id) VALUES (?,?,?)",
                                          (doc.title, chunk, chunk_id))
                    pending.append((chunk_id, f"{doc.title}\n{chunk}"))
            if pending:
                vectors = embedder.embed_documents([text for _, text in pending])
                self.database.executemany(
                    "INSERT OR REPLACE INTO vectors VALUES (?,?,?)",
                    [(chunk_id, embedder.name, vector.astype(np.float32).tobytes())
                     for (chunk_id, _), vector in zip(pending, vectors)])

    def _chunk_size(self, embedder: Embedder) -> int:
        """Chunks sized to the encoder: one 2-3 minute section stays whole on
        long-context models, and nothing gets truncated on short ones. Capped
        at ~1000 tokens because longer chunks blur what a hit is about."""
        if self.chunk_chars != "auto":
            return int(self.chunk_chars)
        return max(400, min(4000, int(embedder.max_tokens * 3)))

    def reembed(self, embedder: Embedder, batch: int = 256, progress=None) -> int:
        """Embed every chunk that has no vector for this embedder."""
        rows = self.database.execute(
            "SELECT c.chunk_id, d.title, c.text FROM chunks c JOIN docs d USING(doc_id) "
            "WHERE c.chunk_id NOT IN (SELECT chunk_id FROM vectors WHERE embedder=?)",
            (embedder.name,)).fetchall()
        for start in range(0, len(rows), batch):
            batch_rows = rows[start:start + batch]
            vectors = embedder.embed_documents([f"{title}\n{text}" for _, title, text in batch_rows])
            with self.database:
                self.database.executemany("INSERT OR REPLACE INTO vectors VALUES (?,?,?)",
                                          [(chunk_id, embedder.name, vector.tobytes())
                                           for (chunk_id, _, _), vector in zip(batch_rows, vectors)])
            if progress:
                progress(min(start + batch, len(rows)), len(rows))
        for (video_id,) in self.database.execute("SELECT doc_id FROM docs WHERE kind='video'").fetchall():
            self.pool_video(video_id, embedder)
        return len(rows)

    def delete_video(self, video_id: str) -> None:
        with self.database:
            self._delete_docs("video_id=?", (video_id,))

    def pool_video(self, video_id: str, embedder: Embedder) -> None:
        rows = self.database.execute(
            "SELECT v.vec FROM vectors v JOIN chunks c USING(chunk_id) JOIN docs d USING(doc_id) "
            "WHERE d.video_id=? AND d.kind='section' AND v.embedder=?",
            (video_id, embedder.name)).fetchall()
        if not rows:
            return
        mean = normalize(np.mean([np.frombuffer(row[0], np.float32) for row in rows], axis=0))
        self.set_doc_vector(video_id, embedder, mean)

    def set_doc_vector(self, doc_id: str, embedder: Embedder, vector) -> None:
        with self.database:
            self.database.execute("INSERT OR REPLACE INTO doc_vectors VALUES (?,?,?)",
                                  (doc_id, embedder.name, normalize(vector).astype(np.float32).tobytes()))

    # ---- reading -----------------------------------------------------------

    def _allowed_docs(self, filters: SearchFilters) -> set[str] | None:
        where, args = [], []
        if filters.kind:
            where.append("kind=?"); args.append(filters.kind)
        if filters.channel:
            where.append("(channel=? OR channel LIKE ?)"); args += [filters.channel, f"%{filters.channel}%"]
        if filters.since:
            where.append("published>=?"); args.append(filters.since)
        if filters.exclude_sponsor:
            where.append("is_sponsor=0")
        for tag in filters.tags:
            where.append("tags LIKE ?"); args.append(f"% {tag} %")
        if not where:
            return None
        return {row[0] for row in self.database.execute(
            f"SELECT doc_id FROM docs WHERE {' AND '.join(where)}", args)}

    def _matrix(self, embedder: Embedder):
        version = self.database.execute("PRAGMA data_version").fetchone()[0]
        total = self.database.total_changes
        key = embedder.name
        cached = self._cache.get(key)
        if cached and cached[0] == (version, total):
            return cached[1], cached[2], cached[3]
        rows = self.database.execute(
            "SELECT v.chunk_id, c.doc_id, v.vec FROM vectors v JOIN chunks c USING(chunk_id) "
            "WHERE v.embedder=?", (key,)).fetchall()
        ids = np.array([row[0] for row in rows], dtype=np.int64)
        docs = [row[1] for row in rows]
        matrix = (np.vstack([np.frombuffer(row[2], np.float32) for row in rows]) if rows
                  else np.zeros((0, 1), np.float32))
        self._cache[key] = ((version, total), ids, matrix, docs)
        return ids, matrix, docs

    def search(self, query: str, embedder: Embedder, top_k: int = 8,
               filters: SearchFilters | None = None) -> list[SearchHit]:
        active_filters = filters or SearchFilters()
        allowed = self._allowed_docs(active_filters)
        scores: dict[int, float] = {}
        chunk_doc: dict[int, str] = {}

        # Keyword ranking
        fts_query_text = fts_query(query)
        if fts_query_text:
            rows = self.database.execute(
                "SELECT f.chunk_id, c.doc_id FROM chunks_fts f JOIN chunks c ON c.chunk_id=f.chunk_id "
                "WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts, 2.0, 1.0) LIMIT ?",
                (fts_query_text, self.candidates * 3)).fetchall()
            rank = 0
            for chunk_id, doc_id in rows:
                if allowed is not None and doc_id not in allowed:
                    continue
                scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (RRF_K + rank)
                chunk_doc[chunk_id] = doc_id
                rank += 1
                if rank >= self.candidates:
                    break

        # Vector ranking
        ids, mat, docs = self._matrix(embedder)
        if len(ids):
            similarities = mat @ embedder.embed_query(query)
            if allowed is not None:
                mask = np.array([doc_id in allowed for doc_id in docs])
                similarities = np.where(mask, similarities, -np.inf)
            top = np.argsort(-similarities)[: self.candidates]
            for rank, position in enumerate(top):
                if not np.isfinite(similarities[position]):
                    break
                chunk_id = int(ids[position])
                scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (RRF_K + rank)
                chunk_doc[chunk_id] = docs[position]

        # Best chunk per document
        best: dict[str, tuple[float, int]] = {}
        for chunk_id, score in scores.items():
            doc_id = chunk_doc[chunk_id]
            if doc_id not in best or score > best[doc_id][0]:
                best[doc_id] = (score, chunk_id)
        ranked = sorted(best.items(), key=lambda pair: -pair[1][0])[:top_k]
        return [self._hit(doc_id, score, chunk_id) for doc_id, (score, chunk_id) in ranked]

    def _hit(self, doc_id: str, score: float, chunk_id: int | None) -> SearchHit:
        doc_row = self.database.execute("SELECT kind, title, path, video_id, url, tags, published, body "
                                        "FROM docs WHERE doc_id=?", (doc_id,)).fetchone()
        snippet = doc_row[7]
        if chunk_id is not None:
            row = self.database.execute("SELECT text FROM chunks WHERE chunk_id=?", (chunk_id,)).fetchone()
            snippet = row[0] if row else snippet
        snippet = snippet if len(snippet) <= 400 else snippet[:397] + "..."
        return SearchHit(doc_id=doc_id, kind=doc_row[0], title=doc_row[1], path=doc_row[2],
                         video_id=doc_row[3], url=doc_row[4], score=round(score, 5), snippet=snippet,
                         tags=doc_row[5].split(), published=doc_row[6])

    def similar(self, video_id: str, embedder: Embedder, top_k: int = 8) -> list[SearchHit]:
        rows = self.database.execute("SELECT doc_id, vec FROM doc_vectors WHERE embedder=?",
                                     (embedder.name,)).fetchall()
        vectors = {doc_id: np.frombuffer(vector, np.float32) for doc_id, vector in rows}
        if video_id not in vectors:
            return []
        query_vector = vectors[video_id]
        similarities = sorted(((float(vector @ query_vector), doc_id)
                               for doc_id, vector in vectors.items() if doc_id != video_id), reverse=True)
        return [self._hit(doc_id, similarity, None) for similarity, doc_id in similarities[:top_k]]

    def stats(self) -> dict:
        scalar = lambda sql: self.database.execute(sql).fetchone()[0]
        return {
            "videos": scalar("SELECT COUNT(*) FROM docs WHERE kind='video'"),
            "sections": scalar("SELECT COUNT(*) FROM docs WHERE kind='section'"),
            "chunks": scalar("SELECT COUNT(*) FROM chunks"),
            "vectors_by_embedder": dict(self.database.execute(
                "SELECT embedder, COUNT(*) FROM vectors GROUP BY embedder").fetchall()),
        }
