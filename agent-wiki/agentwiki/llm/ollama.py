from __future__ import annotations

from ..registry import register
from .base import LLM, get_ok, post_json


@register("llm", "ollama")
class OllamaLLM(LLM):
    def __init__(self, model: str, host: str = "http://localhost:11434",
                 num_ctx: int = 16384, timeout: float = 600):
        self.model = model
        self.host = host.rstrip("/")
        self.num_ctx = num_ctx
        self.timeout = timeout

    def _ping(self) -> bool:
        return get_ok(f"{self.host}/api/tags")

    def complete(self, prompt, system=None, *, max_tokens=1024, temperature=0.2, json_mode=False):
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": prompt}]
        body = {"model": self.model, "messages": messages, "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens,
                            "num_ctx": self.num_ctx}}
        if json_mode:
            body["format"] = "json"
        return post_json(f"{self.host}/api/chat", body, timeout=self.timeout)["message"]["content"]
