// Data-cleaning pass over the `establishment` table.
//
// Philosophy: never silently drop data.
//   * "REMOVE" rules target rows that are *impossible* / corrupt. Matching rows
//     are copied into establishment_rejects (a full audit copy + reason) BEFORE
//     being deleted, so every removal is recorded and reversible.
//   * "FLAG" rules target rows that are *incomplete but legitimate* (e.g. a
//     mobile caterer with no postcode, a premise awaiting its first inspection).
//     These are counted and reported but KEPT — deleting them would lose real data.
//
// Every rule, its SQL predicate and its row count are written to:
//   * cleaning_log         (table, machine-readable audit)
//   * establishment_rejects(table, the actual removed rows + reason)
//   * report/CLEANING_REPORT.md (human-readable summary + samples)
//
// Idempotent: re-running finds nothing new (removed rows are already gone; the
// rejects table is keyed on fhrs_id so it never double-records).
const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');
const cfg = require('../config');

// Real (non-generated) establishment columns, in order.
const COLS = ['fhrs_id', 'la_business_id', 'business_name', 'business_type_id',
  'address_line1', 'address_line2', 'address_line3', 'address_line4', 'post_code',
  'rating_value', 'rating_numeric', 'rating_date', 'la_code', 'scheme_type',
  'new_rating_pending', 'longitude', 'latitude', 'hygiene_score',
  'structural_score', 'confidence_score'];

// Valid FHRS component-score values (anything else is a data error).
const HYG = '(0,5,10,15,20,25)';      // hygiene & structural
const CONF = '(0,5,10,20,30)';        // confidence in management

// ---- the rules -------------------------------------------------------------
const REMOVE_RULES = [
  ['empty_business_name', 'Business name is null or blank (no identity)',
    "business_name IS NULL OR TRIM(business_name) = ''"],
  ['empty_rating_value', 'Rating value is null or blank',
    "rating_value IS NULL OR TRIM(rating_value) = ''"],
  ['impossible_future_date', 'Rating date is in the future (after today)',
    'rating_date > CURDATE()'],
  ['pre_scheme_date', 'Rating date predates any scheme existing (< 2006; FHIS began 2006, FHRS 2010)',
    "rating_date < '2006-01-01'"],
  ['coords_outside_uk', 'Geocode falls outside the UK bounding box (lat 49.8-60.9, long -8.65-1.77)',
    'longitude IS NOT NULL AND (latitude NOT BETWEEN 49.8 AND 60.9 OR longitude NOT BETWEEN -8.65 AND 1.77)'],
  ['invalid_component_score', `Component score outside the permitted FHRS values (hygiene/structural ${HYG}, confidence ${CONF})`,
    `(hygiene_score    IS NOT NULL AND hygiene_score    NOT IN ${HYG})
     OR (structural_score IS NOT NULL AND structural_score NOT IN ${HYG})
     OR (confidence_score IS NOT NULL AND confidence_score NOT IN ${CONF})`],
];

// Reported but NOT deleted (incomplete but valid).
const FLAG_RULES = [
  ['missing_postcode', 'No postcode — valid for some premises (e.g. mobile caterers) but cannot be geo-joined',
    "post_code IS NULL OR TRIM(post_code) = ''"],
  ['awaiting_first_inspection', 'No rating date because the premise is awaiting its first inspection (legitimate)',
    'rating_date IS NULL'],
  ['numeric_rating_without_scores', 'FHRS premise has a 0-5 rating but no component scores recorded',
    "scheme_type = 'FHRS' AND rating_numeric IS NOT NULL AND hygiene_score IS NULL"],
  ['fhrs_date_pre_rollout', 'FHRS rating date between 2006 and the 2010 national rollout (suspect, retained)',
    "scheme_type = 'FHRS' AND rating_date >= '2006-01-01' AND rating_date < '2010-01-01'"],
];

