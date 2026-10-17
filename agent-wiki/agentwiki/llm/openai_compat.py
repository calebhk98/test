from __future__ import annotations

import os

from ..registry import register
from .base import LLM, get_ok, post_json


@register("llm", "openai-compatible")
class OpenAICompatLLM(LLM):
    """Any /v1/chat/completions server: llama.cpp, LM Studio, vLLM, OpenRouter, OpenAI."""

    def __init__(self, model: str, base_url: str = "http://localhost:8080/v1",
                 api_key_env: str = "OPENAI_API_KEY", json_mode_supported: bool = True,
                 timeout: float = 600):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.json_mode_supported = json_mode_supported
        self.timeout = timeout

    def _ping(self) -> bool:
        key = os.environ.get(self.api_key_env, "")
        return get_ok(f"{self.base_url}/models", {"Authorization": f"Bearer {key}"} if key else {})

    def complete(self, prompt, system=None, *, max_tokens=1024, temperature=0.2, json_mode=False):
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": prompt}]
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens,
                "temperature": temperature}
        if json_mode and self.json_mode_supported:
            body["response_format"] = {"type": "json_object"}
        key = os.environ.get(self.api_key_env, "")
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        r = post_json(f"{self.base_url}/chat/completions", body, headers, self.timeout)
        return r["choices"][0]["message"]["content"]
