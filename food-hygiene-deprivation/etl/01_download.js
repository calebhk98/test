// Download every FHRS open-data XML file (one per local authority).
// Uses curl under the hood so it honours the environment's HTTPS proxy.
// Re-runnable: skips files already present unless --force is passed.
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const cfg = require('../config');

const FORCE = process.argv.includes('--force');
const CONCURRENCY = 8;

function curl(url, dest) {
  return new Promise((resolve, reject) => {
    // -f: fail on HTTP errors, -L: follow redirects, --retry: network retries
    execFile('curl', ['-fsSL', '--retry', '4', '--retry-delay', '2', '-m', '120',
      '-o', dest, url], { maxBuffer: 1 << 20 }, (err) => {
      if (err) { fs.rmSync(dest, { force: true }); return reject(err); }
      if (!fs.existsSync(dest) || fs.statSync(dest).size < 80) {
        fs.rmSync(dest, { force: true });
        return reject(new Error('empty/short file'));
      }
      resolve();
    });
  });
}

async function main() {
  fs.mkdirSync(cfg.paths.fhrs, { recursive: true });
  const authorities = require(path.join(cfg.paths.raw, 'authorities_full.json')).authorities;
  console.log(`Authorities to download: ${authorities.length}`);

  const queue = authorities.slice();
  let done = 0, skipped = 0; const failed = [];

  async function worker() {
    while (queue.length) {
      const a = queue.shift();
      const dest = path.join(cfg.paths.fhrs, `FHRS${a.LocalAuthorityIdCode}.xml`);
      if (!FORCE && fs.existsSync(dest) && fs.statSync(dest).size > 80) { skipped++; continue; }
      try {
        await curl(a.FileName, dest);
        done++;
        if ((done + skipped) % 25 === 0) console.log(`  ...${done + skipped}/${authorities.length}`);
      } catch (e) {
        failed.push({ code: a.LocalAuthorityIdCode, name: a.Name, err: e.message });
      }
    }
  }

  await Promise.all(Array.from({ length: CONCURRENCY }, worker));
  console.log(`Downloaded: ${done}, skipped(existing): ${skipped}, failed: ${failed.length}`);
  if (failed.length) console.log(JSON.stringify(failed, null, 2));
}

main().catch(e => { console.error(e); process.exit(1); });