async function scalar(conn, sql) { const [r] = await conn.query(sql); return Object.values(r[0])[0]; }

async function main() {
  const conn = await mysql.createConnection({
    host: cfg.db.host, port: cfg.db.port, database: cfg.db.database,
    user: cfg.admin.user, password: cfg.admin.password, multipleStatements: true,
  });
  console.log('Connected as', cfg.admin.user);

  // ---- audit tables ----------------------------------------------------
  await conn.query(`CREATE TABLE IF NOT EXISTS establishment_rejects (
      ${COLS.map(c => `${c} ${columnType(c)}`).join(',\n      ')},
      reject_reason VARCHAR(80) NOT NULL,
      rejected_at   DATETIME NOT NULL,
      PRIMARY KEY (fhrs_id)
    ) ENGINE=InnoDB`);
  await conn.query(`CREATE TABLE IF NOT EXISTS cleaning_log (
      log_id     INT AUTO_INCREMENT PRIMARY KEY,
      run_at     DATETIME NOT NULL,
      rule_name  VARCHAR(60) NOT NULL,
      action     ENUM('removed','flagged') NOT NULL,
      description VARCHAR(255) NOT NULL,
      predicate  TEXT NOT NULL,
      rows_affected INT NOT NULL
    ) ENGINE=InnoDB`);

  const runAt = await scalar(conn, 'SELECT NOW()');   // single server-side timestamp for this run
  const before = await scalar(conn, 'SELECT COUNT(*) FROM establishment');
  const colList = COLS.join(', ');
  const results = { removed: [], flagged: [], samples: {} };

  // ---- REMOVE rules (quarantine then delete) ---------------------------
  for (const [name, desc, pred] of REMOVE_RULES) {
    await conn.beginTransaction();
    // capture sample rows for the report before deleting
    const [sample] = await conn.query(
      `SELECT fhrs_id, business_name, post_code, rating_value, rating_date, scheme_type, latitude, longitude
       FROM establishment WHERE ${pred} LIMIT 5`);
    const [ins] = await conn.query(
      `INSERT IGNORE INTO establishment_rejects (${colList}, reject_reason, rejected_at)
       SELECT ${colList}, ? , ? FROM establishment WHERE ${pred}`, [name, runAt]);
    const [del] = await conn.query(`DELETE FROM establishment WHERE ${pred}`);
    await conn.query(
      `INSERT INTO cleaning_log (run_at, rule_name, action, description, predicate, rows_affected)
       VALUES (?,?,?,?,?,?)`, [runAt, name, 'removed', desc, pred.replace(/\s+/g, ' ').trim(), del.affectedRows]);
    await conn.commit();
    results.removed.push([name, desc, del.affectedRows]);
    if (del.affectedRows > 0) results.samples[name] = sample;
    console.log(`REMOVE ${name}: ${del.affectedRows} rows`);
  }

  // ---- FLAG rules (report only) ----------------------------------------
  for (const [name, desc, pred] of FLAG_RULES) {
    const n = await scalar(conn, `SELECT COUNT(*) FROM establishment WHERE ${pred}`);
    await conn.query(
      `INSERT INTO cleaning_log (run_at, rule_name, action, description, predicate, rows_affected)
       VALUES (?,?,?,?,?,?)`, [runAt, name, 'flagged', desc, pred.replace(/\s+/g, ' ').trim(), n]);
    results.flagged.push([name, desc, n]);
    console.log(`FLAG   ${name}: ${n} rows (kept)`);
  }

  const after = await scalar(conn, 'SELECT COUNT(*) FROM establishment');
  const totalRejects = await scalar(conn, 'SELECT COUNT(*) FROM establishment_rejects');
  writeReport({ runAt, before, after, totalRejects, results });
  console.log(`\nBefore: ${before}  After: ${after}  Removed: ${before - after}  (quarantined total: ${totalRejects})`);
  console.log('Report written to report/CLEANING_REPORT.md');
  await conn.end();
}

