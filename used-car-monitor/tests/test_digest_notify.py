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
    """Stands in for `requests`, for both the webhook and bot-DM transports."""

    def __init__(self, statuses=(204,), dm_channel_id="dm-channel-1"):
        self.statuses = list(statuses)
        self.posts = []
        self.dm_channel_id = dm_channel_id

    def post(self, url, json=None, timeout=None, headers=None):
        self.posts.append({"url": url, "payload": json, "headers": headers or {}})
        if url.endswith("/users/@me/channels"):
            return FakeResponse(200, {"id": self.dm_channel_id})
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

    def test_digest_reports_api_quota_with_pace(self):
        markdown = digest_module.render_digest(self.config, self.conn)
        self.assertIn("MarketCheck quota", markdown)
        self.assertIn("/ 500", markdown)
        self.assertIn("expected ~", markdown)
        self.assertIn("x pace", markdown)
        self.assertIn("still affordable", markdown)

    def test_digest_warns_loudly_about_demo_data(self):
        markdown = digest_module.render_digest(self.config, self.conn)
        self.assertIn("DEMO DATA", markdown)
        self.assertIn("not real cars", markdown)

    def test_digest_reports_a_month_end_sweep(self):
        markdown = digest_module.render_digest(
            self.config, self.conn,
            run_result={"fetched": 20, "kept": 8, "api_calls": 40,
                        "sweep": {"ran": True, "calls_used": 37,
                                  "queries": [{"label": "deep pagination", "listings": 50}]}},
        )
        self.assertIn("Month-end sweep", markdown)
        self.assertIn("37", markdown)
        self.assertIn("expired tonight", markdown)

    def test_digest_names_newly_looked_up_models(self):
        markdown = digest_module.render_digest(
            self.config, self.conn,
            run_result={"enrichment": {"nhtsa": {"api_calls": 4,
                                                 "new_models": ["2022 Kia Forte (31 complaints, 1 recalls)"]}}},
        )
        self.assertIn("first NHTSA lookup: 2022 Kia Forte", markdown)

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
        transport = notify.send_digest(
            self.config, self.conn, webhook_url="https://discord.test/hook",
            session=fake, mode="webhook",
        )
        self.assertEqual(transport, "webhook")
        self.assertEqual(len(fake.posts), 1)
        self.assertEqual(fake.posts[0]["url"], "https://discord.test/hook")

    def test_status_field_reports_quota_pace(self):
        payload = notify.build_discord_payload(self.config, self.conn)
        status = next(f for f in payload["embeds"][0]["fields"] if f["name"] == "Status")
        self.assertIn("pace", status["value"])
        self.assertIn("expected ~", status["value"])

    def test_demo_data_is_flagged_in_the_message(self):
        payload = notify.build_discord_payload(self.config, self.conn)
        first = payload["embeds"][0]["fields"][0]
        self.assertIn("DEMO", first["name"])
        self.assertIn("not real cars", first["value"])

    def test_month_end_sweep_is_reported(self):
        payload = notify.build_discord_payload(
            self.config, self.conn,
            run_result={"fetched": 10, "kept": 5, "api_calls": 30,
                        "sweep": {"ran": True, "calls_used": 24}},
        )
        status = next(f for f in payload["embeds"][0]["fields"] if f["name"] == "Status")
        self.assertIn("sweep", status["value"].lower())
        self.assertIn("24", status["value"])


class DiscordTransportTests(unittest.TestCase):
    """Direct-message transport and transport selection."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config = load_config()
        self.config.data["paths"]["db"] = str(self.tmp / "t.db")
        self.conn = db.init_db(self.config.db_path)
        demo.seed(self.config, self.conn, count=4)

    def tearDown(self):
        self.conn.close()

    def test_dm_opens_a_channel_then_posts_to_it(self):
        fake = FakeDiscord()
        transport = notify.send_digest(
            self.config, self.conn, session=fake, mode="dm",
            bot_token="bot-token", user_id="123456789",
        )
        self.assertEqual(transport, "dm")
        self.assertEqual(len(fake.posts), 2)
        self.assertTrue(fake.posts[0]["url"].endswith("/users/@me/channels"))
        self.assertEqual(fake.posts[0]["payload"], {"recipient_id": "123456789"})
        self.assertEqual(fake.posts[0]["headers"]["Authorization"], "Bot bot-token")
        self.assertIn("/channels/dm-channel-1/messages", fake.posts[1]["url"])
        self.assertIn("embeds", fake.posts[1]["payload"])

    def test_dm_payload_drops_webhook_only_fields(self):
        fake = FakeDiscord()
        notify.send_digest(self.config, self.conn, session=fake, mode="dm",
                           bot_token="t", user_id="1")
        self.assertNotIn("username", fake.posts[1]["payload"],
                         "username/avatar_url are webhook-only and Discord rejects them on DMs")

    def test_auto_mode_prefers_dm_when_a_bot_is_configured(self):
        target = notify.resolve_transport(self.config, mode="auto", webhook_url="https://hook",
                                          bot_token="t", user_id="1")
        self.assertEqual(target["transport"], "dm")

    def test_auto_mode_falls_back_to_webhook(self):
        target = notify.resolve_transport(self.config, mode="auto", webhook_url="https://hook",
                                          bot_token="", user_id="")
        self.assertEqual(target["transport"], "webhook")

    def test_dm_mode_without_credentials_explains_what_is_missing(self):
        with self.assertRaises(notify.DiscordError) as ctx:
            notify.resolve_transport(self.config, mode="dm", webhook_url="https://hook",
                                     bot_token="", user_id="")
        self.assertIn("DISCORD_BOT_TOKEN", str(ctx.exception))

    def test_nothing_configured_at_all_is_a_clear_error(self):
        with self.assertRaises(notify.DiscordError) as ctx:
            notify.resolve_transport(self.config, mode="auto", webhook_url="", bot_token="", user_id="")
        self.assertIn("No Discord delivery configured", str(ctx.exception))

    def test_forbidden_dm_explains_the_shared_server_rule(self):
        fake = FakeDiscord(statuses=[403])
        with self.assertRaises(notify.DiscordError) as ctx:
            notify.post_to_dm("token", "123", {"content": "hi"}, session=fake)
        self.assertIn("share no server", str(ctx.exception))

    def test_missing_user_id_names_the_developer_mode_steps(self):
        with self.assertRaises(notify.DiscordError) as ctx:
            notify.open_dm_channel("token", "", session=FakeDiscord())
        self.assertIn("Developer Mode", str(ctx.exception))

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
