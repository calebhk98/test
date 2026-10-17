from __future__ import annotations

import os

from ..registry import register
from .base import LLM, LLMError, post_json


@register("llm", "anthropic")
class AnthropicLLM(LLM):
    def __init__(self, model: str, api_key_env: str = "ANTHROPIC_API_KEY",
                 base_url: str = "https://api.anthropic.com", timeout: float = 600):
        self.model = model
        self.api_key_env = api_key_env
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _ping(self) -> bool:
        return bool(os.environ.get(self.api_key_env))

    def complete(self, prompt, system=None, *, max_tokens=1024, temperature=0.2, json_mode=False):
        key = os.environ.get(self.api_key_env)
        if not key:
            raise LLMError(f"set {self.api_key_env} to use the anthropic LLM")
        if json_mode:
            prompt += "\n\nReply with only the JSON object."
        body = {"model": self.model, "max_tokens": max_tokens, "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]}
        if system:
            body["system"] = system
        response = post_json(f"{self.base_url}/v1/messages", body,
                             {"x-api-key": key, "anthropic-version": "2023-06-01"}, self.timeout)
        return "".join(block.get("text", "") for block in response.get("content", [])
                       if block.get("type") == "text")
