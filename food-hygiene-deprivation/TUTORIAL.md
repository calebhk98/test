# Build a Food-Hygiene + Deprivation database — student tutorial

You will build, from scratch, a MySQL database of UK food-hygiene ratings and use
it to ask whether hygiene varies by region, business type and deprivation, then
put a small web app in front of it.

The tutorial grows in **9 steps**. **Every step ends in a working state** with a
*Checkpoint* you can run to prove it works. Early steps are deliberately tiny (one
local authority, one table); later steps scale up and restructure. **It is normal
to replace or delete earlier code in a later step** — that is how real projects
evolve, and the tutorial tells you when.

One step (Step 2) writes no code at all: it teaches the *method* — how you'd work
out what to build from an unfamiliar dataset on your own, which is the part that
transfers to any future project.

> Work inside one project folder (whatever folder you were told to use). Every path
> below is relative to that folder. Create files exactly as shown.

> **A note on names — you can change almost any of them.** Names like the database
> `fhrs_tutorial`, the tables `establishment` / `region` / `local_authority` /
> `business_type`, the columns, and the read-only user `fhrs_read` are *our* choices,
> not rules. You could just as well call them `food_db`, `premises`, `outlets`,
> `report_user`, and so on. **This tutorial assumes the names shown below**, and
> we'll keep using them. If you rename one, change it **everywhere it appears** and
> stay consistent: the database name lives in `config.js` **and** in the
> `CREATE DATABASE` / `USE …;` lines of the `sql/*.sql` files; table and column
> names appear in the schema, the loader scripts and the queries. (File names like
> `load-one.js` are also free to change — just run the file you actually created.)

**What you need:** Node.js 18+ and MySQL or MariaDB. All commands assume you can run
`mysql` and that Node is installed. This tutorial uses a database called
`fhrs_tutorial`, so it will not touch any other database you may have.

---

## Step 1 — Project setup and a database connection

**Goal:** a Node project that can connect to MySQL and confirm the database exists.

**Try it first — why one config file and a socket connection?**
- Imagine hard-coding the host, user and password into *every* script. It works —
  until you rename the database and must edit every file (and miss one). Keeping the
  settings in `config.js` once is why we start there.
- Why connect as root over the local *socket* rather than TCP with a password? Once
  MySQL is running (step 1a, next), compare the two and see for yourself:
  ```bash
  mysql -e "SELECT 1"                       # over the socket as your OS user -> works, no password
  mysql -h 127.0.0.1 -u root -e "SELECT 1"  # forces TCP -> "Access denied for user 'root'"
  ```
  The socket trusts your operating-system user, so there's no password to manage for
  local work. (In Step 8 we go the opposite way and make a deliberately *limited*
  user for the web app.)

**1a. Make sure MySQL is running.** On a normal desktop install that is
`sudo service mysql start` (or `brew services start mariadb` on macOS). In a fresh
cloud container with no service manager, start it manually:

```bash
# Only needed if `mysqladmin ping` fails. Safe to copy-paste as-is.
mysqladmin ping 2>/dev/null || {
  mkdir -p /run/mysqld && chown mysql:mysql /run/mysqld
  [ -d /var/lib/mysql/mysql ] || mariadb-install-db --user=mysql >/dev/null 2>&1
  nohup mariadbd-safe --datadir=/var/lib/mysql >/tmp/mysqld.log 2>&1 &
  for i in $(seq 1 30); do mysqladmin ping --silent 2>/dev/null && break; sleep 1; done
}
mysqladmin ping
```

**1b. Create `package.json`:**

```json
{
  "name": "fhrs-tutorial",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "express": "^4.19.2",
    "fast-xml-parser": "^4.4.1",
    "mysql2": "^3.11.0",
    "xlsx": "^0.18.5"
  }
}
```

Install the dependencies:

```bash
npm install
```

> Whenever a later step says *Create `etl/load-one.js`*, it means a file
> `load-one.js` inside an `etl` folder. Most editors create the folder for you when
> you save; if you work from the terminal, make each folder the first time it
> appears — we add a `mkdir` reminder at that point. (You never need to create
> `data/` yourself; the download scripts make it.) We create folders only in the
> step that first uses them, never earlier.

**1c. Create `config.js`** — every script reads its database settings from here:

```js
// Central config. The loader connects as root over the local socket (no
// password); the web app later uses a read-only user. Override with env vars.
module.exports = {
  dbName: process.env.DB_NAME || 'fhrs_tutorial',
  socketPath: process.env.DB_SOCKET || '/run/mysqld/mysqld.sock',
  admin: { user: 'root' },                       // full access, used by ETL
  app:   { user: 'fhrs_read', password: 'readonly' }, // read-only, used by web app (Step 8)
};
```

> **Socket path.** The default above works on most Linux installs. If `node
> check-db.js` (next) fails with a socket error, find your socket with
> `mysqladmin variables | grep ' socket'`, then edit the `socketPath` line in
> `config.js` to that path (a common alternative is `/var/run/mysqld/mysqld.sock`).
> The plain `mysql < file` commands later in the tutorial use the same default
> socket automatically; if yours differs, add `--socket=/your/path` to them.

**1d. Create `check-db.js`:**

