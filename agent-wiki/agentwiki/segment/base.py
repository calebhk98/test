from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Section, Transcript, VideoInfo
from ..registry import Component


class Segmenter(Component, ABC):
    @abstractmethod
    def split(self, video_info: VideoInfo, transcript: Transcript) -> list[Section]:
        """Return sections with `text` filled, or [] if this method does not apply."""


def fill_text(sections: list[Section], transcript: Transcript) -> list[Section]:
    for section in sections:
        section.text = " ".join(
            segment.text.strip() for segment in transcript.between(section.start, section.end)).strip()
    return sections
