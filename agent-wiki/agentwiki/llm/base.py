from __future__ import annotations

import json
import re
import time
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
        """Can this LLM answer right now? Cached for a minute, so a stopped
        server is noticed quickly and a restarted one is picked up again."""
        now = time.time()
        if now - self._checked_at > 60:
            self._ok = self._ping()
            self._checked_at = now
        return self._ok

    def mark_unavailable(self) -> None:
        self._ok, self._checked_at = False, time.time()

    def _ping(self) -> bool:
        return True

    _ok: bool = True
    _checked_at: float = 0.0

    @abstractmethod
    def complete(self, prompt: str, system: str | None = None, *, max_tokens: int = 1024,
                 temperature: float = 0.2, json_mode: bool = False) -> str: ...

    def complete_json(self, prompt: str, system: str | None = None, **options) -> Any:
        text = self.complete(prompt, system, json_mode=True, **options)
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
    depth, in_string, escaped = 0, False, False
    for position in range(start, len(text)):
        character = text[position]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:position + 1])
    raise LLMError(f"unterminated JSON in reply: {text[:200]!r}")


def get_ok(url: str, headers: dict | None = None, timeout: float = 3) -> bool:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=timeout):
            return True
    except Exception:
        return False


def post_json(url: str, body: dict, headers: dict | None = None, timeout: float = 600) -> dict:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise LLMError(f"{url}: HTTP {error.code}: {error.read()[:500]!r}") from error
    except (urllib.error.URLError, ConnectionError, TimeoutError) as error:
        raise LLMUnavailable(f"{url}: {getattr(error, 'reason', error)}") from error
