from __future__ import annotations

import os

import numpy as np

from ..llm.base import post_json
from ..registry import register
from .base import Embedder


@register("embedder", "openai-compatible")
class OpenAICompatEmbedder(Embedder):
    def __init__(self, model: str, base_url: str = "http://localhost:8080/v1",
                 api_key_env: str = "OPENAI_API_KEY", dimensions: int | None = None,
                 query_prefix: str = "", document_prefix: str = "", batch_size: int = 32):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.dimensions = dimensions
        self.query_prefix = query_prefix
        self.document_prefix = document_prefix
        self.batch_size = batch_size

    @property
    def name(self) -> str:
        return f"openai-compatible:{self.model}" + (f"@{self.dimensions}" if self.dimensions else "")

    def _embed(self, texts, is_query):
        prefix = self.query_prefix if is_query else self.document_prefix
        body = {"model": self.model, "input": [prefix + t for t in texts]}
        if self.dimensions:
            body["dimensions"] = self.dimensions
        key = os.environ.get(self.api_key_env, "")
        r = post_json(f"{self.base_url}/embeddings", body,
                      {"Authorization": f"Bearer {key}"} if key else {})
        data = sorted(r["data"], key=lambda d: d["index"])
        return np.array([d["embedding"] for d in data], dtype=np.float32)
