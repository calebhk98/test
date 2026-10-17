from __future__ import annotations

from ..models import Section, Transcript, VideoInfo
from ..registry import create, register
from .base import Segmenter


@register("segmenter", "chain")
class ChainSegmenter(Segmenter):
    def __init__(self, segmenters: list[Segmenter]):
        self.segmenters = segmenters

    @classmethod
    def from_config(cls, params, ctx=None):
        return cls([create("segmenter", s, ctx) for s in params["segmenters"]])

    def split(self, info: VideoInfo, transcript: Transcript) -> list[Section]:
        for s in self.segmenters:
            out = s.split(info, transcript)
            if out:
                return out
        return []
