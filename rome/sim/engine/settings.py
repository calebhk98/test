"""Where a player's stuff lives, and what they told the menu to remember.

Two different things share this file, and the difference matters:

  1. THE CONFIG - a handful of preferences (where saves go, what the New
     Game wizard should default to) that live OUTSIDE any one game, at a
     fixed place on disk, and are read again on the NEXT invocation of the
     process. This is what makes "put my saves somewhere else" stick without
     a flag: see PLAYER REQUEST #1 below.

  2. PER-SESSION META - a couple of fields (right now, just the horizon) that
     belong to one save file but are not part of the save format the engine
     itself owns (rome/sim/engine/protocol.py: SAVE_FIELDS, save_state,
     load_state). That file is rewritten from a fixed field list after every
     single command, so anything written here is not preserved there. It
     gets a small sidecar of its own instead.

Nothing in this module is imported by, or imports, protocol.py/core.py/
projects.py/labour.py/society.py/economy.py: it is filesystem bookkeeping
around the engine, not the engine.

PLAYER REQUEST #1 - "saves in a place that survives": several players run
somewhere the default save directory (~/.rome-saves) is not the durable
storage they actually have - a fresh container on every terminal session,
with a persistent volume mounted somewhere else entirely. Three ways to say
where saves should go, checked in this order, so whichever one actually
survives in a given environment works:

  1. the ROME_SAVE_DIR environment variable, for a player who can export
     one line in a shell profile that DOES survive even when $HOME does not
  2. "save_dir" in the config file (see CONFIG_PATH below), for a player who
     sets it once from the Options menu and whose home directory is the
     thing that survives
  3. ~/.rome-saves, unchanged, for everyone who has not asked for anything
     else
"""
import json
import os
import time


# ---------------------------------------------------------------------------
# The config file: a handful of preferences that outlive any one game.
# ---------------------------------------------------------------------------

# ROME_SIM_CONFIG lets a player put the config file itself somewhere durable,
# for the same reason ROME_SAVE_DIR exists: an environment where $HOME does
# not survive between terminal sessions cannot be fixed by writing a dotfile
# into $HOME, however sensible that dotfile is everywhere else.
SAVE_DIR_ENV = "ROME_SAVE_DIR"
CONFIG_PATH_ENV = "ROME_SIM_CONFIG"

_DEFAULT_SAVE_DIR = os.path.join(os.path.expanduser("~"), ".rome-saves")
_DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".rome-sim-config.json")

# What the New Game wizard offers before a player has ever changed anything,
# and what a bare `play`/`agent` invocation still uses - identical to the
# flag defaults in main() (data.DEFAULTS, STARTING_KITS), repeated here as
# plain values rather than imported, so this module never has to import the
# engine to know what "unset" means.
CONFIG_DEFAULTS = {
    "save_dir": None,          # None means "use the rule above"
    "default_civ": "rome_100ad",
    "default_kit": "poor_scholar",
    "default_fog": True,
    "default_mortal": False,
    "default_horizon": 500,
}


def config_path():
    return os.environ.get(CONFIG_PATH_ENV) or _DEFAULT_CONFIG_PATH


def load_config():
    """The player's saved preferences, or CONFIG_DEFAULTS if there are none
    yet or the file cannot be read. Never raises: a corrupt or missing
    config is a fresh install, not an error a player should see."""
    cfg = dict(CONFIG_DEFAULTS)
    try:
        with open(config_path()) as fh:
            raw = json.load(fh)
        if isinstance(raw, dict):
            for k in CONFIG_DEFAULTS:
                if k in raw:
                    cfg[k] = raw[k]
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    """Write the preferences back. Atomic, like the game's own save_state,
    for the same reason: a crash mid-write must not leave a config file that
    loads as neither the old preferences nor the new ones."""
    path = config_path()
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except OSError:
            return False
    out = {k: cfg.get(k, CONFIG_DEFAULTS[k]) for k in CONFIG_DEFAULTS}
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def resolve_save_dir(cfg=None, ensure=True):
    """Where saves go right now, in order: ROME_SAVE_DIR, the config file's
    save_dir, then ~/.rome-saves. Creates the directory if it does not exist
    yet and `ensure` is true; falls back to "." if it cannot be created or
    written to at all, the same fallback _pick_session_filename always had."""
    env = os.environ.get(SAVE_DIR_ENV)
    if env:
        d = os.path.expanduser(env)
    else:
        if cfg is None:
            cfg = load_config()
        d = cfg.get("save_dir") or _DEFAULT_SAVE_DIR
        d = os.path.expanduser(d)
    if ensure:
        try:
            os.makedirs(d, exist_ok=True)
            # Confirm it is actually writable, not merely present - a
            # directory that exists but is read-only would otherwise surface
            # as a save failure deep inside the game instead of here, where
            # the player is choosing a location and can pick another one.
            probe = os.path.join(d, ".rome-write-test")
            with open(probe, "w"):
                pass
            os.remove(probe)
        except OSError:
            return "."
    return d


