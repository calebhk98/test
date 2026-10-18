"""Split by topic using the embedding model, for videos without chapters.

The transcript is cut into short blocks, each block embedded, and the
similarity between what comes before and after each block boundary
measured. A topic change shows up as a dip; the deepest dips become section
boundaries (the TextTiling method, with embeddings instead of word counts).
Titles are the block's most representative key phrase.
"""
from __future__ import annotations

import numpy as np

from ..enrich.text_tools import phrase_candidates
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
    def from_config(cls, params, app=None):
        return cls(embedder=app.embedder, **params)

    def _blocks(self, transcript: Transcript) -> list[tuple[float, float, str]]:
        blocks, current_texts, start = [], [], None
        for segment in transcript.segments:
            if start is None:
                start = segment.start
            current_texts.append(segment.text.strip())
            if segment.end - start >= self.block:
                blocks.append((start, segment.end, " ".join(current_texts)))
                current_texts, start = [], None
        if current_texts:
            blocks.append((start, transcript.segments[-1].end, " ".join(current_texts)))
        return blocks

    def split(self, video_info: VideoInfo, transcript: Transcript) -> list[Section]:
        blocks = self._blocks(transcript)
        if len(blocks) < 4:
            return []
        vectors = self.embedder.embed_documents([block[2] for block in blocks])
        block_count, window_size = len(blocks), self.window
        # Similarity between the window_size blocks before and after each gap.
        gap_similarity = np.ones(block_count)
        for gap in range(1, block_count):
            before_mean = vectors[max(0, gap - window_size):gap].mean(axis=0)
            after_mean = vectors[gap:gap + window_size].mean(axis=0)
            norms = np.linalg.norm(before_mean) * np.linalg.norm(after_mean)
            gap_similarity[gap] = float(before_mean @ after_mean / (norms + 1e-9))
        # Depth: how far the gap falls below the nearest peaks on each side.
        depth = np.zeros(block_count)
        for gap in range(1, block_count):
            left_peak = _climb(gap_similarity[gap:0:-1])      # walk left over gaps gap, gap-1, ..., 1
            right_peak = _climb(gap_similarity[gap:])         # walk right
            depth[gap] = (left_peak - gap_similarity[gap]) + (right_peak - gap_similarity[gap])

        gap_depths = depth[1:]
        threshold = gap_depths.mean() + self.sensitivity * gap_depths.std()
        cuts: list[int] = []
        for gap in np.argsort(-depth):
            if depth[gap] <= threshold:
                break
            cut_time = blocks[gap][0]
            if cut_time - blocks[0][0] < self.min_len or blocks[-1][1] - cut_time < self.min_len:
                continue
            if all(abs(cut_time - blocks[cut][0]) >= self.min_len for cut in cuts):
                cuts.append(int(gap))
        cuts = sorted(cuts)
        # Force a cut inside any stretch longer than max_section_seconds.
        bounds = [0] + cuts + [block_count]
        final = []
        for start_block, end_block in zip(bounds, bounds[1:]):
            final.append(start_block)
            while blocks[end_block - 1][1] - blocks[final[-1]][0] > self.max_len:
                span = range(final[-1] + 1, end_block)
                limit = [gap for gap in span if blocks[gap][0] - blocks[final[-1]][0] <= self.max_len]
                if not limit:
                    break
                final.append(max(limit, key=lambda gap: depth[gap]))
        final = sorted(set(final))

        video_centroid = vectors.mean(axis=0)
        sections = []
        for position, start_block in enumerate(final):
            end_block = final[position + 1] if position + 1 < len(final) else block_count
            text = " ".join(block[2] for block in blocks[start_block:end_block])
            title = self._title(text, vectors[start_block:end_block].mean(axis=0), video_centroid,
                                position + 1)
            sections.append(Section(index=position + 1, title=title, start=blocks[start_block][0],
                                    end=blocks[end_block - 1][1], text=text))
        return sections

    def _title(self, text: str, centroid: np.ndarray, video: np.ndarray, part_number: int) -> str:
        """Two key phrases that describe this part and not the whole video.
        Without the second term every part of a video about models is "Model"."""
        candidates = [candidate for candidate in phrase_candidates(text, limit=40) if len(candidate) > 3]
        if not candidates:
            return f"Part {part_number}"
        candidate_vectors = self.embedder.embed_documents(candidates)
        unit = lambda vector: vector / (np.linalg.norm(vector) + 1e-9)
        score = candidate_vectors @ unit(centroid) - 0.7 * (candidate_vectors @ unit(video))
        order = list(np.argsort(-score))
        first = order[0]
        stem = lambda phrase: {word.lower().rstrip("s") for word in phrase.split()}
        # The second phrase must add something: no shared words ("World model
        # and model") and not a near-synonym of the first.
        second = next((position for position in order[1:]
                       if not stem(candidates[position]) & stem(candidates[first])
                       and float(candidate_vectors[position] @ candidate_vectors[first]) < 0.8), None)
        words = [candidates[first]] + ([candidates[second]] if second is not None else [])
        title = " and ".join(words)
        return title[:1].upper() + title[1:]


def _climb(similarities) -> float:
    """Highest value reached walking outward while similarity keeps rising."""
    peak = similarities[0]
    for value in similarities[1:]:
        if value < peak:
            break
        peak = value
    return float(peak)
