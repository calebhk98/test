from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..registry import Component


class Embedder(Component, ABC):
    """Text to unit-length float32 vectors.

    `name` must change whenever the vector space changes (different model or
    output size), because the index keys stored vectors by it.
    """

    model: str = ""
    batch_size: int = 16

    @property
    def name(self) -> str:
        return f"{self.registry_name}:{self.model}"

    @abstractmethod
    def _embed(self, texts: list[str], is_query: bool) -> np.ndarray: ...

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        out = [self._embed(texts[i:i + self.batch_size], False)
               for i in range(0, len(texts), self.batch_size)]
        return normalize(np.vstack(out)) if out else np.zeros((0, 0), np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return normalize(self._embed([text], True))[0]


def normalize(m: np.ndarray) -> np.ndarray:
    m = np.asarray(m, dtype=np.float32)
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(n == 0, 1, n)