```js
const mysql = require('mysql2/promise');
const cfg = require('./config');
(async () => {
  const c = await mysql.createConnection({ socketPath: cfg.socketPath, user: cfg.admin.user });
  await c.query(`CREATE DATABASE IF NOT EXISTS \`${cfg.dbName}\`
                 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`);
  const [[v]] = await c.query('SELECT VERSION() AS version');
  console.log('Connected. Server:', v.version);
  console.log('Database ready:', cfg.dbName);
  await c.end();
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
```

**Checkpoint 1:**

```bash
node check-db.js
```

You should see `Connected. Server: …` and `Database ready: fhrs_tutorial`.

---

## Step 2 — Explore the data before you model it

**Goal:** learn the method you'd use for *any* unfamiliar dataset — find it, look
at it, understand its shape — and use it to justify the table you build next. This
step writes **no code and creates no database objects**; it's about looking before
you leap. (If you only ever follow recipes you never learn this part — so do it.)

When you're not following a tutorial, you don't begin by knowing the columns. You
find data and interrogate it. Here is a repeatable five-question method, applied to
the FHRS food-hygiene data.

**2a. Find the data (discoverability).**
- Start at an open-data catalogue — for the UK, <https://www.data.gov.uk>;
  elsewhere, data.gov, the EU data portal, or your city's portal. Search your topic
  (e.g. "food hygiene ratings").
- Prefer the **primary, official** source over a re-publisher. Here that is the Food
  Standards Agency open-data page, `https://ratings.food.gov.uk/open-data`. Good
  signs: the body that *produces* the data publishes it, it is **machine-readable**
  (XML/CSV/JSON, not a PDF), it is **documented**, and it is refreshed on a schedule.
- Check the **licence** (here, the Open Government Licence) so you know what you may
  do with it.

**2b. Get ONE small sample, not the whole thing.** Don't download 363 files to learn
the shape — grab one and look at it:

```bash
mkdir -p data
curl -fsSL -o data/sample.xml "https://ratings.food.gov.uk/OpenDataFiles/FHRS501en-GB.xml"
head -c 1200 data/sample.xml; echo
```

(For a CSV you would `head -5`; for JSON, pipe it through a formatter.)

**2c. Interrogate it — grain, key, fields, values, gaps.** These five questions
decide your schema. A few lines of Node let you *look* instead of guess:

```bash
node -e '
const {XMLParser}=require("fast-xml-parser");const fs=require("fs");
let e=new XMLParser({ignoreAttributes:false,parseTagValue:false})
  .parse(fs.readFileSync("data/sample.xml","utf8"))
  .FHRSEstablishment.EstablishmentCollection.EstablishmentDetail;
if(!Array.isArray(e)) e=[e];
console.log("rows in this one file:", e.length);
console.log("one row:", JSON.stringify(e[0],null,2));
console.log("distinct RatingValue:", [...new Set(e.map(x=>x.RatingValue))].join(", "));
console.log("rows with no RatingDate:", e.filter(x=>!x.RatingDate||typeof x.RatingDate==="object").length);
'
```

Read the output and answer:
- **Grain** — what is one row? (One rated establishment. That is your fact-table grain.)
- **Key** — what uniquely identifies a row? (`FHRSID` — your primary key.)
- **Fields & types** — name (text), postcode (text), `RatingDate` (a date),
  `Geocode` (two numbers), three component `Scores`…
- **Value surprises** — `RatingValue` isn't only 0–5: you'll also see
  `AwaitingInspection`, `Exempt`, and (in Scotland) `Pass`. Always list the *real*
  distinct values; assumptions lie.
- **What's missing** — `RatingDate` is absent for premises awaiting inspection, so
  that column must allow NULL.

**2d. Read the documentation.** A good dataset ships a schema/readme defining each
field. The FSA open-data page links field definitions (what `SchemeType` and the
`Scores` mean — e.g. that hygiene `Scores` are "lower is better", the opposite
direction to the headline rating). Docs confirm guesses and explain codes you
can't infer.

**2e. Turn observations into a table design.** Now every column we create in the
next step is *justified by something we saw*:

| What we observed | Schema decision (next step) |
|---|---|
| one row = one establishment | a single fact table |
| `FHRSID` is unique | `BIGINT PRIMARY KEY` |
| `RatingValue` mixes text and numbers | keep raw text **and** a nullable numeric column |
| `RatingDate` sometimes absent | `DATE NULL` |
| `Geocode` has lat/long | two `DECIMAL` columns |
| three component `Scores` | three `SMALLINT` columns |

**Checkpoint 2:** You can state, for this data, (a) what one row represents, (b) its
unique key, and (c) at least one `RatingValue` you wouldn't have guessed. If you ran
the Node snippet you saw ~1438 rows and a distinct `RatingValue` list including
`AwaitingInspection` and `Exempt`. No tables exist yet — but you now know exactly
what to build next, and why.

> **The method, reusable for any dataset:** find it (catalogue → primary,
> documented, machine-readable source) → sample **one** file → identify **grain,
> key, types, value surprises, and what's nullable** → read the **docs** → design
> the table from what you actually observed. We use this same method again in
> **Step 7** when we add a second dataset (deprivation) and have to work out how it
> joins to this one.

---

## Step 3 — Your first table

**Goal:** one table, `establishment`, to hold rated premises. No relationships yet
— we start as simple as possible.

**Try it first — why store the rating twice (as text *and* as a number)?**
One column seems simpler. Test both shortcuts in a throwaway table — `TEMPORARY`
tables disappear when you disconnect, so this can't hurt anything:
```bash
# A) a numeric-only column can't even hold the real data:
mysql fhrs_tutorial -e "CREATE TEMPORARY TABLE t(v TINYINT); INSERT INTO t VALUES ('5'),('AwaitingInspection');"
#   -> ERROR 1366: Incorrect integer value 'AwaitingInspection'  (you'd lose every un-rated premise)

# B) a text-only column stores everything but lies when you do maths:
mysql fhrs_tutorial -e "CREATE TEMPORARY TABLE t(v VARCHAR(30)); INSERT INTO t VALUES('5'),('5'),('Exempt'); SELECT AVG(v) FROM t;"
#   -> 3.33, because 'Exempt' silently became 0
```
So the table keeps **both**: `rating_value` (text — loses nothing) and
`rating_numeric` (NULL unless 0–5 — so averages stay honest). And the key: `fhrs_id`
is the FSA's own unique id, so making it the `PRIMARY KEY` means re-loading a file
can't silently create duplicate rows.

