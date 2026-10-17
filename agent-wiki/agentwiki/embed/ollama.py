from __future__ import annotations

import numpy as np

from ..llm.base import post_json
from ..registry import register
from .base import Embedder


@register("embedder", "ollama")
class OllamaEmbedder(Embedder):
    def __init__(self, model: str = "embeddinggemma", host: str = "http://localhost:11434",
                 query_prefix: str = "", document_prefix: str = "", batch_size: int = 16,
                 max_tokens: int = 2048):
        self.model = model
        self.host = host.rstrip("/")
        self.query_prefix = query_prefix
        self.document_prefix = document_prefix
        self.batch_size = batch_size
        self.max_tokens = max_tokens   # set to your model's context window

    def _embed(self, texts, is_query):
        prefix = self.query_prefix if is_query else self.document_prefix
        response = post_json(f"{self.host}/api/embed", {"model": self.model,
                                                        "input": [prefix + text for text in texts]})
        return np.array(response["embeddings"], dtype=np.float32)
