"""Digest rendering and Discord delivery."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon import db, demo, digest as digest_module, notify
from carmon.config import load_config


class FakeResponse:
    def __init__(self, status_code=204, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class FakeDiscord:
    def __init__(self, statuses=(204,)):
        self.statuses = list(statuses)
        self.posts = []

    def post(self, url, json=None, timeout=None):
        self.posts.append({"url": url, "payload": json})
        status = self.statuses.pop(0) if self.statuses else 204
        return FakeResponse(status, {"retry_after": 0.01}, text="err")


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "t.db")
        self.config.data["paths"]["digest_dir"] = str(self.tmp / "digests")
        self.conn = db.init_db(self.config.db_path)
        demo.seed(self.config, self.conn, count=8)

    def tearDown(self):
        self.conn.close()

    def test_digest_has_all_three_sections(self):
        markdown = digest_module.render_digest(self.config, self.conn, days=30)
        self.assertIn("# Used Car Daily Digest", markdown)
        self.assertIn("## New since", markdown)
        self.assertIn("## Price drops since", markdown)
        self.assertIn("## Top 5 overall by score", markdown)

    def test_digest_reports_api_quota(self):
        markdown = digest_module.render_digest(self.config, self.conn)
        self.assertIn("MarketCheck calls this month", markdown)
        self.assertIn("/ 500", markdown)

    def test_digest_includes_cross_shop_links(self):
        markdown = digest_module.render_digest(self.config, self.conn)
        self.assertIn("Cross-shop the same search", markdown)
        self.assertIn("CarGurus", markdown)
        self.assertIn("Toyota Certified", markdown)
        self.assertIn("does not scrape", markdown)

    def test_digest_shows_score_reasons(self):
        markdown = digest_module.render_digest(self.config, self.conn, days=30)
        self.assertIn("why:", markdown, "the digest must show why something scored well")

    def test_digest_is_saved_and_found_again(self):
        markdown = digest_module.render_digest(self.config, self.conn)
        path = digest_module.save_digest(self.config, markdown, run_date="2026-08-18")
        self.assertTrue(path.exists())
        self.assertEqual(digest_module.latest_digest_path(self.config), path)
        self.assertEqual(digest_module.latest_digest_text(self.config), markdown)

    def test_empty_database_still_renders(self):
        empty_conn = db.init_db(self.tmp / "empty.db")
        markdown = digest_module.render_digest(self.config, empty_conn)
        self.assertIn("Nothing new today.", markdown)
        self.assertIn("No listings stored yet.", markdown)
        empty_conn.close()


class DiscordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "t.db")
        self.conn = db.init_db(self.config.db_path)
        demo.seed(self.config, self.conn, count=8)

    def tearDown(self):
        self.conn.close()

    def test_payload_shape_is_discord_compatible(self):
        payload = notify.build_discord_payload(self.config, self.conn, run_date="2026-08-18", days=30)
        embed = payload["embeds"][0]
        self.assertIn("Used Car Daily Digest", embed["title"])
        self.assertLessEqual(len(embed["fields"]), 25)
        for field in embed["fields"]:
            self.assertLessEqual(len(field["value"]), 1024, "Discord rejects fields over 1024 chars")
            self.assertTrue(field["value"].strip())
        names = " ".join(f["name"] for f in embed["fields"])
        self.assertIn("New since", names)
        self.assertIn("Price drops", names)
        self.assertIn("Top", names)
        self.assertIn("Status", names)

    def test_status_field_reports_quota(self):
        payload = notify.build_discord_payload(self.config, self.conn)
        status = next(f for f in payload["embeds"][0]["fields"] if f["name"] == "Status")
        self.assertIn("MarketCheck quota", status["value"])

    def test_send_digest_posts_once(self):
        fake = FakeDiscord()
        notify.send_digest(self.config, self.conn, webhook_url="https://discord.test/hook", session=fake)
        self.assertEqual(len(fake.posts), 1)
        self.assertEqual(fake.posts[0]["url"], "https://discord.test/hook")

    def test_rate_limit_is_retried(self):
        fake = FakeDiscord(statuses=[429, 204])
        self.assertTrue(notify.post_to_discord("https://discord.test/hook", {"content": "hi"}, session=fake))
        self.assertEqual(len(fake.posts), 2)

    def test_hard_failure_raises(self):
        fake = FakeDiscord(statuses=[404])
        with self.assertRaises(notify.DiscordError):
            notify.post_to_discord("https://discord.test/hook", {"content": "hi"}, session=fake)

    def test_missing_webhook_raises_clear_error(self):
        with self.assertRaises(notify.DiscordError) as ctx:
            notify.post_to_discord("", {"content": "hi"})
        self.assertIn("DISCORD_WEBHOOK_URL", str(ctx.exception))

    def test_long_text_is_chunked(self):
        fake = FakeDiscord(statuses=[204, 204, 204])
        notify.send_text("https://discord.test/hook", "x" * 4100, session=fake)
        self.assertEqual(len(fake.posts), 3)
        for post in fake.posts:
            self.assertLessEqual(len(post["payload"]["content"]), 2000)


if __name__ == "__main__":
    unittest.main()
