// Load the two geography/deprivation datasets added in db/schema_geo.sql:
//   * imd_lsoa  from IoD 2019 File 7 (LSOA-level), CSV already downloaded
//   * postcode  from the ONS Aug-2021 Postcode->LSOA(2011) lookup (389 MB CSV)
//
// The postcode lookup is streamed line-by-line and FILTERED to only the
// postcodes that actually occur in our establishments (~254k of 2.66M), so the
// loaded table stays small. This is an optimisation, not data invention: the
// full file is the documented source (etl/00_download_geo.sh) and no rows are
// fabricated. Re-running with a fuller establishment set would pick up more.
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const mysql = require('mysql2/promise');
const cfg = require('../config');

const RAW = cfg.paths.raw;
const num = (v) => { const n = parseFloat(v); return Number.isFinite(n) ? n : null; };
const int = (v) => { const n = parseInt(v, 10); return Number.isFinite(n) ? n : null; };

// Minimal CSV line splitter that respects double-quoted fields (IoD names have commas).
function splitCsv(line) {
  const out = []; let cur = '', q = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (q) { if (c === '"') { if (line[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
    else if (c === '"') q = true;
    else if (c === ',') { out.push(cur); cur = ''; }
    else cur += c;
  }
  out.push(cur);
  return out;
}
const normPc = (s) => (s || '').toUpperCase().replace(/\s+/g, '');

async function batch(conn, sql, rows, per = 2000) {
  for (let i = 0; i < rows.length; i += per) await conn.query(sql, [rows.slice(i, i + per)]);
}

async function main() {
  const conn = await mysql.createConnection({
    host: cfg.db.host, port: cfg.db.port, database: cfg.db.database,
    user: cfg.admin.user, password: cfg.admin.password,
  });
  console.log('Connected as', cfg.admin.user);

  // ---- imd_lsoa (IoD 2019 File 7) ---------------------------------------
  // Column indices within File 7 (0-based).
  const C = { lsoa: 0, name: 1, lad: 2, imdScore: 4, imdRank: 5, imdDec: 6,
    incScore: 7, incDec: 9, empScore: 10, empDec: 12, eduScore: 13, eduDec: 15,
    heaScore: 16, heaDec: 18, criScore: 19, criDec: 21, barScore: 22, barDec: 24,
    livScore: 25, livDec: 27, pop: 52 };
  const lsoaRows = [];
  {
    const rl = readline.createInterface({ input: fs.createReadStream(path.join(RAW, 'imd2019_lsoa_all.csv')) });
    let header = true;
    for await (const line of rl) {
      if (header) { header = false; continue; }
      if (!line.trim()) continue;
      const f = splitCsv(line);
      lsoaRows.push([
        f[C.lsoa], f[C.name], f[C.lad],
        num(f[C.imdScore]), int(f[C.imdRank]), int(f[C.imdDec]),
        num(f[C.incScore]), num(f[C.empScore]), num(f[C.eduScore]), num(f[C.heaScore]),
        num(f[C.criScore]), num(f[C.barScore]), num(f[C.livScore]),
        int(f[C.incDec]), int(f[C.empDec]), int(f[C.eduDec]), int(f[C.heaDec]),
        int(f[C.criDec]), int(f[C.barDec]), int(f[C.livDec]), int(f[C.pop]),
      ]);
    }
  }
  await batch(conn, `INSERT INTO imd_lsoa (lsoa11cd, lsoa11nm, lad_code, imd_score, imd_rank,
    imd_decile, income_score, employment_score, education_score, health_score, crime_score,
    barriers_score, living_score, income_decile, employment_decile, education_decile,
    health_decile, crime_decile, barriers_decile, living_decile, total_population) VALUES ?`, lsoaRows);
  console.log('imd_lsoa rows:', lsoaRows.length);

  // ---- which postcodes do we actually need? -----------------------------
  const [pcRows] = await conn.query(
    'SELECT DISTINCT postcode_norm FROM establishment WHERE postcode_norm IS NOT NULL');
  const need = new Set(pcRows.map(r => r.postcode_norm));
  console.log('distinct establishment postcodes to resolve:', need.size);

  // ---- stream the 389 MB ONS lookup, keep only needed postcodes ----------
  const big = path.join(RAW, 'pcd_unzip', 'PCD_OA_LSOA_MSOA_LAD_AUG21_UK_LU.csv');
  // header: pcd7,pcd8,pcds,dointr,doterm,usertype,oa11cd,lsoa11cd,msoa11cd,ladcd,...
  const PC = { pcds: 2, lsoa: 7, lad: 9 };
  const toInsert = [];
  let scanned = 0, matched = 0;
  {
    const rl = readline.createInterface({ input: fs.createReadStream(big) });
    let header = true;
    for await (const line of rl) {
      if (header) { header = false; continue; }
      scanned++;
      const f = splitCsv(line);
      const norm = normPc(f[PC.pcds]);
      if (!need.has(norm)) continue;
      need.delete(norm);                       // de-dup: keep first occurrence
      matched++;
      toInsert.push([norm, f[PC.pcds], f[PC.lsoa] || null, f[PC.lad] || null]);
      if (toInsert.length >= 5000) {
        await batch(conn, 'INSERT IGNORE INTO postcode (postcode_norm, pcds, lsoa11cd, lad_code) VALUES ?', toInsert);
        toInsert.length = 0;
      }
    }
  }
  if (toInsert.length) await batch(conn, 'INSERT IGNORE INTO postcode (postcode_norm, pcds, lsoa11cd, lad_code) VALUES ?', toInsert);
  console.log(`postcode lookup scanned ${scanned} rows, inserted ${matched} matching postcodes`);

  await conn.end();
}
main().catch(e => { console.error(e); process.exit(1); });
