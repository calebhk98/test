# Setup and daily operation

Everything needed to get the daily job running, and to keep it running on a schedule.

[← back to the README](../README.md)

---

## Setup

```bash
cd used-car-monitor
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

The first `carmon` command creates a `.env` for you — blank, `chmod 600`, gitignored, with
every secret listed and a link to where each one comes from. There is nothing to copy.

### Get a MarketCheck API key (free tier)

1. Go to <https://www.marketcheck.com/apis> (developer portal: <https://docs.marketcheck.com>)
   and sign up for the **free plan**: 500 calls/month, 5 calls/sec, 100-mile radius cap, $0/mo.
2. Copy your key into `.env`:

   ```
   MARKETCHECK_API_KEY=your_key_here
   ```

`.env` is gitignored. Nothing in this repo ever writes your key to disk anywhere else, and
`GET /api/config` deliberately serves `config.json` only — secrets live exclusively in `.env`.

**The free tier is never silently exceeded.** Every API call is logged to the `api_usage`
table, the client refuses to start a request once `api.monthly_call_cap` (500) is reached,
requests are throttled to 5/sec, and a radius above 100 miles is clamped with a warning.
Usage shows up in the digest, on the website, and in `python3 -m carmon stats`.
Upgrading the plan means editing `api.monthly_call_cap` yourself — the code will not do it.

### Discord (optional): direct message or server channel

Pick one transport. `discord.mode` in `config.json` is `"auto"` — DM if a bot is configured,
webhook otherwise — or force it with `"dm"` / `"webhook"` (or `--mode` on the command line).

**(a) Direct message — no server channel.** The digest lands in your Discord DMs, like a
message from a friend.

1. <https://discord.com/developers/applications> → **New Application** → **Bot** → **Reset
   Token**, and copy the token into `.env` as `DISCORD_BOT_TOKEN`.
2. Discord Settings → **Advanced → Developer Mode**, then right-click your own name →
   **Copy User ID** → `.env` as `DISCORD_USER_ID`.
3. One unavoidable Discord rule: **a bot may only DM a user it shares a server with.** That
   is the platform's rule, not this project's, and there is no way around it. The standard
   workaround is a private server containing just you and the bot (Discord → **+** → *Create
   My Own*, then invite the bot from the developer portal's OAuth2 URL generator with the
   `bot` scope). You never have to open that server — the digest still arrives as a DM.
   Also keep **Privacy Settings → Allow direct messages from server members** on.

**(b) Server webhook.** Simpler, but always posts into a channel: Discord → **Server Settings
→ Integrations → Webhooks → New Webhook → Copy URL** → `.env` as `DISCORD_WEBHOOK_URL`.

Leave both unset and the run just skips the message. Test either one with
`python3 -m carmon notify --mode dm` (or `--mode webhook`).

## Try it without an API key

```bash
python3 -m carmon seed-demo      # 18 realistic fake listings, tagged source='demo'
python3 -m carmon enrich         # attach REAL NHTSA + EPA data to them (no key needed)
python3 -m carmon digest --days 30
python3 -m carmon serve          # http://127.0.0.1:8787
python3 -m carmon seed-demo --clear
```

**Demo data cannot be mistaken for real inventory.** It is tagged `source='demo'` and:

* a real `carmon run` **deletes every demo row before storing anything** — the two never mix;
* it **expires by itself** after `demo.auto_clear_hours` (default 12); any command, including
  the web server, clears it once stale;
* while it exists, every surface says so out loud — a stderr warning on each CLI command, a
  red banner on every web page, a `DEMO` badge on each listing, a `⚠️ DEMO DATA` field at the
  top of the Discord message, a blockquote in the digest, and a `warning` field in the API and
  MCP payloads.

---

## Run it manually

```bash
python3 -m carmon run                 # fetch → enrich → store → score → digest → Discord
python3 -m carmon run --dry-run       # hit the APIs, print the digest, write nothing
python3 -m carmon run --no-discord    # skip the Discord post
python3 -m carmon digest --days 7     # re-render from stored data, zero API calls
python3 -m carmon enrich              # refresh NHTSA + EPA data, then rescore (no MarketCheck calls)
python3 -m carmon reliability --make Honda --model Civic --year 2022
python3 -m carmon appraise --make Toyota --model Corolla --year 2022 --mileage 35000 --price 17500
python3 -m carmon deals               # active listings ranked by price versus expected
python3 -m carmon market              # price trends, days on market, per-model stats
python3 -m carmon quota               # calls used vs how much of the month has passed
python3 -m carmon stats               # DB + quota stats as JSON
python3 -m carmon config-check        # validate config.json and report drift
python3 -m carmon score --make Nissan --model Sentra --mileage 45000 --distance 70
python3 -m carmon sources             # cross-shopping links (see SOURCES.md)
python3 -m carmon notify --mode dm    # send the digest as a Discord direct message
python3 -m carmon selftest            # run the bundled test suite
```

A run costs **5 API calls by default** (5 pages of up to 50 listings), plus 2 more for the
certified pass — about 7/day, ~210/month against the 500 cap. Tune with `search.max_pages`
and `search.certified_max_pages` in `config.json`.

---

## Schedule it daily (Windows, macOS or Linux)

```bash
python3 -m carmon cron --at 7:30                      # detects your OS
python3 -m carmon cron --at 7:30 --platform windows   # force the Windows form
```

**Linux / macOS** — it prints the crontab line and a one-liner to install it:

```
30 7 * * * cd /path/to/used-car-monitor && /usr/bin/python3 -m carmon run >> /path/to/used-car-monitor/data/cron.log 2>&1
```

On Linux you can instead use the systemd units in `deploy/` (`carmon.service` + `carmon.timer`,
plus `carmon-web.service` to keep the website up).

**Windows** — it prints a Task Scheduler command to run once in an Administrator prompt:

```
schtasks /Create /SC DAILY /ST 07:30 /TN "UsedCarMonitor" /TR "cmd /c cd /d C:\path\to\used-car-monitor && \"C:\Python311\python.exe\" -m carmon run >> \"C:\path\to\used-car-monitor/data/run.log\" 2>&1"
```

plus the `/Query`, `/Run` and `/Delete` forms. In the Task Scheduler GUI, tick *"Run task as
soon as possible after a scheduled start is missed"* so a sleeping laptop catches up.

### Does this run on Windows?

Yes — Windows, macOS and Linux, from the same checkout. It is pure Python 3.11 standard
library plus `requests`: `pathlib` for every path, `sqlite3` for storage (no server to
install), `http.server` for the website, and no shell-outs, symlinks, or POSIX-only calls
anywhere. Concretely:

* **Paths** in `config.json` are relative and resolved with `pathlib`, so `data/carmon.db`
  works unchanged on both `C:\` and `/home`.
* **Text** is read and written as explicit UTF-8, and the CLI reconfigures stdout/stderr to
  UTF-8 at startup — without that, the pace gauge and status icons crash a *redirected*
  Windows run with `UnicodeEncodeError`, which is exactly what a scheduled task does.
* **Scheduling** is the only genuinely OS-specific part, which is why `carmon cron` emits the
  right form per platform. The systemd units in `deploy/` are Linux-only by nature.

The database file is portable: copy `data/carmon.db` between machines and the history,
scores and NHTSA cache come with it.

---

Next: [where the data comes from](data-sources.md) · [configuration and scoring](configuration.md)
