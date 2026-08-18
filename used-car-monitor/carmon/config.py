"""Configuration loading: config.json for search/scoring knobs, .env for secrets."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


class ConfigError(RuntimeError):
    """Raised when configuration is missing or malformed."""


def load_env(env_path: Path | str | None = None) -> Dict[str, str]:
    """Read a simple KEY=VALUE .env file into a dict (does not overwrite real env vars).

    Values already present in os.environ win, so `MARKETCHECK_API_KEY=... python -m carmon`
    works the same as putting the key in .env.
    """
    path = Path(env_path) if env_path else DEFAULT_ENV_PATH
    values: Dict[str, str] = {}
    if path.exists():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            values[key.strip()] = value
    for key in ("MARKETCHECK_API_KEY", "DISCORD_WEBHOOK_URL", "CARMON_API_TOKEN"):
        env_value = os.environ.get(key)
        if env_value:
            values[key] = env_value
    return values


def get_secret(name: str, env: Dict[str, str] | None = None, required: bool = False) -> str:
    env = env if env is not None else load_env()
    value = (env.get(name) or "").strip()
    if required and not value:
        raise ConfigError(
            f"{name} is not set. Copy .env.example to .env and fill it in "
            f"(or export {name} in your shell)."
        )
    return value


class Config:
    """Thin wrapper around the parsed config.json with convenience accessors."""

    def __init__(self, data: Dict[str, Any], path: Path | None = None):
        self.data = data
        self.path = path

    # --- sections -------------------------------------------------------
    @property
    def search(self) -> Dict[str, Any]:
        return self.data.setdefault("search", {})

    @property
    def scoring(self) -> Dict[str, Any]:
        return self.data.setdefault("scoring", {})

    @property
    def api(self) -> Dict[str, Any]:
        return self.data.setdefault("api", {})

    @property
    def digest(self) -> Dict[str, Any]:
        return self.data.setdefault("digest", {})

    @property
    def web(self) -> Dict[str, Any]:
        return self.data.setdefault("web", {})

    @property
    def paths(self) -> Dict[str, Any]:
        return self.data.setdefault("paths", {})

    # --- resolved paths -------------------------------------------------
    def _resolve(self, value: str) -> Path:
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            return candidate
        return (PROJECT_ROOT / candidate).resolve()

    @property
    def db_path(self) -> Path:
        return self._resolve(self.paths.get("db", "data/carmon.db"))

    @property
    def digest_dir(self) -> Path:
        return self._resolve(self.paths.get("digest_dir", "data/digests"))

    def to_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self.data)


def load_config(path: Path | str | None = None) -> Config:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Config file {config_path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Config file {config_path} must contain a JSON object")
    return Config(data, config_path)
