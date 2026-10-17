from __future__ import annotations

import numpy as np

from ..registry import register
from .base import Embedder


@register("embedder", "sentence-transformers")
class SentenceTransformerEmbedder(Embedder):
    """Any Hugging Face embedding model, e.g. google/embeddinggemma-300m.

    Models that ship query/document prompts (EmbeddingGemma does) get them
    applied automatically. `dim` truncates Matryoshka models such as
    EmbeddingGemma to 512/256/128 dimensions to save space.
    """

    def __init__(self, model: str = "google/embeddinggemma-300m", device: str | None = None,
                 dim: int | None = None, batch_size: int = 16, query_prompt: str | None = None,
                 document_prompt: str | None = None):
        self.model = model
        self.device = None if device in (None, "auto") else device
        self.dim = dim
        self.batch_size = batch_size
        self.query_prompt = query_prompt
        self.document_prompt = document_prompt
        self._st = None

    @property
    def name(self) -> str:
        return f"st:{self.model}" + (f"@{self.dim}" if self.dim else "")

    def _load(self):
        if self._st is None:
            from sentence_transformers import SentenceTransformer
            self._st = SentenceTransformer(self.model, device=self.device,
                                           truncate_dim=self.dim)
        return self._st

    def _embed(self, texts: list[str], is_query: bool) -> np.ndarray:
        st = self._load()
        explicit = self.query_prompt if is_query else self.document_prompt
        if explicit is not None:
            return st.encode([explicit + t for t in texts], convert_to_numpy=True)
        fn = getattr(st, "encode_query" if is_query else "encode_document", None)
        if fn is not None:   # sentence-transformers >= 5 applies the model's own prompts
            return fn(texts, convert_to_numpy=True)
        return st.encode(texts, convert_to_numpy=True)
