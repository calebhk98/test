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
    out, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind(". "), window.rfind("? "), window.rfind("! "))
            if cut < size // 2:
                cut = window.rfind(" ")
            if cut > size // 4:
                end = start + cut + 1
        out.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        # Do not start a chunk mid-word.
        sp = text.find(" ", start)
        if 0 <= sp < end:
            start = sp + 1
    return [c for c in out if c]


def fts_query(q: str) -> str:
    terms = re.findall(r"\w+", q.lower())
    return " OR ".join(f'"{t}"' for t in terms)


@register("index", "sqlite")
class SQLiteIndex(VectorIndex):
    def __init__(self, path: str | Path, chunk_chars: int = 1500, chunk_overlap: int = 200,
                 candidates: int = 200):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.executescript(SCHEMA)
        self.chunk_chars = chunk_chars
        self.chunk_overlap = chunk_overlap
        self.candidates = candidates
        self._cache: dict[str, tuple[int, np.ndarray, np.ndarray, list[str]]] = {}

    @classmethod
    def from_config(cls, params, ctx=None):
        params = dict(params)
        params.setdefault("path", ctx.config.data_dir / "index.sqlite")
        return cls(**params)

    # ---- writing -----------------------------------------------------------

    def _delete_docs(self, where: str, args: tuple) -> None:
        ids = [r[0] for r in self.db.execute(f"SELECT doc_id FROM docs WHERE {where}", args)]
        for d in ids:
            cids = [r[0] for r in self.db.execute("SELECT chunk_id FROM chunks WHERE doc_id=?", (d,))]
            self.db.executemany("DELETE FROM vectors WHERE chunk_id=?", [(c,) for c in cids])
            self.db.executemany("DELETE FROM chunks_fts WHERE chunk_id=?", [(c,) for c in cids])
            self.db.execute("DELETE FROM chunks WHERE doc_id=?", (d,))
            self.db.execute("DELETE FROM doc_vectors WHERE doc_id=?", (d,))
            self.db.execute("DELETE FROM docs WHERE doc_id=?", (d,))

    def upsert(self, docs: list[IndexDoc], embedder: Embedder) -> None:
        pending: list[tuple[int, str]] = []
        with self.db:
            for doc in docs:
                self._delete_docs("doc_id=?", (doc.doc_id,))
                self.db.execute(
                    "INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (doc.doc_id, doc.kind, doc.video_id, doc.channel, doc.path, doc.title, doc.url,
                     doc.published, " " + " ".join(doc.tags) + " ", int(doc.is_sponsor), doc.text))
                for i, ch in enumerate(chunk_text(doc.text, self.chunk_chars, self.chunk_overlap)):
                    cid = self.db.execute("INSERT INTO chunks (doc_id, ord, text) VALUES (?,?,?)",
                                          (doc.doc_id, i, ch)).lastrowid
                    self.db.execute("INSERT INTO chunks_fts (title, text, chunk_id) VALUES (?,?,?)",
                                    (doc.title, ch, cid))
                    pending.append((cid, f"{doc.title}\n{ch}"))
            if pending:
                vecs = embedder.embed_documents([t for _, t in pending])
                self.db.executemany(
                    "INSERT OR REPLACE INTO vectors VALUES (?,?,?)",
                    [(cid, embedder.name, v.astype(np.float32).tobytes())
                     for (cid, _), v in zip(pending, vecs)])

    def reembed(self, embedder: Embedder, batch: int = 256, progress=None) -> int:
        """Embed every chunk that has no vector for this embedder."""
        rows = self.db.execute(
            "SELECT c.chunk_id, d.title, c.text FROM chunks c JOIN docs d USING(doc_id) "
            "WHERE c.chunk_id NOT IN (SELECT chunk_id FROM vectors WHERE embedder=?)",
            (embedder.name,)).fetchall()
        for i in range(0, len(rows), batch):
            part = rows[i:i + batch]
            vecs = embedder.embed_documents([f"{t}\n{x}" for _, t, x in part])
            with self.db:
                self.db.executemany("INSERT OR REPLACE INTO vectors VALUES (?,?,?)",
                                    [(c, embedder.name, v.tobytes()) for (c, _, _), v in zip(part, vecs)])
            if progress:
                progress(min(i + batch, len(rows)), len(rows))
        for (vid,) in self.db.execute("SELECT doc_id FROM docs WHERE kind='video'").fetchall():
            self.pool_video(vid, embedder)
        return len(rows)

    def delete_video(self, video_id: str) -> None:
        with self.db:
            self._delete_docs("video_id=?", (video_id,))

    def pool_video(self, video_id: str, embedder: Embedder) -> None:
        rows = self.db.execute(
            "SELECT v.vec FROM vectors v JOIN chunks c USING(chunk_id) JOIN docs d USING(doc_id) "
            "WHERE d.video_id=? AND d.kind='section' AND v.embedder=?",
            (video_id, embedder.name)).fetchall()
        if not rows:
            return
        mean = normalize(np.mean([np.frombuffer(r[0], np.float32) for r in rows], axis=0))
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO doc_vectors VALUES (?,?,?)",
                            (video_id, embedder.name, mean.tobytes()))

    # ---- reading -----------------------------------------------------------

    def _allowed_docs(self, f: SearchFilters) -> set[str] | None:
        where, args = [], []
        if f.kind:
            where.append("kind=?"); args.append(f.kind)
        if f.channel:
            where.append("(channel=? OR channel LIKE ?)"); args += [f.channel, f"%{f.channel}%"]
        if f.since:
            where.append("published>=?"); args.append(f.since)
        if f.exclude_sponsor:
            where.append("is_sponsor=0")
        for t in f.tags:
            where.append("tags LIKE ?"); args.append(f"% {t} %")
        if not where:
            return None
        return {r[0] for r in self.db.execute(f"SELECT doc_id FROM docs WHERE {' AND '.join(where)}", args)}

    def _matrix(self, embedder: Embedder):
        version = self.db.execute("PRAGMA data_version").fetchone()[0]
        total = self.db.total_changes
        key = embedder.name
        c = self._cache.get(key)
        if c and c[0] == (version, total):
            return c[1], c[2], c[3]
        rows = self.db.execute(
            "SELECT v.chunk_id, c.doc_id, v.vec FROM vectors v JOIN chunks c USING(chunk_id) "
            "WHERE v.embedder=?", (key,)).fetchall()
        ids = np.array([r[0] for r in rows], dtype=np.int64)
        docs = [r[1] for r in rows]
        mat = np.vstack([np.frombuffer(r[2], np.float32) for r in rows]) if rows else np.zeros((0, 1), np.float32)
        self._cache[key] = ((version, total), ids, mat, docs)
        return ids, mat, docs

    def search(self, query: str, embedder: Embedder, k: int = 8,
               filters: SearchFilters | None = None) -> list[SearchHit]:
        f = filters or SearchFilters()
        allowed = self._allowed_docs(f)
        scores: dict[int, float] = {}
        chunk_doc: dict[int, str] = {}

        # Keyword ranking
        fq = fts_query(query)
        if fq:
            rows = self.db.execute(
                "SELECT f.chunk_id, c.doc_id FROM chunks_fts f JOIN chunks c ON c.chunk_id=f.chunk_id "
                "WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts, 2.0, 1.0) LIMIT ?",
                (fq, self.candidates * 3)).fetchall()
            rank = 0
            for cid, did in rows:
                if allowed is not None and did not in allowed:
                    continue
                scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank)
                chunk_doc[cid] = did
                rank += 1
                if rank >= self.candidates:
                    break

        # Vector ranking
        ids, mat, docs = self._matrix(embedder)
        if len(ids):
            sims = mat @ embedder.embed_query(query)
            if allowed is not None:
                mask = np.array([d in allowed for d in docs])
                sims = np.where(mask, sims, -np.inf)
            top = np.argsort(-sims)[: self.candidates]
            for rank, i in enumerate(top):
                if not np.isfinite(sims[i]):
                    break
                cid = int(ids[i])
                scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank)
                chunk_doc[cid] = docs[i]

        # Best chunk per document
        best: dict[str, tuple[float, int]] = {}
        for cid, s in scores.items():
            d = chunk_doc[cid]
            if d not in best or s > best[d][0]:
                best[d] = (s, cid)
        ranked = sorted(best.items(), key=lambda kv: -kv[1][0])[:k]
        return [self._hit(d, s, cid) for d, (s, cid) in ranked]

    def _hit(self, doc_id: str, score: float, chunk_id: int | None) -> SearchHit:
        r = self.db.execute("SELECT kind, title, path, video_id, url, tags, published, body "
                            "FROM docs WHERE doc_id=?", (doc_id,)).fetchone()
        snippet = r[7]
        if chunk_id is not None:
            row = self.db.execute("SELECT text FROM chunks WHERE chunk_id=?", (chunk_id,)).fetchone()
            snippet = row[0] if row else snippet
        snippet = snippet if len(snippet) <= 400 else snippet[:397] + "..."
        return SearchHit(doc_id=doc_id, kind=r[0], title=r[1], path=r[2], video_id=r[3], url=r[4],
                         score=round(score, 5), snippet=snippet, tags=r[5].split(), published=r[6])

    def similar(self, video_id: str, embedder: Embedder, k: int = 8) -> list[SearchHit]:
        rows = self.db.execute("SELECT doc_id, vec FROM doc_vectors WHERE embedder=?",
                               (embedder.name,)).fetchall()
        vecs = {d: np.frombuffer(v, np.float32) for d, v in rows}
        if video_id not in vecs:
            return []
        q = vecs[video_id]
        sims = sorted(((float(v @ q), d) for d, v in vecs.items() if d != video_id), reverse=True)
        return [self._hit(d, s, None) for s, d in sims[:k]]

    def stats(self) -> dict:
        one = lambda sql: self.db.execute(sql).fetchone()[0]
        return {
            "videos": one("SELECT COUNT(*) FROM docs WHERE kind='video'"),
            "sections": one("SELECT COUNT(*) FROM docs WHERE kind='section'"),
            "chunks": one("SELECT COUNT(*) FROM chunks"),
            "vectors_by_embedder": dict(self.db.execute(
                "SELECT embedder, COUNT(*) FROM vectors GROUP BY embedder").fetchall()),
        }
