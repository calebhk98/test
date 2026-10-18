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

    def split(self, video_info: VideoInfo, transcript: Transcript) -> list[Section]:
        sections: list[Section] = []
        current_segments: list = []
        start = 0.0
        for segment in transcript.segments:
            if current_segments and segment.start - start >= self.window:
                sections.append(self._make(len(sections) + 1, start, segment.start,
                                           current_segments))
                current_segments, start = [], segment.start
            current_segments.append(segment)
        if current_segments:
            sections.append(self._make(len(sections) + 1, start, current_segments[-1].end,
                                       current_segments))
        return sections

    @staticmethod
    def _make(index, start, end, segments_in_section) -> Section:
        minutes, seconds = divmod(int(start), 60)
        return Section(index=index, title=f"Part {index} ({minutes}:{seconds:02d})", start=start,
                       end=end,
                       text=" ".join(segment.text.strip() for segment in segments_in_section).strip())
