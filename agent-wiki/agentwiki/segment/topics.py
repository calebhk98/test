"""Split by topic using the embedding model, for videos without chapters.

The transcript is cut into short blocks, each block embedded, and the
similarity between what comes before and after each block boundary
measured. A topic change shows up as a dip; the deepest dips become section
boundaries (the TextTiling method, with embeddings instead of word counts).
Titles are the block's most representative key phrase.
"""
from __future__ import annotations

import numpy as np

from ..enrich.local import _candidates, _mmr
from ..models import Section, Transcript, VideoInfo
from ..registry import register
from .base import Segmenter


@register("segmenter", "topics")
class TopicSegmenter(Segmenter):
    def __init__(self, embedder, block_seconds: float = 20, window: int = 3,
                 min_section_seconds: float = 60, max_section_seconds: float = 480,
                 sensitivity: float = 0.5):
        self.embedder = embedder
        self.block = block_seconds
        self.window = window
        self.min_len = min_section_seconds
        self.max_len = max_section_seconds
        # Cut where a dip is deeper than mean + sensitivity * std of this video's
        # dips. Relative to the video, so a rambling interview and a rapid-fire
        # news roundup each get cut at their own topic changes.
        self.sensitivity = sensitivity

    @classmethod
    def from_config(cls, params, ctx=None):
        return cls(embedder=ctx.embedder, **params)

    def _blocks(self, t: Transcript) -> list[tuple[float, float, str]]:
        blocks, cur, start = [], [], None
        for s in t.segments:
            if start is None:
                start = s.start
            cur.append(s.text.strip())
            if s.end - start >= self.block:
                blocks.append((start, s.end, " ".join(cur)))
                cur, start = [], None
        if cur:
            blocks.append((start, t.segments[-1].end, " ".join(cur)))
        return blocks

    def split(self, info: VideoInfo, transcript: Transcript) -> list[Section]:
        blocks = self._blocks(transcript)
        if len(blocks) < 4:
            return []
        vecs = self.embedder.embed_documents([b[2] for b in blocks])
        n, w = len(blocks), self.window
        # Similarity between the w blocks before and after each gap.
        gap_sim = np.ones(n)
        for g in range(1, n):
            a = vecs[max(0, g - w):g].mean(axis=0)
            b = vecs[g:g + w].mean(axis=0)
            gap_sim[g] = float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
        # Depth: how far the gap falls below the nearest peaks on each side.
        depth = np.zeros(n)
        for g in range(1, n):
            lp = _climb(gap_sim[g:0:-1])      # walk left over gaps g, g-1, ..., 1
            rp = _climb(gap_sim[g:])          # walk right
            depth[g] = (lp - gap_sim[g]) + (rp - gap_sim[g])

        d = depth[1:]
        threshold = d.mean() + self.sensitivity * d.std()
        cuts: list[int] = []
        for g in np.argsort(-depth):
            if depth[g] <= threshold:
                break
            t = blocks[g][0]
            if t - blocks[0][0] < self.min_len or blocks[-1][1] - t < self.min_len:
                continue
            if all(abs(t - blocks[c][0]) >= self.min_len for c in cuts):
                cuts.append(int(g))
        cuts = sorted(cuts)
        # Force a cut inside any stretch longer than max_section_seconds.
        bounds = [0] + cuts + [n]
        final = []
        for a, b in zip(bounds, bounds[1:]):
            final.append(a)
            while blocks[b - 1][1] - blocks[final[-1]][0] > self.max_len:
                span = range(final[-1] + 1, b)
                limit = [g for g in span if blocks[g][0] - blocks[final[-1]][0] <= self.max_len]
                if not limit:
                    break
                final.append(max(limit, key=lambda g: depth[g]))
        final = sorted(set(final))

        video_centroid = vecs.mean(axis=0)
        sections = []
        for i, a in enumerate(final):
            b = final[i + 1] if i + 1 < len(final) else n
            text = " ".join(x[2] for x in blocks[a:b])
            title = self._title(text, vecs[a:b].mean(axis=0), video_centroid, i + 1)
            sections.append(Section(index=i + 1, title=title, start=blocks[a][0],
                                    end=blocks[b - 1][1], text=text))
        return sections

    def _title(self, text: str, centroid: np.ndarray, video: np.ndarray, i: int) -> str:
        """Two key phrases that describe this part and not the whole video.
        Without the second term every part of a video about models is "Model"."""
        cands = [c for c in _candidates(text, "", limit=40) if len(c) > 3]
        if not cands:
            return f"Part {i}"
        cv = self.embedder.embed_documents(cands)
        unit = lambda v: v / (np.linalg.norm(v) + 1e-9)
        score = cv @ unit(centroid) - 0.7 * (cv @ unit(video))
        order = list(np.argsort(-score))
        first = order[0]
        stem = lambda p: {w.lower().rstrip("s") for w in p.split()}
        # The second phrase must add something: no shared words ("World model
        # and model") and not a near-synonym of the first.
        second = next((j for j in order[1:] if not stem(cands[j]) & stem(cands[first])
                       and float(cv[j] @ cv[first]) < 0.8), None)
        words = [cands[first]] + ([cands[second]] if second is not None else [])
        title = " and ".join(words)
        return title[:1].upper() + title[1:]


def _climb(seq) -> float:
    """Highest value reached walking outward while similarity keeps rising."""
    peak = seq[0]
    for v in seq[1:]:
        if v < peak:
            break
        peak = v
    return float(peak)
