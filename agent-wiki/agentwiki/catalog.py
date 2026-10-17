"""What has been seen, queued, processed or failed. The dedupe check lives here."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
  video_id TEXT PRIMARY KEY, channel_id TEXT, title TEXT, status TEXT NOT NULL,
  priority INTEGER DEFAULT 0, attempts INTEGER DEFAULT 0, error TEXT,
  stage TEXT, published TEXT, page TEXT, added_at TEXT, updated_at TEXT);
CREATE INDEX IF NOT EXISTS videos_status ON videos(status, priority);
CREATE TABLE IF NOT EXISTS channels (
  channel_id TEXT PRIMARY KEY, name TEXT, url TEXT, auto_check INTEGER DEFAULT 1,
  added_at TEXT, last_checked TEXT);
"""

# queued -> processing -> done | failed | skipped
STATUSES = ("queued", "processing", "done", "failed", "skipped")
PRIORITY_MANUAL, PRIORITY_NEW, PRIORITY_BACKFILL = 100, 50, 0


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Catalog:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.database = sqlite3.connect(path)
        self.database.row_factory = sqlite3.Row
        self.database.executescript(SCHEMA)

    # ---- videos ------------------------------------------------------------

    def get(self, video_id: str) -> dict | None:
        row = self.database.execute("SELECT * FROM videos WHERE video_id=?", (video_id,)).fetchone()
        return dict(row) if row else None

    def has(self, video_id: str) -> bool:
        return self.get(video_id) is not None

    def enqueue(self, video_id: str, *, channel_id: str = "", title: str = "",
                priority: int = PRIORITY_NEW) -> bool:
        """Queue a video if it has never been seen. Returns True if it was new.

        A known video keeps its status; only its priority can go up, so adding
        a backfilled video by hand moves it to the front of the queue.
        """
        with self.database:
            cursor = self.database.execute(
                "INSERT OR IGNORE INTO videos (video_id, channel_id, title, status, priority, "
                "added_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (video_id, channel_id, title, "queued", priority, now(), now()))
            if cursor.rowcount == 0:
                self.database.execute("UPDATE videos SET priority=MAX(priority, ?) WHERE video_id=?",
                                      (priority, video_id))
                return False
            return True

    def requeue(self, video_id: str, priority: int | None = None) -> None:
        with self.database:
            self.database.execute(
                "UPDATE videos SET status='queued', attempts=0, error=NULL, updated_at=?, "
                "priority=COALESCE(?, priority) WHERE video_id=?", (now(), priority, video_id))

    def next_queued(self, max_attempts: int) -> dict | None:
        row = self.database.execute(
            "SELECT * FROM videos WHERE (status='queued' OR (status='failed' AND attempts<?)) "
            "ORDER BY status='failed', priority DESC, published DESC, added_at LIMIT 1",
            (max_attempts,)).fetchone()
        return dict(row) if row else None

    def update(self, video_id: str, **fields) -> None:
        fields["updated_at"] = now()
        columns = ", ".join(f"{column}=?" for column in fields)
        with self.database:
            self.database.execute(f"UPDATE videos SET {columns} WHERE video_id=?",
                                  (*fields.values(), video_id))

    def mark_failed(self, video_id: str, error: str) -> None:
        with self.database:
            self.database.execute("UPDATE videos SET status='failed', attempts=attempts+1, error=?, "
                                  "updated_at=? WHERE video_id=?", (error[:2000], now(), video_id))

    def counts(self) -> dict[str, int]:
        out = {status: 0 for status in STATUSES}
        for row in self.database.execute("SELECT status, COUNT(*) FROM videos GROUP BY status"):
            out[row[0]] = row[1]
        return out

    def list(self, status: str | None = None, limit: int = 50) -> list[dict]:
        if status:
            rows = self.database.execute("SELECT * FROM videos WHERE status=? ORDER BY updated_at DESC "
                                         "LIMIT ?", (status, limit))
        else:
            rows = self.database.execute("SELECT * FROM videos ORDER BY updated_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in rows]

    def find_by_title(self, text: str, limit: int = 10) -> list[dict]:
        """Videos whose title is `text` exactly (ignoring case), else contains it."""
        exact = self.database.execute("SELECT * FROM videos WHERE lower(title)=lower(?)", (text,)).fetchall()
        if exact:
            return [dict(row) for row in exact]
        rows = self.database.execute("SELECT * FROM videos WHERE title LIKE ? ORDER BY published DESC LIMIT ?",
                                     (f"%{text}%", limit))
        return [dict(row) for row in rows]

    def all_ids(self, status: str | None = None) -> list[str]:
        query_text = "SELECT video_id FROM videos" + (" WHERE status=?" if status else "")
        return [row[0] for row in self.database.execute(query_text, (status,) if status else ())]

    def reset_stuck(self) -> int:
        """`processing` rows left behind by a crash go back to the queue."""
        with self.database:
            return self.database.execute(
                "UPDATE videos SET status='queued' WHERE status='processing'").rowcount

    # ---- channels ----------------------------------------------------------

    def add_channel(self, channel_id: str, name: str, url: str) -> bool:
        with self.database:
            cursor = self.database.execute(
                "INSERT OR IGNORE INTO channels (channel_id, name, url, added_at) "
                "VALUES (?,?,?,?)", (channel_id, name, url, now()))
            return cursor.rowcount == 1

    def remove_channel(self, key: str) -> bool:
        with self.database:
            return self.database.execute("DELETE FROM channels WHERE channel_id=? OR name=? OR url=?",
                                         (key, key, key)).rowcount > 0

    def channels(self) -> list[dict]:
        return [dict(row) for row in self.database.execute("SELECT * FROM channels ORDER BY name")]

    def find_channel(self, key: str) -> dict | None:
        row = self.database.execute("SELECT * FROM channels WHERE channel_id=? OR name=? OR url=? "
                                    "OR url LIKE ?", (key, key, key, f"%{key.lstrip('@')}%")).fetchone()
        return dict(row) if row else None

    def touch_channel(self, channel_id: str) -> None:
        with self.database:
            self.database.execute("UPDATE channels SET last_checked=? WHERE channel_id=?",
                                  (now(), channel_id))
