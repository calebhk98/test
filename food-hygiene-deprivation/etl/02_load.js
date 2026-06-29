// Parse the downloaded sources and load them into MySQL.
// Order: region -> business_type -> imd_lad -> local_authority -> establishment.
const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');
const XLSX = require('xlsx');
const { XMLParser } = require('fast-xml-parser');
const cfg = require('../config');

const RAW = cfg.paths.raw;
const parser = new XMLParser({ ignoreAttributes: false, parseTagValue: false });

// ---- helpers ---------------------------------------------------------------
const asArray = (x) => (x == null ? [] : Array.isArray(x) ? x : [x]);
const txt = (v) => {
  if (v == null) return null;
  if (typeof v === 'object') return null;   // e.g. xsi:nil dates -> {"@_xsi:nil":"true"}
  const s = String(v).trim();
  return s === '' ? null : s;
};
const intOrNull = (v) => { const n = parseInt(txt(v), 10); return Number.isFinite(n) ? n : null; };
const numOrNull = (v) => { const n = parseFloat(txt(v)); return Number.isFinite(n) ? n : null; };
const dateOrNull = (v) => { const s = txt(v); return s && /^\d{4}-\d{2}-\d{2}/.test(s) ? s.slice(0, 10) : null; };

// Normalise a place name so FHRS authority names line up with ONS LAD names.
function norm(s) {
  return String(s).toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[.,'`]/g, '')
    .replace(/-/g, ' ')
    .replace(/\b(london borough of|royal borough of|borough of|city of|county of|the)\b/g, '')
    .replace(/\b(council|corporation|district|county|city|ua|unitary)\b/g, '')
    .replace(/\s+/g, ' ').trim();
}
// Manual aliases for the few FHRS names that don't normalise to their ONS LAD
// name. Keys and values are BOTH normalised forms (norm() applied).
// The remaining unmatched English authorities are post-2019 unitary
// re-organisations (no single IoD2019 district) or port health authorities
// (no resident population), which legitimately have no deprivation row.
const ALIAS = {
  'blackburn': 'blackburn with darwen',
  'hull': 'kingston upon hull',     // FHRS "Hull City" -> norm "hull"
};

async function batchInsert(conn, sql, rows, perBatch = 1000) {
  for (let i = 0; i < rows.length; i += perBatch) {
    await conn.query(sql, [rows.slice(i, i + perBatch)]);
  }
}

async function main() {
  const conn = await mysql.createConnection({
    host: cfg.db.host, port: cfg.db.port, database: cfg.db.database,
    user: cfg.admin.user, password: cfg.admin.password, multipleStatements: false,
  });
  console.log('Connected as', cfg.admin.user);

  const authorities = require(path.join(RAW, 'authorities_full.json')).authorities;

  // ---- 1. regions --------------------------------------------------------
  const regions = [...new Set(authorities.map(a => a.RegionName).filter(Boolean))];
  await batchInsert(conn, 'INSERT INTO region (region_name) VALUES ?', regions.map(r => [r]));
  const [regRows] = await conn.query('SELECT region_id, region_name FROM region');
  const regionId = Object.fromEntries(regRows.map(r => [r.region_name, r.region_id]));
  console.log('regions:', regions.length);

  // ---- 2. business types (API + any seen later get added on the fly) ------
  const bt = parser.parse(fs.readFileSync(path.join(RAW, 'business_types.xml'), 'utf8'));
  const btList = asArray(bt.ArrayOfWebBusinessTypeAPI.WebBusinessTypeAPI);
  const btSeen = new Map();
  for (const b of btList) {
    const id = intOrNull(b.BusinessTypeId);
    if (id != null && !btSeen.has(id)) btSeen.set(id, txt(b.BusinessTypeName) || `Type ${id}`);
  }
  await batchInsert(conn, 'INSERT INTO business_type (business_type_id, business_type_name) VALUES ?',
    [...btSeen.entries()].map(([id, name]) => [id, name]));
  console.log('business types (from API):', btSeen.size);

  // ---- 3. IMD LAD summary (File 10, sheet "IMD") --------------------------
  const wb = XLSX.readFile(path.join(RAW, 'imd2019_lad_summary.xlsx'));
  const rows = XLSX.utils.sheet_to_json(wb.Sheets['IMD'], { header: 1 });
  const imdRows = rows.slice(1).filter(r => r[0]).map(r => [
    r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11],
  ]);
  await batchInsert(conn,
    `INSERT INTO imd_lad (lad_code, lad_name, imd_avg_rank, imd_rank_of_avg_rank,
       imd_avg_score, imd_rank_of_avg_score, prop_lsoa_in_most_deprived_decile,
       rank_prop_most_deprived, imd_extent, rank_extent, imd_local_concentration,
       rank_local_concentration) VALUES ?`, imdRows);
  console.log('imd_lad districts:', imdRows.length);

  // Build normalised name -> lad_code map for matching
  const ladByNorm = new Map();
  for (const r of imdRows) ladByNorm.set(norm(r[1]), r[0]);
  function matchLad(name, regionName) {
    if (['Scotland', 'Wales', 'Northern Ireland'].includes(regionName)) return null;
    const n = norm(name);
    if (n in ALIAS) return ALIAS[n] == null ? null : (ladByNorm.get(ALIAS[n]) || null);
    return ladByNorm.get(n) || null;
  }

  // ---- 4. local authorities ----------------------------------------------
  const laRows = [];
  const unmatchedEnglish = [];
  for (const a of authorities) {
    const lad = matchLad(a.Name, a.RegionName);
    if (!lad && !['Scotland', 'Wales', 'Northern Ireland'].includes(a.RegionName)) {
      unmatchedEnglish.push(a.Name);
    }
    laRows.push([
      a.LocalAuthorityIdCode, a.LocalAuthorityId, a.Name, a.FriendlyName,
      regionId[a.RegionName], a.SchemeType, a.Url || null, a.Email || null,
      a.EstablishmentCount, dateTime(a.LastPublishedDate), lad,
    ]);
  }
  await batchInsert(conn,
    `INSERT INTO local_authority (la_code, la_id, name, friendly_name, region_id,
       scheme_type, url, email, establishment_count, last_published_date, lad_code) VALUES ?`, laRows);
  console.log('local authorities:', laRows.length,
    '| matched to IMD:', laRows.filter(r => r[10]).length,
    '| unmatched English:', unmatchedEnglish.length);
  if (unmatchedEnglish.length) console.log('  UNMATCHED ENGLISH:', unmatchedEnglish.join('; '));

  // ---- 5. establishments (stream file by file) ---------------------------
  const dir = cfg.paths.fhrs;
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.xml'));
  const estSql = `INSERT INTO establishment (fhrs_id, la_business_id, business_name,
    business_type_id, address_line1, address_line2, address_line3, address_line4,
    post_code, rating_value, rating_numeric, rating_date, la_code, scheme_type,
    new_rating_pending, longitude, latitude, hygiene_score, structural_score,
    confidence_score) VALUES ?`;
  let total = 0, fileNo = 0;
  const seenIds = new Set();
  for (const f of files) {
    fileNo++;
    let doc;
    try { doc = parser.parse(fs.readFileSync(path.join(dir, f), 'utf8')); }
    catch (e) { console.warn('  parse fail', f, e.message); continue; }
    const coll = doc?.FHRSEstablishment?.EstablishmentCollection?.EstablishmentDetail;
    const ests = asArray(coll);
    const newTypes = [];
    const batch = [];
    for (const e of ests) {
      const id = intOrNull(e.FHRSID);
      if (id == null || seenIds.has(id)) continue;   // guard against dup FHRSIDs across files
      seenIds.add(id);
      const btId = intOrNull(e.BusinessTypeID);
      if (btId != null && !btSeen.has(btId)) {
        btSeen.set(btId, txt(e.BusinessType) || `Type ${btId}`);
        newTypes.push([btId, btSeen.get(btId)]);
      }
      const rv = txt(e.RatingValue);
      const rn = rv != null && /^[0-5]$/.test(rv) ? parseInt(rv, 10) : null;
      const g = e.Geocode;
      const sc = (e.Scores && typeof e.Scores === 'object') ? e.Scores : {};
      batch.push([
        id, txt(e.LocalAuthorityBusinessID), txt(e.BusinessName), btId,
        txt(e.AddressLine1), txt(e.AddressLine2), txt(e.AddressLine3), txt(e.AddressLine4),
        txt(e.PostCode), rv, rn, dateOrNull(e.RatingDate), txt(e.LocalAuthorityCode),
        txt(e.SchemeType), txt(e.NewRatingPending) === 'True',
        numOrNull(g && g.Longitude), numOrNull(g && g.Latitude),
        intOrNull(sc.Hygiene), intOrNull(sc.Structural), intOrNull(sc.ConfidenceInManagement),
      ]);
    }
    if (newTypes.length) {
      await conn.query('INSERT IGNORE INTO business_type (business_type_id, business_type_name) VALUES ?', [newTypes]);
    }
    if (batch.length) await batchInsert(conn, estSql, batch);
    total += batch.length;
    if (fileNo % 25 === 0) console.log(`  loaded ${fileNo}/${files.length} files, ${total} establishments`);
  }
  console.log('TOTAL establishments loaded:', total);

  await conn.end();
}

function dateTime(s) {
  if (!s) return null;
  const m = String(s).match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})/);
  return m ? `${m[1]} ${m[2]}` : null;
}

main().catch(e => { console.error(e); process.exit(1); });
