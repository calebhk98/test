from __future__ import annotations

import numpy as np

from ..llm.base import post_json
from ..registry import register
from .base import Embedder


@register("embedder", "ollama")
class OllamaEmbedder(Embedder):
    def __init__(self, model: str = "embeddinggemma", host: str = "http://localhost:11434",
                 query_prefix: str = "", document_prefix: str = "", batch_size: int = 16):
        self.model = model
        self.host = host.rstrip("/")
        self.query_prefix = query_prefix
        self.document_prefix = document_prefix
        self.batch_size = batch_size

    def _embed(self, texts, is_query):
        prefix = self.query_prefix if is_query else self.document_prefix
        r = post_json(f"{self.host}/api/embed", {"model": self.model,
                                                  "input": [prefix + t for t in texts]})
        return np.array(r["embeddings"], dtype=np.float32)
