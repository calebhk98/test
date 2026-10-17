from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Section, Transcript, VideoInfo
from ..registry import Component


class Segmenter(Component, ABC):
    @abstractmethod
    def split(self, info: VideoInfo, transcript: Transcript) -> list[Section]:
        """Return sections with `text` filled, or [] if this method does not apply."""


def fill_text(sections: list[Section], transcript: Transcript) -> list[Section]:
    for s in sections:
        s.text = " ".join(seg.text.strip() for seg in transcript.between(s.start, s.end)).strip()
    return sections