# ---------------------------------------------------------------------------
# Per-session meta: the one field (horizon) a save's own file cannot carry.
# ---------------------------------------------------------------------------

def _meta_path(session):
    return session + ".meta.json" if session else None


def load_session_meta(session):
    """{} if there is no sidecar yet, or it cannot be read - never raises,
    the same policy as load_config: an absent or corrupt sidecar is exactly
    what an ordinary flag-driven save (never touched by the menu or the
    in-game options command) always has."""
    path = _meta_path(session)
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            v = json.load(fh)
        return v if isinstance(v, dict) else {}
    except (OSError, ValueError):
        return {}


def save_session_meta(session, meta):
    path = _meta_path(session)
    if not path:
        return False
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as fh:
            json.dump(meta, fh, indent=1, sort_keys=True)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def move_session_meta(old_session, new_session):
    """Carry the sidecar along when a save is moved to a new path. Losing it
    silently would not corrupt anything - see load_session_meta - it would
    just quietly forget a horizon the player deliberately changed, which is
    exactly the kind of small unannounced loss a save-relocation feature
    exists to never cause."""
    old_meta = load_session_meta(old_session)
    old_path = _meta_path(old_session)
    if old_meta:
        save_session_meta(new_session, old_meta)
    if old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Listing saves, for "Load a saved game".
# ---------------------------------------------------------------------------

def list_saves(save_dir):
    """One summary dict per save file in `save_dir`, newest-written first.

    Reads the JSON directly rather than going through the engine's
    load_state: this runs before any Sim exists (the whole point is to help
    a player choose which one to build), and it must not refuse a file just
    because it looks odd - a save this listing cannot make sense of is still
    shown, with what little can be read from it, rather than silently
    dropped from the list a player is choosing a filename out of.
    """
    out = []
    try:
        names = os.listdir(save_dir)
    except OSError:
        return out
    for fn in sorted(names):
        if not fn.endswith(".json") or fn.endswith(".meta.json"):
            continue
        path = os.path.join(save_dir, fn)
        try:
            st = os.stat(path)
        except OSError:
            continue
        if st.st_size == 0:
            # A slot claimed by _pick_session_filename's O_EXCL but never
            # actually played into - see cli.py's _is_claimed_slot. Not a
            # save; skip it rather than show a player an entry that errors
            # the moment they pick it.
            continue
        row = {"path": path, "filename": fn, "mtime": st.st_mtime,
               "readable": False}
        try:
            with open(path) as fh:
                blob = json.load(fh)
            if not isinstance(blob, dict) or "_civ" not in blob:
                continue
            row.update({
                "readable": True,
                "civ_id": blob.get("_civ"),
                "year": blob.get("year"),
                "fog": bool(blob.get("_fog", False)),
                "founder_alive": blob.get("founder_alive", True),
                "dead_reason": blob.get("dead_reason"),
                "goal_year": blob.get("goal_year"),
                "reputation": blob.get("reputation"),
                "scholars": blob.get("scholars"),
                "artisans": blob.get("artisans"),
                "capital": blob.get("capital"),
                "done": ((blob.get("done") or {}).get("__set__") or []),
            })
        except (OSError, ValueError):
            pass
        out.append(row)
    out.sort(key=lambda r: -r["mtime"])
    return out


def humanize_age(mtime):
    """'3 minutes ago', 'yesterday', 'on 2026-03-01' - roughly, not exactly:
    a player choosing between saves wants a sense of how stale one is, not a
    timestamp to do arithmetic on."""
    delta = max(0, time.time() - mtime)
    if delta < 90:
        return "moments ago"
    mins = delta / 60
    if mins < 90:
        return "%d minutes ago" % mins
    hours = mins / 60
    if hours < 36:
        return "%d hours ago" % hours
    days = hours / 24
    if days < 2:
        return "yesterday"
    if days < 14:
        return "%d days ago" % days
    return time.strftime("on %Y-%m-%d", time.localtime(mtime))
