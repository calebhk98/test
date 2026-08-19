"""Safe, auditable editing of config.json and .env — the backend behind the settings page.

Letting a web page rewrite configuration and secrets deserves care, so the rules are here in
one place rather than scattered through the HTTP layer:

* **Only a known set of keys may change.** A key must already exist in config.json, and the
  new value must be the same JSON type as the old one. New keys, new sections and type
  changes are rejected. That makes it impossible to bend the file into a shape the rest of
  the code does not expect.
* **`paths` is not editable over HTTP at all.** Repointing the database or digest directory
  is a filesystem operation, and a web form is the wrong place for it.
* **Secrets are write-only through the API.** Reading `.env` returns whether each secret is
  set and its last four characters — never the value. `.env` is rewritten with 0600
  permissions.
* **Every write is validated, backed up and timestamped.** `validate_config` runs before the
  file is replaced; a rejected change leaves the file untouched. The previous version is kept
  in `data/config-history/`.
* **Writes are refused on a non-loopback bind without a token.** A dashboard reachable from
  the network must not be able to hand out API keys or turn on scrapers anonymously.
"""

from __future__ import annotations

import copy
import ipaddress
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import PROJECT_ROOT, Config, load_env, validate_config

# Sections a settings page may touch. `paths` is deliberately absent.
EDITABLE_SECTIONS = ("search", "scoring", "api", "enrichment", "scrapers", "digest",
                     "demo", "web", "market", "discord", "sources")

# The only secrets the API knows about. Anything else in .env is left alone.
KNOWN_SECRETS = (
    "MARKETCHECK_API_KEY",
    "DISCORD_WEBHOOK_URL",
    "DISCORD_BOT_TOKEN",
    "DISCORD_USER_ID",
    "CARMON_API_TOKEN",
)

# Each secret, what it is for, and exactly where to go and get one. The settings page turns
# `url` into a link and shows `how` as the instructions, so nobody has to dig through docs.
SECRET_META: Dict[str, Dict[str, str]] = {
    "MARKETCHECK_API_KEY": {
        "label": "MarketCheck API key",
        "purpose": "Required — this is what fetches the listings.",
        "url": "https://www.marketcheck.com/apis",
        "how": "Sign up for the free plan (500 calls/month, $0). The key appears on your "
               "dashboard right after signup.",
    },
    "DISCORD_WEBHOOK_URL": {
        "label": "Discord webhook URL",
        "purpose": "Optional — posts the daily digest into a server channel.",
        "url": "https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks",
        "how": "In Discord: Server Settings → Integrations → Webhooks → New Webhook → Copy "
               "Webhook URL.",
    },
    "DISCORD_BOT_TOKEN": {
        "label": "Discord bot token",
        "purpose": "Optional — sends the digest as a direct message instead of to a channel.",
        "url": "https://discord.com/developers/applications",
        "how": "New Application → Bot → Reset Token → copy it. Discord only lets a bot DM you "
               "if you share a server with it, so also invite the bot to a private server.",
    },
    "DISCORD_USER_ID": {
        "label": "Your Discord user id",
        "purpose": "Optional — who the direct message goes to.",
        "url": "https://support.discord.com/hc/en-us/articles/206346498",
        "how": "Discord Settings → Advanced → Developer Mode on, then right-click your own "
               "name → Copy User ID.",
    },
    "CARMON_API_TOKEN": {
        "label": "API bearer token",
        "purpose": "Optional — leave blank on localhost. Required to edit settings over the "
                   "network, and to use the API from another machine.",
        "url": "",
        "how": "Invent one — any long random string. `python3 -c \"import secrets; "
               "print(secrets.token_urlsafe(32))\"` produces a good one.",
    },
}

SECRET_LABELS = {key: meta["label"] for key, meta in SECRET_META.items()}

ENV_TEMPLATE_HEADER = """# Secrets for the Used Car Daily Monitor.
#
# This file was created automatically and is gitignored — it never leaves your machine.
# Fill values in here, or edit them on the website's Settings page, which writes this file.
# Everything else (search criteria, scoring, scrapers) lives in config.json, not here.
"""


