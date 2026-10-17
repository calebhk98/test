from __future__ import annotations

import logging

import numpy as np

from .. import hardware
from ..registry import register
from .base import Embedder

log = logging.getLogger(__name__)


@register("embedder", "sentence-transformers")
class SentenceTransformerEmbedder(Embedder):
    """Any Hugging Face embedding model.

    Context windows (from the model cards): Qwen/Qwen3-Embedding-0.6B, -4B and
    -8B take 32K tokens; google/embeddinggemma-2 8K; nomic-embed-text-v1.5 and
    BAAI/bge-m3 8K; google/embeddinggemma-300m 2K.

    Query and document prompts that ship with the model are applied
    automatically. `dim` truncates Matryoshka models to save space; it changes
    the vector space, so it is part of `name`. `max_tokens` caps the window
    below the model's own, which bounds memory on small devices (attention
    cost grows with length).
    """

    def __init__(self, model: str = "Qwen/Qwen3-Embedding-0.6B", device: str = "auto",
                 dim: int | None = None, batch_size: int | str = "auto",
                 max_tokens: int | None = None, precision: str = "auto",
                 query_prompt: str | None = None, document_prompt: str | None = None,
                 trust_remote_code: bool = False):
        self.model = model
        hw = hardware.detect()
        self.device = hw.device if device == "auto" else device
        self.dim = dim
        self.batch_size = (32 if self.device != "cpu" else 4) if batch_size == "auto" else int(batch_size)
        self._max_tokens_cap = max_tokens
        self.precision = precision
        self.query_prompt = query_prompt
        self.document_prompt = document_prompt
        self.trust_remote_code = trust_remote_code
        self._st = None

    @property
    def name(self) -> str:
        return f"st:{self.model}" + (f"@{self.dim}" if self.dim else "")

    def _load(self):
        if self._st is None:
            from sentence_transformers import SentenceTransformer
            kwargs = {}
            if self.device != "cpu" and self.precision in ("auto", "half"):
                import torch
                # Half precision halves memory with no meaningful loss for embeddings.
                kwargs["torch_dtype"] = torch.bfloat16 if self.device == "cuda" else torch.float16
            log.info("loading embedder %s on %s", self.model, self.device)
            self._st = SentenceTransformer(self.model, device=self.device, truncate_dim=self.dim,
                                           trust_remote_code=self.trust_remote_code,
                                           model_kwargs=kwargs or None)
            if self._max_tokens_cap:
                self._st.max_seq_length = min(self._st.max_seq_length or self._max_tokens_cap,
                                              self._max_tokens_cap)
        return self._st

    @property
    def max_tokens(self) -> int:
        return int(self._load().max_seq_length or 512)

    def count_tokens(self, text: str) -> int:
        return len(self._load().tokenizer(text, add_special_tokens=False)["input_ids"])

    def _embed(self, texts: list[str], is_query: bool) -> np.ndarray:
        st = self._load()
        explicit = self.query_prompt if is_query else self.document_prompt
        if explicit is not None:
            return st.encode([explicit + t for t in texts], convert_to_numpy=True)
        fn = getattr(st, "encode_query" if is_query else "encode_document", None)
        if fn is not None:   # sentence-transformers >= 5 applies the model's own prompts
            return fn(texts, convert_to_numpy=True)
        return st.encode(texts, convert_to_numpy=True)
