"""Load config.toml and merge it over the defaults."""
from __future__ import annotations

import copy
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "plugins": [],
    "source": {"type": "yt-dlp"},
    "transcriber": {
        "type": "chain",
        "transcribers": [
            {"type": "faster-whisper", "model": "large-v3-turbo"},
            {"type": "youtube-captions"},
        ],
    },
    "segmenter": {
        "type": "chain",
        "segmenters": [{"type": "chapters"}, {"type": "fixed-window", "minutes": 4}],
    },
    "llm": {"type": "null"},
    "enricher": {"type": "local"},
    "embedder": {"type": "hashing"},
    "index": {"type": "sqlite", "chunk_chars": "auto", "chunk_overlap": 200, "whole_video": "auto"},
    "ingest": {
        "min_duration": 90,          # seconds; drops Shorts
        "skip_live": True,
        "sleep_between": 15,         # seconds between downloads in `run`
        "max_attempts": 3,
        "check_recent": 30,          # uploads per channel looked at by `check`
        "keep_audio": False,
    },
    "search": {"k": 8, "exclude_sponsor": True},
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        # A new `type` replaces a component wholesale rather than mixing params.
        if isinstance(v, dict) and isinstance(out.get(k), dict) and "type" not in v:
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


@dataclass
class Config:
    root: Path
    data: dict[str, Any]

    @property
    def wiki_dir(self) -> Path:
        return self.root / "wiki"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    @classmethod
    def load(cls, root: str | Path | None = None, path: str | Path | None = None) -> "Config":
        root = Path(root or ".").resolve()
        path = Path(path) if path else root / "config.toml"
        user: dict[str, Any] = {}
        if path.exists():
            with open(path, "rb") as f:
                user = tomllib.load(f)
        return cls(root=root, data=_merge(DEFAULTS, user))