class SettingsError(ValueError):
    """A rejected change, with a message meant for the person who tried to make it."""


# --- write authorisation -------------------------------------------------
def is_loopback(host: Optional[str]) -> bool:
    if not host:
        return False
    if host in ("localhost", "::1"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def writes_allowed(bind_host: Optional[str], token: Optional[str]) -> Tuple[bool, str]:
    """May this server accept configuration writes at all?

    Loopback: yes. Anything else: only with a bearer token configured, because the settings
    page can reveal and change credentials.
    """
    if is_loopback(bind_host):
        return True, ""
    if token:
        return True, ""
    return False, (
        f"Refusing settings writes: the server is bound to {bind_host or 'a non-loopback address'} "
        "with no CARMON_API_TOKEN set. Bind to 127.0.0.1, or set a token in .env, before editing "
        "configuration over the network."
    )


# --- config --------------------------------------------------------------
def _walk(data: Dict[str, Any], dotted: str) -> Tuple[Dict[str, Any], str]:
    """Resolve 'scrapers.sources.carmax' to (parent_dict, 'carmax')."""
    parts = dotted.split(".")
    node: Any = data
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            raise SettingsError(f"unknown setting: {dotted}")
        node = node[part]
    if not isinstance(node, dict) or parts[-1] not in node:
        raise SettingsError(f"unknown setting: {dotted}")
    return node, parts[-1]


def _same_type(old: Any, new: Any) -> bool:
    if isinstance(old, bool) or isinstance(new, bool):
        return isinstance(old, bool) and isinstance(new, bool)
    if isinstance(old, (int, float)) and isinstance(new, (int, float)):
        return True
    return type(old) is type(new)


def editable_settings(config: Config) -> Dict[str, Any]:
    """Every editable key, with its current value and type — what a settings form renders."""
    fields: Dict[str, Any] = {}

    def walk(prefix: str, node: Dict[str, Any]) -> None:
        for key, value in node.items():
            dotted = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                walk(dotted, value)
            else:
                fields[dotted] = {
                    "value": value,
                    "type": "bool" if isinstance(value, bool) else
                            "number" if isinstance(value, (int, float)) else
                            "list" if isinstance(value, list) else "string",
                }

    for section in EDITABLE_SECTIONS:
        if isinstance(config.data.get(section), dict):
            walk(section, config.data[section])
    return fields


def apply_changes(config: Config, changes: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Validate and apply a set of dotted-key changes to config.json.

    Returns {"applied": {...}, "warnings": [...], "backup": path|None}. Raises SettingsError
    without touching the file if any single change is rejected — all or nothing.
    """
    if not isinstance(changes, dict) or not changes:
        raise SettingsError("no changes supplied")

    candidate = copy.deepcopy(config.data)
    applied: Dict[str, Any] = {}

    for dotted, new_value in changes.items():
        section = dotted.split(".")[0]
        if section not in EDITABLE_SECTIONS:
            raise SettingsError(
                f"{dotted!r} is not editable here. Editable sections: {', '.join(EDITABLE_SECTIONS)}. "
                "`paths` is deliberately excluded — change it in config.json directly."
            )
        parent, leaf = _walk(candidate, dotted)
        old_value = parent[leaf]
        if isinstance(old_value, str) and str(old_value).lower() == "auto" and new_value in (None, "", "auto"):
            continue  # leave derived weights alone
        if not _same_type(old_value, new_value):
            raise SettingsError(
                f"{dotted} expects {type(old_value).__name__}, got {type(new_value).__name__}. "
                "Values may change, but their type may not."
            )
        if isinstance(old_value, (int, float)) and not isinstance(old_value, bool):
            new_value = type(old_value)(new_value)
        parent[leaf] = new_value
        applied[dotted] = new_value

    if not applied:
        return {"applied": {}, "warnings": [], "backup": None}

    probe = Config(candidate, config.path)
    warnings = validate_config(probe)
    hard = [w for w in warnings if "unknown key" in w or "not recognised" in w]
    if hard:
        raise SettingsError("; ".join(hard))

    if dry_run:
        return {"applied": applied, "warnings": warnings, "backup": None, "dry_run": True}

    backup = _write_config(config, candidate)
    config.data.clear()
    config.data.update(candidate)
    return {"applied": applied, "warnings": warnings, "backup": str(backup) if backup else None}


def _write_config(config: Config, data: Dict[str, Any]) -> Optional[Path]:
    path = Path(config.path or (PROJECT_ROOT / "config.json"))
    backup_dir = PROJECT_ROOT / "data" / "config-history"
    backup: Optional[Path] = None
    if path.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        # Microseconds, because two edits in the same second would otherwise overwrite
        # each other's archive — the one case where you most want both copies.
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        backup = backup_dir / f"config-{stamp}.json"
        shutil.copy2(path, backup)
        shutil.copy2(path, path.with_suffix(".json.bak"))

    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)  # atomic swap, so a crash cannot leave half a config
    return backup


# --- secrets -------------------------------------------------------------
def _env_path() -> Path:
    return PROJECT_ROOT / ".env"


def env_template() -> str:
    """The starting .env: every known secret, blank, with instructions and a link."""
    lines = [ENV_TEMPLATE_HEADER]
    for key, meta in SECRET_META.items():
        lines.append(f"# {meta['label']} — {meta['purpose']}")
        lines.append(f"#   How: {meta['how']}")
        if meta["url"]:
            lines.append(f"#   Where: {meta['url']}")
        lines.append(f"{key}=")
        lines.append("")
    return "\n".join(lines)


def ensure_env_file(path: Optional[Path] = None) -> bool:
    """Create .env if it does not exist. Returns True when it was just created.

    There is no "copy the example file" step: the first command that needs secrets writes a
    documented, blank .env (mode 600) and tells you where to fill it in.
    """
    path = Path(path) if path else _env_path()
    if path.exists():
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(env_template(), encoding="utf-8")
        path.chmod(0o600)
    except OSError:
        return False
    return True


def secret_help() -> List[Dict[str, str]]:
    """Per-secret guidance for the settings page: what it is, how to get it, and where."""
    return [{"key": key, **meta} for key, meta in SECRET_META.items()]


def mask(value: Optional[str]) -> str:
    if not value:
        return ""
    value = str(value)
    return "•" * max(0, len(value) - 4) + value[-4:] if len(value) > 4 else "•" * len(value)


def secrets_status() -> List[Dict[str, Any]]:
    """Which secrets are set, masked — never the actual values. Creates .env if missing."""
    ensure_env_file()
    env = load_env()
    return [
        {
            "key": key,
            "label": SECRET_META.get(key, {}).get("label", key),
            "purpose": SECRET_META.get(key, {}).get("purpose", ""),
            "how": SECRET_META.get(key, {}).get("how", ""),
            "url": SECRET_META.get(key, {}).get("url", ""),
            "set": bool((env.get(key) or "").strip()),
            "masked": mask(env.get(key)),
            "from_environment": bool(os.environ.get(key)),
        }
        for key in KNOWN_SECRETS
    ]


def update_secrets(changes: Dict[str, str]) -> Dict[str, Any]:
    """Set or clear secrets in .env. Values are never echoed back."""
    unknown = sorted(set(changes) - set(KNOWN_SECRETS))
    if unknown:
        raise SettingsError(
            f"unknown secret(s): {', '.join(unknown)}. Known: {', '.join(KNOWN_SECRETS)}"
        )
    ensure_env_file()
    path = _env_path()
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen = set()
    output: List[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in changes:
                seen.add(key)
                value = (changes[key] or "").strip()
                output.append(f"{key}={value}")
                continue
        output.append(line)

    for key, value in changes.items():
        if key not in seen:
            output.append(f"{key}={(value or '').strip()}")

    path.write_text("\n".join(output).rstrip("\n") + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)  # keep credentials off other accounts on shared machines
    except OSError:
        pass
    for key, value in changes.items():
        if os.environ.get(key) and not (value or "").strip():
            os.environ.pop(key, None)
        elif (value or "").strip() and key in os.environ:
            os.environ[key] = value.strip()
    return {
        "updated": sorted(changes),
        "note": "Secrets are stored in .env (chmod 600) and never returned by the API.",
    }
