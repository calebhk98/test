from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..registry import Component


class Embedder(Component, ABC):
    """Text to unit-length float32 vectors.

    `name` must change whenever the vector space changes (different model or
    output size), because the index keys stored vectors by it. Device, batch
    size and precision do not change the space and are not part of the name,
    so the same wiki can be embedded on a laptop and searched on a phone.
    """

    model: str = ""
    batch_size: int = 16
    #: Longest input in tokens before the model truncates.
    max_tokens: int = 512

    @property
    def name(self) -> str:
        return f"{self.registry_name}:{self.model}"

    def count_tokens(self, text: str) -> int:
        """Override with the real tokenizer when there is one. ~4 chars per token in English."""
        return len(text) // 4 + 1

    @abstractmethod
    def _embed(self, texts: list[str], is_query: bool) -> np.ndarray: ...

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        batches = [self._embed(texts[start:start + self.batch_size], False)
                   for start in range(0, len(texts), self.batch_size)]
        return normalize(np.vstack(batches)) if batches else np.zeros((0, 0), np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return normalize(self._embed([text], True))[0]


def normalize(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=-1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)
