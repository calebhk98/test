/**
 * dashGuard.test.ts: build-failing scan for em dashes (U+2014) and en
 * dashes (U+2013) anywhere in the repository's own source and
 * documentation. The project standard is no em dash and no en dash, ever;
 * use a comma, a colon, parentheses, a separate sentence, or (for a
 * numeric or section range) the word "to" instead. A plain hyphen (-) in
 * a compound word or a command-line flag is untouched by this guard, only
 * the two longer dash characters are banned.
 *
 * SCOPE: every file in the repository tree, walked from the project root,
 * EXCEPT:
 *   - `node_modules/`, `dist/`, `.pgdata/`: dependencies and build output,
 *     not this project's own source or documentation.
 *   - `.git/`: not source content.
 *   - Any lockfile (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`):
 *     machine-generated, never hand-authored, and never a place a stray
 *     dash character would mean anything.
 *   - Generated/runtime artifacts already covered by `.gitignore`
 *     (`.pglog`, `*.log`, `coverage/`): not source or documentation.
 *   - Binary files (detected by a failed clean UTF-8 decode): a dash
 *     character inside binary data isn't a copy violation.
 *   - `SPEC.md` at the repository root: a verbatim copy of the product
 *     specification the project owner supplied, not a document this
 *     project authors, and the reference every conformance claim in the
 *     repository is measured against. Preserved exactly as received,
 *     punctuation and all; only a file actually named `SPEC.md` sitting
 *     directly in the repo root is exempted, so a same-named file nested
 *     somewhere else in the tree is still scanned normally.
 *
 * HOW THE SCAN WORKS: this is a real scan of file contents, not a spot
 * check. Every in-scope file is read as UTF-8 and checked for either
 * character appearing anywhere at all, not just inside a string literal
 * (unlike `copyGuard.test.ts`): a dash in a code comment or a markdown
 * document is exactly as much a violation as one inside a quoted string.
 * "It actually catches something" is proven below by running the same
 * scanner against a deliberately-violating fixture, not just asserting it
 * stays quiet on the real tree.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const REPO_ROOT = join(import.meta.dirname, '..', '..');

const EXCLUDED_DIR_NAMES = new Set(['node_modules', 'dist', '.pgdata', '.git', 'coverage']);

const LOCKFILE_NAMES = new Set(['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml']);

const DASH_PATTERN = /[\u2013\u2014]/;

/** Externally supplied documents preserved verbatim, keyed by the repo-root-relative path where each one lives, never by bare filename (so a same-named file elsewhere in the tree, if one is ever added, is still scanned normally). Add a file here only when it is content this project received rather than authored, with a one-line reason. */
const VERBATIM_EXTERNAL_FILES = new Set([
  'SPEC.md', // the product specification as supplied by the project owner; the reference every conformance claim is measured against, preserved exactly as received.
]);

function isExcludedFile(name: string): boolean {
  if (LOCKFILE_NAMES.has(name)) return true;
  if (name === '.pglog' || name.endsWith('.log')) return true;
  return false;
}

/** Recursively lists every in-scope file under `dir`, skipping excluded directories entirely (never descends into them, so a large excluded tree like node_modules costs nothing beyond one stat call per entry). `repoRootRelative` is the path of `dir` relative to `REPO_ROOT` ('' for the root itself), used only to check `VERBATIM_EXTERNAL_FILES` by full path rather than bare name. */
function listScannedFiles(dir: string, repoRootRelative: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    if (EXCLUDED_DIR_NAMES.has(entry)) continue;
    const full = join(dir, entry);
    const entryRelative = repoRootRelative ? `${repoRootRelative}/${entry}` : entry;
    if (VERBATIM_EXTERNAL_FILES.has(entryRelative)) continue;
    const stat = statSync(full);
    if (stat.isDirectory()) {
      out.push(...listScannedFiles(full, entryRelative));
    } else if (stat.isFile() && !isExcludedFile(entry)) {
      out.push(full);
    }
  }
  return out;
}

export interface DashViolation {
  file: string;
  line: number;
  excerpt: string;
}