> *Naming:* we call this table `establishment`; you could call it `premises`,
> `outlets`, `food_business`, etc. We'll assume `establishment` from here on — if you
> choose another name, use it in every later query and script too.

This step introduces the `sql/` folder for your SQL files — from a terminal,
`mkdir -p sql` first (an editor will make it for you on save).

**3a. Create `sql/01_schema_single.sql`:**

```sql
CREATE DATABASE IF NOT EXISTS fhrs_tutorial
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fhrs_tutorial;

DROP TABLE IF EXISTS establishment;
CREATE TABLE establishment (
  fhrs_id        BIGINT PRIMARY KEY,         -- unique id from the FSA
  business_name  VARCHAR(255),
  business_type  VARCHAR(120),              -- text for now; we normalise it in Step 6
  post_code      VARCHAR(20),
  rating_value   VARCHAR(30),               -- '0'..'5', or 'AwaitingInspection', 'Pass', ...
  rating_numeric TINYINT NULL,              -- 0..5 when numeric, else NULL
  rating_date    DATE NULL,                 -- NULL = awaiting first inspection
  la_code        VARCHAR(10),
  scheme_type    VARCHAR(10),
  hygiene_score      SMALLINT NULL,          -- 0 = best, higher = worse (FHRS only)
  structural_score   SMALLINT NULL,
  confidence_score   SMALLINT NULL,
  longitude      DECIMAL(9,6) NULL,
  latitude       DECIMAL(8,6) NULL
) ENGINE=InnoDB;
```

**3b. Run it.** This `mysql` command connects as your system's root user over the
local socket (no password needed) — that is correct here; the read-only `fhrs_read`
user isn't created until Step 8.

```bash
mysql < sql/01_schema_single.sql
```

**Checkpoint 3:**

```bash
mysql fhrs_tutorial -e "SHOW TABLES; DESCRIBE establishment;"
```

You should see the `establishment` table and its columns.

---

## Step 4 — Load one local authority (small scale)

**Goal:** download a single authority's open-data file and load it. We use Barking
and Dagenham (FSA code 501, ~1,400 premises) so it is fast.

**Try it first — why one authority, and why `curl`?**
- Why not load all 363 now? One file is ~1,400 rows and downloads in a second, so
  you can get the parsing right before committing to ~600,000 rows. Scaling up
  before the small case works just makes every mistake slower to find.
- Why shell out to `curl` instead of Node's built-in `fetch`/`https`? On many
  corporate and cloud networks the proxy is configured for `curl` but not for Node,
  so `fetch` hangs while `curl` works — using `curl` keeps the tutorial portable.
- The loader runs `TRUNCATE establishment` before inserting. Run `node etl/load-one.js`
  twice: it stays at ~1,438 rows because of that truncate. Without it, the second
  run would fail on the `fhrs_id` primary key — the database refusing to double-load.

This step introduces the `etl/` folder for your data-loading scripts — from a
terminal, `mkdir -p etl` first (an editor will make it for you on save). The script
itself creates the `data/` download folder when it runs.

**4a. Create `etl/load-one.js`:**

```js
// Download ONE authority's FHRS open-data XML and load it into `establishment`.
// Uses curl so it works behind a corporate/cloud HTTPS proxy (Node's http does not
// read proxy env vars; curl does).
const fs = require('fs');
const { execFileSync } = require('child_process');
const mysql = require('mysql2/promise');
const { XMLParser } = require('fast-xml-parser');
const cfg = require('../config');  // '../' because this file lives in etl/; run it from the project root

const LA_CODE = '501';             // Barking and Dagenham
const URL = `https://ratings.food.gov.uk/OpenDataFiles/FHRS${LA_CODE}en-GB.xml`;

const txt = v => (v == null || typeof v === 'object') ? null : String(v).trim() || null;
const int = v => { const n = parseInt(txt(v), 10); return Number.isFinite(n) ? n : null; };
const num = v => { const n = parseFloat(txt(v)); return Number.isFinite(n) ? n : null; };
const date = v => { const s = txt(v); return s && /^\d{4}-\d{2}-\d{2}/.test(s) ? s.slice(0, 10) : null; };

