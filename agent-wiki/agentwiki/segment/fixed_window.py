from __future__ import annotations

from ..models import Section, Transcript, VideoInfo
from ..registry import register
from .base import Segmenter


@register("segmenter", "fixed-window")
class FixedWindowSegmenter(Segmenter):
    """Cut every N minutes, on transcript segment boundaries. The fallback when
    a video has no chapters; an LLM topic segmenter can replace it later."""

    def __init__(self, minutes: float = 4.0):
        self.window = minutes * 60

    def split(self, info: VideoInfo, transcript: Transcript) -> list[Section]:
        sections: list[Section] = []
        cur: list = []
        start = 0.0
        for seg in transcript.segments:
            if cur and seg.start - start >= self.window:
                sections.append(self._make(len(sections) + 1, start, seg.start, cur))
                cur, start = [], seg.start
            cur.append(seg)
        if cur:
            sections.append(self._make(len(sections) + 1, start, cur[-1].end, cur))
        return sections

    @staticmethod
    def _make(i, start, end, segs) -> Section:
        m, s = divmod(int(start), 60)
        return Section(index=i, title=f"Part {i} ({m}:{s:02d})", start=start, end=end,
                       text=" ".join(x.text.strip() for x in segs).strip())
