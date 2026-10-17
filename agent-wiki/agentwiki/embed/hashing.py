from __future__ import annotations

import hashlib
import re

import numpy as np

from ..registry import register
from .base import Embedder


@register("embedder", "hashing")
class HashingEmbedder(Embedder):
    """Bag of hashed words and word pairs. No model, no download, no meaning.

    For tests and for trying the pipeline before installing a real model;
    search quality is roughly keyword overlap.
    """

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.model = str(dim)

    def _embed(self, texts, is_query):
        m = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            words = re.findall(r"\w+", t.lower())
            for tok in words + [a + " " + b for a, b in zip(words, words[1:])]:
                h = int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=8).digest(), "little")
                m[i, h % self.dim] += 1.0 if (h >> 63) == 0 else -1.0
        return m
