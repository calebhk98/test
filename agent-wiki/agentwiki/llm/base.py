from __future__ import annotations

import json
import re
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from ..registry import Component


class LLMError(RuntimeError):
    pass


class LLMUnavailable(LLMError):
    """The server could not be reached. Worth retrying later, not working around."""


class LLM(Component, ABC):
    model: str = ""

    @property
    def name(self) -> str:
        return f"{self.registry_name}:{self.model}" if self.model else self.registry_name

    @property
    def available(self) -> bool:
        return True

    @abstractmethod
    def complete(self, prompt: str, system: str | None = None, *, max_tokens: int = 1024,
                 temperature: float = 0.2, json_mode: bool = False) -> str: ...

    def complete_json(self, prompt: str, system: str | None = None, **kw) -> Any:
        text = self.complete(prompt, system, json_mode=True, **kw)
        return extract_json(text)


def extract_json(text: str) -> Any:
    """Parse the first JSON object in a reply, tolerating code fences and chatter."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start < 0:
        raise LLMError(f"no JSON object in reply: {text[:200]!r}")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise LLMError(f"unterminated JSON in reply: {text[:200]!r}")


def post_json(url: str, body: dict, headers: dict | None = None, timeout: float = 600) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise LLMError(f"{url}: HTTP {e.code}: {e.read()[:500]!r}") from e
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        raise LLMUnavailable(f"{url}: {getattr(e, 'reason', e)}") from e