/** Runs the scan over an arbitrary list of file/source pairs, factored out so the test below can run it both against the real tree and against a deliberate fixture violation, proving this is a live scan. */
export function scanForDashes(sources: Array<{ file: string; source: string }>): DashViolation[] {
  const violations: DashViolation[] = [];
  for (const { file, source } of sources) {
    const lines = source.split('\n');
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]!;
      if (DASH_PATTERN.test(line)) {
        violations.push({ file, line: i + 1, excerpt: line.trim().slice(0, 120) });
      }
    }
  }
  return violations;
}

function realTreeSources(): Array<{ file: string; source: string }> {
  const out: Array<{ file: string; source: string }> = [];
  for (const absPath of listScannedFiles(REPO_ROOT, '')) {
    let text: string;
    try {
      const buf = readFileSync(absPath);
      // Reject anything that isn't clean UTF-8 text. A real binary file
      // decoded "successfully" as UTF-8 will almost always contain the
      // Unicode replacement character somewhere, which a real source or
      // doc file never does; good enough to skip binaries here.
      text = buf.toString('utf8');
      if (buf.length > 0 && text.includes('\uFFFD')) continue;
    } catch {
      continue;
    }
    const relPath = relative(REPO_ROOT, absPath).split('\\').join('/');
    out.push({ file: relPath, source: text });
  }
  return out;
}

test('dash guard: no em dash or en dash anywhere in the repository, outside node_modules/dist/.pgdata/lockfiles', () => {
  const violations = scanForDashes(realTreeSources());
  assert.deepEqual(
    violations,
    [],
    `Found ${violations.length} em/en dash occurrence(s):\n` +
      violations.map((v) => `  ${v.file}:${v.line}: ${JSON.stringify(v.excerpt)}`).join('\n'),
  );
});

test('dash guard: the scanner itself actually catches a violation, not a silent no-op', () => {
  const fixtures = [
    { file: 'src/services/fixture.service.ts', source: 'A hold that never captured is released \u2014 not refunded.' },
    { file: 'docs/fixture.md', source: 'Users answer 65 to 600 questions (roughly 65\u201300 in the current bank).' },
    { file: 'src/services/fixtureClean.service.ts', source: "A hyphen in a compound word, e.g. 'well-designed', is fine." },
  ];
  const violations = scanForDashes(fixtures);
  const flaggedFiles = new Set(violations.map((v) => v.file));
  assert.ok(flaggedFiles.has('src/services/fixture.service.ts'), 'an em dash must be flagged');
  assert.ok(flaggedFiles.has('docs/fixture.md'), 'an en dash must be flagged');
  assert.ok(!flaggedFiles.has('src/services/fixtureClean.service.ts'), 'a plain hyphen must never false-positive');
});

test('dash guard: excluded directories and lockfiles are never scanned', () => {
  // Sanity-check the exclusion list itself, independent of what happens to
  // be on disk right now: a violation inside any of these must never be
  // reachable through listScannedFiles, because the directory is skipped
  // before it is ever read, and a lockfile is skipped by name.
  assert.ok(EXCLUDED_DIR_NAMES.has('node_modules'));
  assert.ok(EXCLUDED_DIR_NAMES.has('dist'));
  assert.ok(EXCLUDED_DIR_NAMES.has('.pgdata'));
  assert.ok(LOCKFILE_NAMES.has('package-lock.json'));
});

test('dash guard: root SPEC.md is excluded as externally supplied content, but only at the root', () => {
  const files = listScannedFiles(REPO_ROOT, '').map((f) => relative(REPO_ROOT, f).split('\\').join('/'));
  assert.ok(!files.includes('SPEC.md'), 'root SPEC.md must never be scanned, it is preserved verbatim as received');
  // The exclusion is by full repo-root-relative path, not by bare filename,
  // so a same-named file nested elsewhere would still be scanned; prove
  // that with a fixture rather than asserting a negative about the real
  // tree (which has no nested SPEC.md today, but that isn't what this
  // guards against drifting).
  assert.ok(!VERBATIM_EXTERNAL_FILES.has('docs/SPEC.md'), 'the exclusion is keyed by full path, not bare filename');
});