function columnType(c) {
  const t = {
    fhrs_id: 'BIGINT', business_type_id: 'INT', rating_numeric: 'TINYINT', rating_date: 'DATE',
    new_rating_pending: 'BOOLEAN', longitude: 'DECIMAL(9,6)', latitude: 'DECIMAL(8,6)',
    hygiene_score: 'SMALLINT', structural_score: 'SMALLINT', confidence_score: 'SMALLINT',
    la_business_id: 'VARCHAR(100)', business_name: 'VARCHAR(255)', post_code: 'VARCHAR(20)',
    rating_value: 'VARCHAR(30)', la_code: 'VARCHAR(10)', scheme_type: 'VARCHAR(10)',
  };
  return t[c] || 'VARCHAR(255)';
}

function fmtDate(d) {
  if (!d) return '';
  if (d instanceof Date) return d.toISOString().slice(0, 10);
  return String(d).slice(0, 10);
}
function fmtTs(d) {
  if (d instanceof Date) return d.toISOString().slice(0, 19).replace('T', ' ') + ' UTC';
  return String(d);
}
function writeReport({ runAt, before, after, totalRejects, results }) {
  let md = `# Data-cleaning report\n\n`;
  md += `Run at: ${fmtTs(runAt)}\n\n`;
  md += `| | rows |\n|---|--:|\n`;
  md += `| establishments before | ${before} |\n`;
  md += `| **removed (quarantined)** | **${before - after}** |\n`;
  md += `| establishments after | ${after} |\n`;
  md += `| total rows in establishment_rejects | ${totalRejects} |\n\n`;

  md += `## Rules that REMOVE rows (impossible / corrupt data)\n\n`;
  md += `Matching rows are copied to \`establishment_rejects\` with the reason, then deleted.\n\n`;
  md += `| rule | what it catches | removed |\n|---|---|--:|\n`;
  for (const [n, d, c] of results.removed) md += `| \`${n}\` | ${d} | ${c} |\n`;

  md += `\n## Rules that FLAG rows (incomplete but legitimate — KEPT)\n\n`;
  md += `| rule | why it is kept | count |\n|---|---|--:|\n`;
  for (const [n, d, c] of results.flagged) md += `| \`${n}\` | ${d} | ${c} |\n`;

  const sampleNames = Object.keys(results.samples);
  if (sampleNames.length) {
    md += `\n## Examples of removed rows\n`;
    for (const name of sampleNames) {
      md += `\n**\`${name}\`**\n\n| fhrs_id | business_name | post_code | rating_value | rating_date | scheme | lat | long |\n|---|---|---|---|---|---|---|---|\n`;
      for (const r of results.samples[name]) {
        md += `| ${r.fhrs_id} | ${trunc(r.business_name)} | ${r.post_code || ''} | ${r.rating_value} | ${fmtDate(r.rating_date)} | ${r.scheme_type} | ${r.latitude ?? ''} | ${r.longitude ?? ''} |\n`;
      }
    }
  }
  md += `\n## How to inspect or reverse\n\n`;
  md += '```sql\n';
  md += `-- everything that was removed, with reasons\nSELECT reject_reason, COUNT(*) FROM establishment_rejects GROUP BY reject_reason;\n\n`;
  md += `-- the per-run rule log\nSELECT * FROM cleaning_log ORDER BY log_id;\n\n`;
  md += `-- restore one row if a removal was wrong\n-- INSERT INTO establishment (<cols>) SELECT <cols> FROM establishment_rejects WHERE fhrs_id = ?;\n`;
  md += '```\n';
  fs.writeFileSync(path.join(__dirname, '..', 'report', 'CLEANING_REPORT.md'), md);
}
const trunc = (s) => (s && s.length > 40 ? s.slice(0, 38) + '…' : (s || ''));

main().catch(e => { console.error(e); process.exit(1); });
