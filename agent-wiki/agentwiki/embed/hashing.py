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

    def __init__(self, dimensions: int = 512):
        self.dimensions = dimensions
        self.model = str(dimensions)

    def _embed(self, texts, is_query):
        counts = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for row, text in enumerate(texts):
            words = re.findall(r"\w+", text.lower())
            pairs = [first_word + " " + second_word for first_word, second_word in zip(words, words[1:])]
            for token in words + pairs:
                hash_value = int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "little")
                bucket = hash_value % self.dimensions
                counts[row, bucket] += 1.0 if (hash_value >> 63) == 0 else -1.0
        return counts