(async () => {
  fs.mkdirSync('data/fhrs', { recursive: true });
  const file = `data/fhrs/FHRS${LA_CODE}.xml`;
  execFileSync('curl', ['-fsSL', '--retry', '3', '-o', file, URL]);
  console.log('Downloaded', file);

  const parser = new XMLParser({ ignoreAttributes: false, parseTagValue: false });
  const doc = parser.parse(fs.readFileSync(file, 'utf8'));
  let ests = doc.FHRSEstablishment.EstablishmentCollection.EstablishmentDetail;
  if (!Array.isArray(ests)) ests = [ests];

  const rows = ests.map(e => {
    const rv = txt(e.RatingValue);
    const sc = (e.Scores && typeof e.Scores === 'object') ? e.Scores : {};
    const g = e.Geocode || {};
    return [
      int(e.FHRSID), txt(e.BusinessName), txt(e.BusinessType), txt(e.PostCode),
      rv, /^[0-5]$/.test(rv || '') ? parseInt(rv, 10) : null, date(e.RatingDate),
      txt(e.LocalAuthorityCode), txt(e.SchemeType),
      int(sc.Hygiene), int(sc.Structural), int(sc.ConfidenceInManagement),
      num(g.Longitude), num(g.Latitude),
    ];
  });

  const c = await mysql.createConnection({ socketPath: cfg.socketPath, user: cfg.admin.user, database: cfg.dbName });
  await c.query('TRUNCATE establishment');
  await c.query(`INSERT INTO establishment (fhrs_id, business_name, business_type, post_code,
    rating_value, rating_numeric, rating_date, la_code, scheme_type,
    hygiene_score, structural_score, confidence_score, longitude, latitude) VALUES ?`, [rows]);
  const [[n]] = await c.query('SELECT COUNT(*) AS n FROM establishment');
  console.log('Inserted', n.n, 'establishments');
  await c.end();
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
```

**4b. Run it (from the project root):**

```bash
node etl/load-one.js
```

**Checkpoint 4:**

```bash
mysql fhrs_tutorial -e "SELECT COUNT(*) AS premises, COUNT(rating_numeric) AS rated FROM establishment;"
```

You should see roughly 1,400 premises, most with a numeric rating.

---

## Step 5 — Ask your first questions

**Goal:** simple analysis on the single-authority data — no new code, just SQL.

**Try it first — which column do you average, and why a `HAVING` filter?**
- Average the *text* column and watch it mislead:
  ```bash
  mysql fhrs_tutorial -e "SELECT AVG(rating_value) AS text_lie, AVG(rating_numeric) AS honest FROM establishment;"
  ```
  `AVG(rating_value)` turns 'AwaitingInspection'/'Exempt' into 0 and drags the number
  down; `AVG(rating_numeric)` ignores them. Always average the column that is *only*
  numbers.
- In the by-type query below, try deleting the `HAVING rated >= 20` line. Business
  types with one or two premises shoot to the top and bottom on pure chance — the
  threshold is what keeps the ranking meaningful.

**5a. Create `sql/analysis-small.sql`:**

```sql
USE fhrs_tutorial;

-- Distribution of ratings
SELECT rating_value, COUNT(*) AS n
FROM establishment GROUP BY rating_value ORDER BY n DESC;

-- Average rating by business type (numeric ratings only)
SELECT business_type,
       COUNT(rating_numeric) AS rated,
       ROUND(AVG(rating_numeric), 2) AS avg_rating
FROM establishment
WHERE rating_numeric IS NOT NULL
GROUP BY business_type
HAVING rated >= 20
ORDER BY avg_rating DESC;

-- How many are still awaiting their first inspection?
SELECT SUM(rating_date IS NULL) AS awaiting_inspection,
       ROUND(100 * AVG(rating_date IS NULL), 1) AS pct_awaiting
FROM establishment;
```

**Checkpoint 5:**

```bash
mysql fhrs_tutorial -t < sql/analysis-small.sql
```

You should see three result tables (rating distribution, by-type averages, and the
awaiting-inspection count).

---

## Step 6 — Scale up and add relationships

**Goal:** turn the single table into a proper relational schema (regions, local
authorities, business types) and load **many** authorities across the UK.

**Try it first — why split out `region` and `business_type` tables at all?**
Leaving them as text columns on every row (like Step 3 did) looks simpler. Two
problems appear quickly:
```bash
# 1) free text + one typo = a phantom category that corrupts your GROUP BY:
mysql fhrs_tutorial -e "CREATE TEMPORARY TABLE bt(name VARCHAR(40),r INT);
  INSERT INTO bt VALUES('Restaurant',5),('Restaurant',4),('Resturant',1);
  SELECT name,COUNT(*) n,AVG(r) avg FROM bt GROUP BY name;"
#   -> 'Resturant' becomes its own group; your per-type averages are now wrong
```
2) If "London" sits as text on thousands of rows and the name changes, you must
update *every* row; stored once in a `region` table and referenced by id, it's a
one-row change. Putting each region/type in its own table (and joining by id) stops
typos and makes renames trivial — that is what normalisation buys you.

> **From Step 6 on you will NOT run `sql/01_schema_single.sql` or `etl/load-one.js`
> again.** You don't need to delete anything by hand: the new
> `sql/02_schema_relational.sql` below `DROP`s and recreates every table, and a new
> loader replaces the old one. Those two old files just sit unused (keep or delete
> them, your choice). This kind of "replace earlier work as the design grows" is
> normal — we'll always tell you when it happens.

**6a. Create `sql/02_schema_relational.sql`:**

```sql
CREATE DATABASE IF NOT EXISTS fhrs_tutorial
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fhrs_tutorial;

DROP TABLE IF EXISTS establishment;
DROP TABLE IF EXISTS local_authority;
DROP TABLE IF EXISTS business_type;
DROP TABLE IF EXISTS region;

CREATE TABLE region (
  region_id   INT AUTO_INCREMENT PRIMARY KEY,
  region_name VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE business_type (
  business_type_id   INT PRIMARY KEY,
  business_type_name VARCHAR(120) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE local_authority (
  la_code     VARCHAR(10) PRIMARY KEY,
  name        VARCHAR(120) NOT NULL,
  region_id   INT NOT NULL,
  CONSTRAINT fk_la_region FOREIGN KEY (region_id) REFERENCES region(region_id)
) ENGINE=InnoDB;

CREATE TABLE establishment (
  fhrs_id          BIGINT PRIMARY KEY,
  business_name    VARCHAR(255),
  business_type_id INT,
  post_code        VARCHAR(20),
  rating_value     VARCHAR(30),
  rating_numeric   TINYINT NULL,
  rating_date      DATE NULL,
  la_code          VARCHAR(10) NOT NULL,
  scheme_type      VARCHAR(10),
  hygiene_score    SMALLINT NULL,
  structural_score SMALLINT NULL,
  confidence_score SMALLINT NULL,
  longitude        DECIMAL(9,6) NULL,
  latitude         DECIMAL(8,6) NULL,
  CONSTRAINT fk_est_la   FOREIGN KEY (la_code)          REFERENCES local_authority(la_code),
  CONSTRAINT fk_est_type FOREIGN KEY (business_type_id) REFERENCES business_type(business_type_id),
  KEY idx_est_la (la_code), KEY idx_est_type (business_type_id), KEY idx_est_rating (rating_numeric)
) ENGINE=InnoDB;
```

Run it:

```bash
mysql < sql/02_schema_relational.sql
```

**6b. Create `etl/download-many.js`** — fetches the FSA authority list and downloads
**2 authorities per region** (about 24 files: enough for real regional analysis,
small enough to be quick):

```js
const fs = require('fs');
const { execFileSync } = require('child_process');

(async () => {
  fs.mkdirSync('data/fhrs', { recursive: true });
  // 1. the master list of authorities (includes region + file URL for each)
  execFileSync('curl', ['-fsSL', '-H', 'x-api-version: 2', '-o', 'data/authorities.json',
    'https://api.ratings.food.gov.uk/authorities']);
  const all = JSON.parse(fs.readFileSync('data/authorities.json', 'utf8')).authorities;

  // 2. pick 2 authorities from each region
  const perRegion = {};
  const selected = [];
  for (const a of all) {
    perRegion[a.RegionName] = (perRegion[a.RegionName] || 0);
    if (perRegion[a.RegionName] < 2) { selected.push(a); perRegion[a.RegionName]++; }
  }
  fs.writeFileSync('data/selected.json', JSON.stringify(selected, null, 2));
  console.log('Selected', selected.length, 'authorities across', Object.keys(perRegion).length, 'regions');

  // 3. download each one's open-data file
  for (const a of selected) {
    const dest = `data/fhrs/FHRS${a.LocalAuthorityIdCode}.xml`;
    try {
      execFileSync('curl', ['-fsSL', '--retry', '3', '-o', dest, a.FileName]);
      process.stdout.write('.');
    } catch { process.stdout.write('x'); }
  }
  console.log('\nDownloaded files into data/fhrs/');
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
```

**6c. Create `etl/load-many.js`** — loads regions, business types, authorities and
establishments in foreign-key order. *(It reads `data/selected.json`, which 6b
creates, so always run 6b before 6c — the `Run both` block below does this for
you.)*

```js
const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');
const { XMLParser } = require('fast-xml-parser');
const cfg = require('../config');  // '../' because this file lives in etl/

const txt = v => (v == null || typeof v === 'object') ? null : String(v).trim() || null;
const int = v => { const n = parseInt(txt(v), 10); return Number.isFinite(n) ? n : null; };
const num = v => { const n = parseFloat(txt(v)); return Number.isFinite(n) ? n : null; };
const date = v => { const s = txt(v); return s && /^\d{4}-\d{2}-\d{2}/.test(s) ? s.slice(0, 10) : null; };

(async () => {
  const selected = JSON.parse(fs.readFileSync('data/selected.json', 'utf8'));
  const c = await mysql.createConnection({ socketPath: cfg.socketPath, user: cfg.admin.user, database: cfg.dbName });

  // regions
  const regions = [...new Set(selected.map(a => a.RegionName))];
  await c.query('INSERT IGNORE INTO region (region_name) VALUES ?', [regions.map(r => [r])]);
  const [regRows] = await c.query('SELECT region_id, region_name FROM region');
  const regionId = Object.fromEntries(regRows.map(r => [r.region_name, r.region_id]));

  // authorities
  await c.query('INSERT IGNORE INTO local_authority (la_code, name, region_id) VALUES ?',
    [selected.map(a => [a.LocalAuthorityIdCode, a.Name, regionId[a.RegionName]])]);

  // parse every downloaded file: collect business types + establishment rows
  const parser = new XMLParser({ ignoreAttributes: false, parseTagValue: false });
  const types = new Map();
  const rows = [];
  const laCodes = new Set(selected.map(a => a.LocalAuthorityIdCode));
  for (const f of fs.readdirSync('data/fhrs').filter(f => f.endsWith('.xml'))) {
    const doc = parser.parse(fs.readFileSync(path.join('data/fhrs', f), 'utf8'));
    let ests = doc?.FHRSEstablishment?.EstablishmentCollection?.EstablishmentDetail;
    if (!ests) continue;
    if (!Array.isArray(ests)) ests = [ests];
    for (const e of ests) {
      const laCode = txt(e.LocalAuthorityCode);
      if (!laCodes.has(laCode)) continue;                  // keep referential integrity
      const btId = int(e.BusinessTypeID);
      if (btId != null && !types.has(btId)) types.set(btId, txt(e.BusinessType) || `Type ${btId}`);
      const rv = txt(e.RatingValue);
      const sc = (e.Scores && typeof e.Scores === 'object') ? e.Scores : {};
      const g = e.Geocode || {};
      rows.push([
        int(e.FHRSID), txt(e.BusinessName), btId, txt(e.PostCode), rv,
        /^[0-5]$/.test(rv || '') ? parseInt(rv, 10) : null, date(e.RatingDate),
        laCode, txt(e.SchemeType), int(sc.Hygiene), int(sc.Structural),
        int(sc.ConfidenceInManagement), num(g.Longitude), num(g.Latitude),
      ]);
    }
  }

  // business types must exist before establishments (FK)
  await c.query('INSERT IGNORE INTO business_type (business_type_id, business_type_name) VALUES ?',
    [[...types.entries()]]);

  // establishments, in batches, de-duplicated on fhrs_id
  const seen = new Set();
  const unique = rows.filter(r => r[0] != null && !seen.has(r[0]) && seen.add(r[0]));
  for (let i = 0; i < unique.length; i += 2000) {
    await c.query(`INSERT INTO establishment (fhrs_id, business_name, business_type_id, post_code,
      rating_value, rating_numeric, rating_date, la_code, scheme_type,
      hygiene_score, structural_score, confidence_score, longitude, latitude) VALUES ?`,
      [unique.slice(i, i + 2000)]);
  }
  const [[n]] = await c.query('SELECT COUNT(*) AS n FROM establishment');
  console.log('Loaded', n.n, 'establishments,', types.size, 'business types,', regions.length, 'regions');
  await c.end();
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
```

**6d. Run both:**

```bash
node etl/download-many.js
node etl/load-many.js
```

**Checkpoint 6:**

```bash
mysql fhrs_tutorial -t -e "
SELECT r.region_name, COUNT(e.rating_numeric) AS rated, ROUND(AVG(e.rating_numeric),2) AS avg_rating
FROM establishment e
JOIN local_authority la ON e.la_code = la.la_code
JOIN region r ON la.region_id = r.region_id
WHERE e.rating_numeric IS NOT NULL
GROUP BY r.region_name ORDER BY avg_rating DESC;"
```

You should see one row per region with an average rating — a three-table join
working across the data you loaded.

---

## Step 7 — Add deprivation and join it in

**Goal:** bring in the English Indices of Deprivation 2019 (per local-authority
district) and join it to your authorities to ask *"do poorer areas score lower?"*

**Try it first — why not just join on the authority name?**
The obvious join is `... ON la.name = imd.lad_name`. Here's why it falls apart:
```bash
mysql -e "SELECT 'Bristol' = 'Bristol, City of' AS exact_match;"   # -> 0
```
Real names differ by case, punctuation, "City of", `&` vs "and", and post-2019
boundary changes, so an exact join would silently drop most authorities. That's why
`load-imd.js` *normalises* both names before matching, and why the link is left as
NULL for authorities that don't match (visible) instead of using an INNER join that
hides them. Reconciling two datasets with no shared key is the normal cost of
combining real-world data.

> *Apply the Step 2 method to this new source first.* Found it: gov.uk's "English
> indices of deprivation 2019" (official, documented, machine-readable). One row =
> one local-authority district; the key is the **ONS district code**. The hard part
> is the **join**: this data has no FSA code, only a district *name*, so we'll match
> it to our authorities by name (and accept that a few won't match). Spotting "how
> will this join to what I already have?" is the main new question when you add a
> second dataset.

**7a. Add the deprivation table, and the link column.** Now — not back in Step 6 —
is when we need a `lad_code` on `local_authority` to point each authority at its
deprivation district, so we add it here with `ALTER TABLE`. Create `sql/03_imd.sql`:

```sql
USE fhrs_tutorial;
DROP TABLE IF EXISTS imd_lad;
CREATE TABLE imd_lad (
  lad_code      VARCHAR(10) PRIMARY KEY,    -- ONS district code, e.g. E09000002
  lad_name      VARCHAR(120),
  imd_avg_score DECIMAL(8,3),               -- higher = more deprived
  imd_rank      INT                         -- 1 = most deprived district
) ENGINE=InnoDB;

-- Add the deprivation link to local_authority now that we have somewhere to point.
-- (Run this step once; Step 6 recreates local_authority without this column.)
ALTER TABLE local_authority ADD COLUMN lad_code VARCHAR(10) NULL;
```

```bash
mysql < sql/03_imd.sql
```

**7b. Create `etl/load-imd.js`** — downloads the Indices of Deprivation 2019
local-authority-district summary spreadsheet (the official release calls it
"File 10"), loads it, and matches each local authority to its district by name:

```js
const fs = require('fs');
const { execFileSync } = require('child_process');
const mysql = require('mysql2/promise');
const XLSX = require('xlsx');
const cfg = require('../config');  // '../' because this file lives in etl/

const URL = 'https://assets.publishing.service.gov.uk/media/5d8b3cfbe5274a08be69aa91/' +
            'File_10_-_IoD2019_Local_Authority_District_Summaries__lower-tier__.xlsx';

// Normalise a name so FHRS authority names line up with ONS district names.
const norm = s => String(s).toLowerCase().replace(/&/g, 'and').replace(/[.,'`]/g, '')
  .replace(/-/g, ' ').replace(/\b(london borough of|royal borough of|borough of|city of|county of|the)\b/g, '')
  .replace(/\b(council|corporation|district|county|city)\b/g, '').replace(/\s+/g, ' ').trim();

(async () => {
  fs.mkdirSync('data', { recursive: true });
  execFileSync('curl', ['-fsSL', '--retry', '3', '-o', 'data/imd_file10.xlsx', URL]);
  const wb = XLSX.readFile('data/imd_file10.xlsx');
  const rows = XLSX.utils.sheet_to_json(wb.Sheets['IMD'], { header: 1 }).slice(1)
    .filter(r => r[0]);
  // columns: 0 = LAD code, 1 = LAD name, 4 = IMD average score, 5 = rank of avg score
  const imd = rows.map(r => [r[0], r[1], r[4], r[5]]);

  const c = await mysql.createConnection({ socketPath: cfg.socketPath, user: cfg.admin.user, database: cfg.dbName });
  await c.query('INSERT IGNORE INTO imd_lad (lad_code, lad_name, imd_avg_score, imd_rank) VALUES ?', [imd]);

  // map normalised district name -> code, then update each local authority
  const byName = new Map(imd.map(r => [norm(r[1]), r[0]]));
  const [las] = await c.query('SELECT la_code, name FROM local_authority');
  let matched = 0;
  for (const la of las) {
    const lad = byName.get(norm(la.name));
    if (lad) { await c.query('UPDATE local_authority SET lad_code=? WHERE la_code=?', [lad, la.la_code]); matched++; }
  }
  console.log(`Loaded ${imd.length} districts; matched ${matched}/${las.length} authorities to deprivation`);
  await c.end();
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
```

```bash
node etl/load-imd.js
```

**7c. Create `sql/analysis-deprivation.sql`:**

```sql
USE fhrs_tutorial;

-- Average hygiene rating vs district deprivation, per matched authority
SELECT la.name, r.region_name,
       imd.imd_avg_score AS deprivation,
       ROUND(AVG(e.rating_numeric), 2) AS avg_rating
FROM establishment e
JOIN local_authority la ON e.la_code = la.la_code
JOIN region r           ON la.region_id = r.region_id
JOIN imd_lad imd        ON la.lad_code = imd.lad_code
WHERE e.rating_numeric IS NOT NULL
GROUP BY la.la_code
ORDER BY deprivation DESC;

-- One-number summary: Pearson correlation between deprivation and average rating
WITH s AS (
  SELECT imd.imd_avg_score AS x, AVG(e.rating_numeric) AS y
  FROM establishment e
  JOIN local_authority la ON e.la_code = la.la_code
  JOIN imd_lad imd        ON la.lad_code = imd.lad_code
  WHERE e.rating_numeric IS NOT NULL
  GROUP BY la.la_code
)
SELECT COUNT(*) AS authorities,
       ROUND((COUNT(*)*SUM(x*y) - SUM(x)*SUM(y)) /
         (SQRT(COUNT(*)*SUM(x*x) - POW(SUM(x),2)) *
          SQRT(COUNT(*)*SUM(y*y) - POW(SUM(y),2))), 3) AS pearson_r
FROM s;
```

**Checkpoint 7:**

```bash
mysql fhrs_tutorial -t < sql/analysis-deprivation.sql
```

You should see a per-authority table and a `pearson_r` value (negative means more
deprived areas tend to score lower). *With this small sample the correlation is
only indicative; the full 363-authority dataset gives a clearer figure.*

> **Note — only matched authorities appear.** The deprivation data is England-only,
> and a few authorities' names don't line up with an ONS district, so they get no
> `lad_code` and the `JOIN imd_lad` quietly leaves them out (that's why the count is
> ~17, not 24). This is expected, not a bug. To see how many of your authorities
> matched, run:
> ```bash
> mysql fhrs_tutorial -e "SELECT COUNT(*) AS matched FROM local_authority WHERE lad_code IS NOT NULL;"
> ```

---

## Step 8 — A read-only web app

**Goal:** serve the results over HTTP, using a database user that can only read.

**Try it first — why not let the web app connect as root?**
Anything the connection is allowed to do, a bug or an injected query can do too. See
what root could do to your data — the transaction is rolled back, so nothing
actually changes:
```bash
mysql fhrs_tutorial -e "START TRANSACTION; DELETE FROM establishment LIMIT 1; SELECT ROW_COUNT() AS root_could_delete; ROLLBACK;"
#   -> root_could_delete = 1   (a query-only web app should never be able to do that)
```
After you create the read-only `fhrs_read` user below, that same `DELETE` is refused.
Giving the web tier only `SELECT` means a compromised query can read data but never
change or drop it.

**8a. Create the read-only user.** The username `fhrs_read` and password `readonly`
are arbitrary — pick your own if you like, but then set the same values in
`config.js` under `app`. We'll assume `fhrs_read` / `readonly`.

Create `sql/04_users.sql`:

```sql
CREATE USER IF NOT EXISTS 'fhrs_read'@'localhost' IDENTIFIED BY 'readonly';
GRANT SELECT ON fhrs_tutorial.* TO 'fhrs_read'@'localhost';
FLUSH PRIVILEGES;
```

```bash
mysql < sql/04_users.sql
```

Confirm the limit is real — this `DELETE` as `fhrs_read` should be **refused**:
```bash
mysql -u fhrs_read -preadonly fhrs_tutorial -e "DELETE FROM establishment LIMIT 1;"
#   -> ERROR 1142: DELETE command denied to user 'fhrs_read'@'localhost'
```

This step introduces the `webapp/` and `webapp/public/` folders — from a terminal,
`mkdir -p webapp/public` first (an editor will make them for you on save).

**8b. Create `webapp/server.js`:**

```js
const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path');
const cfg = require('../config');

const app = express();
const pool = mysql.createPool({
  socketPath: cfg.socketPath, database: cfg.dbName,
  user: cfg.app.user, password: cfg.app.password, connectionLimit: 4,
});
const q = async (sql) => (await pool.query(sql))[0];

app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/regions', async (_req, res) => {
  try {
    res.json(await q(`
      SELECT r.region_name,
             COUNT(e.rating_numeric) AS rated,
             ROUND(AVG(e.rating_numeric),2) AS avg_rating
      FROM establishment e
      JOIN local_authority la ON e.la_code=la.la_code
      JOIN region r ON la.region_id=r.region_id
      WHERE e.rating_numeric IS NOT NULL
      GROUP BY r.region_name ORDER BY avg_rating DESC`));
  } catch (e) { res.status(500).json({ error: e.message }); }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Web app on http://localhost:${PORT}`));
```

**8c. Create `webapp/public/index.html`:**

```html
<!DOCTYPE html><html><head><meta charset="utf-8"><title>Food hygiene by region</title>
<style>body{font-family:system-ui;margin:2rem}table{border-collapse:collapse}
td,th{border:1px solid #ccc;padding:4px 10px;text-align:left}</style></head>
<body><h1>Average food-hygiene rating by region</h1><table id="t">
<thead><tr><th>Region</th><th>Rated premises</th><th>Avg rating</th></tr></thead>
<tbody></tbody></table>
<script>
fetch('/api/regions').then(r=>r.json()).then(rows=>{
  document.querySelector('#t tbody').innerHTML = rows.map(r=>
    `<tr><td>${r.region_name}</td><td>${r.rated}</td><td>${r.avg_rating}</td></tr>`).join('');
});
</script></body></html>
```

**8d. Start it.** On Linux/macOS you can background it in the same terminal with `&`
(below). On Windows, or if you prefer, open a **second terminal** in the same
project folder and run `node webapp/server.js` there without the `&`.

```bash
node webapp/server.js &
sleep 1
```

If you see `EADDRINUSE` (port 3000 already taken), start it on another port and use
that port in the checkpoint, e.g. `PORT=8000 node webapp/server.js &`.

**Checkpoint 8:**

```bash
curl -s http://localhost:3000/api/regions
```

You should get a JSON array of regions with average ratings. Opening
`http://localhost:3000/` in a browser shows the same as a table. (Stop the server
later with `kill %1` or by closing the terminal.)

---

## Step 9 — Clean the data, with an audit trail

**Goal:** remove *impossible* records, but record exactly what was removed so the
cleaning is transparent and reversible.

**Try it first — why quarantine rows, and why keep ones with no postcode?**
- The blunt fix is `DELETE FROM establishment WHERE rating_date < '2006-01-01';` —
  it works, and those rows are gone forever with no record of what left or why. Our
  cleaner first copies them into an `establishment_rejects` table *with a reason*,
  so every removal is auditable and reversible.
- "Missing" is not the same as "wrong". Before you'd delete rows with no postcode,
  count them:
  ```bash
  mysql fhrs_tutorial -e "SELECT COUNT(*) AS no_postcode FROM establishment WHERE post_code IS NULL OR post_code='';"
  ```
  Most are legitimate premises (e.g. mobile caterers). Deleting them would throw away
  real data — so the cleaner *flags and keeps* them, and removes only what is
  genuinely impossible.

**9a. Create `etl/clean.js`:**

```js
// Quarantine impossible rows into establishment_rejects (with a reason), then
// delete them from establishment. Nothing is silently lost.
const fs = require('fs');
const mysql = require('mysql2/promise');
const cfg = require('../config');  // '../' because this file lives in etl/

// Rows whose inspection date predates any scheme existing (FHIS 2006, FHRS 2010)
// are impossible -> remove. Add more rules here as you find more problems.
const RULES = [
  ['pre_scheme_date', "rating_date < '2006-01-01'"],
  ['future_date',     'rating_date > CURDATE()'],
];

(async () => {
  const c = await mysql.createConnection({ socketPath: cfg.socketPath, user: cfg.admin.user, database: cfg.dbName });
  await c.query(`CREATE TABLE IF NOT EXISTS establishment_rejects (
    fhrs_id BIGINT PRIMARY KEY, business_name VARCHAR(255), rating_value VARCHAR(30),
    rating_date DATE, la_code VARCHAR(10), reject_reason VARCHAR(60), rejected_at DATETIME)`);

  const before = (await c.query('SELECT COUNT(*) n FROM establishment'))[0][0].n;
  const summary = [];
  for (const [name, pred] of RULES) {
    await c.query(`INSERT IGNORE INTO establishment_rejects
      SELECT fhrs_id, business_name, rating_value, rating_date, la_code, ?, NOW()
      FROM establishment WHERE ${pred}`, [name]);
    const [del] = await c.query(`DELETE FROM establishment WHERE ${pred}`);
    summary.push([name, del.affectedRows]);
    console.log(`removed ${del.affectedRows} rows for rule ${name}`);
  }
  const after = (await c.query('SELECT COUNT(*) n FROM establishment'))[0][0].n;

  let md = `# Cleaning report\n\nBefore: ${before}  After: ${after}  Removed: ${before - after}\n\n`;
  md += `| rule | removed |\n|---|--:|\n` + summary.map(([n, c]) => `| ${n} | ${c} |`).join('\n') + '\n';
  fs.writeFileSync('report-cleaning.md', md);
  console.log(`Before ${before} -> After ${after}. Wrote report-cleaning.md`);
  await c.end();
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
```

**9b. Run it:**

```bash
node etl/clean.js
```

**Checkpoint 9:** (Counts depend on which authorities you sampled — a removal count
of **0 is also a pass**: it just means your sample had no impossible dates, and the
empty `establishment_rejects` table proves the check ran.)

```bash
cat report-cleaning.md
mysql fhrs_tutorial -e "SELECT reject_reason, COUNT(*) FROM establishment_rejects GROUP BY reject_reason;"
```

You should see the cleaning report and the quarantined rows grouped by reason.

---

## You're done

You built a relational database from open data, scaled it from one authority to
many, joined in a second dataset (deprivation), served it over HTTP with a
least-privilege user, and cleaned it with an audit trail. To go further: load **all
363** authorities (remove the "2 per region" cap in `etl/download-many.js`), add the
remaining deprivation domains, or push the deprivation join down to neighbourhood
(LSOA) level using an ONS postcode→LSOA lookup.
