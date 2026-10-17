from __future__ import annotations

from ..models import Section, Transcript, VideoInfo
from ..registry import create, register
from .base import Segmenter


@register("segmenter", "chain")
class ChainSegmenter(Segmenter):
    def __init__(self, segmenters: list[Segmenter]):
        self.segmenters = segmenters

    @classmethod
    def from_config(cls, params, app=None):
        return cls([create("segmenter", segmenter_spec, app)
                    for segmenter_spec in params["segmenters"]])

    def split(self, video_info: VideoInfo, transcript: Transcript) -> list[Section]:
        for segmenter in self.segmenters:
            sections = segmenter.split(video_info, transcript)
            if sections:
                return sections
        return []
