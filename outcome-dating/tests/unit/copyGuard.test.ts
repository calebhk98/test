/**
 * copyGuard.test.ts — build-failing scan for spec citations/section marks
 * leaking into user-visible strings (docs/ux-api-review.md §14: "Spec
 * section references baked into the string", "Raw parameter/internal-name
 * leaks"). Users have no access to the specification and must never see
 * one of its section numbers or the literal word "spec" used as a
 * citation.
 *
 * SCOPE: every `.ts` file under `src/services/**` and `src/http/**` —
 * this is where a string can become part of `error.message` (sent
 * verbatim to the client, see `src/http/errors.ts`) or become static
 * user-facing copy — EXCEPT two files that hold spec citations as
 * internal, never-serialized audit metadata by design, not user copy:
 *
 *   - `src/http/routeTable.ts` — its own header explains its `spec`
 *     column is "the route -> spec-section coverage table," read only by
 *     `tests/http/routeTable.test.ts`; never sent to an HTTP client.
 *   - `src/config/config.service.ts` — its `specSection` field is
 *     internal config-registry metadata, never returned by any route.
 *
 * `src/jobs/**` is also out of scope: a job's `description` is operator/
 * CLI-facing (`jobs:run`, process logs), never reachable by an app user.
 *
 * HOW THE SCAN WORKS: this is a real lexical scan, not a spot check — it
 * extracts every single-, double-, and backtick-quoted string/template
 * literal from each in-scope file's raw source (comments are naturally
 * excluded: `§`/`spec` inside a `//` or `/* *\/` comment is never inside a
 * quoted literal) and fails the moment ANY of them contains a section
 * mark (`§`) or the word "spec" used as a citation (`spec §…`, `(spec
 * …)`, "spec section …"). `it actually catches something` is proven
 * below by running the exact same scanner against deliberately-violating
 * fixture source text, not just asserting it stays quiet on real files.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const SRC_ROOT = join(import.meta.dirname, '..', '..', 'src');

const SCAN_DIRS = ['services', 'http'];

/** Files whose spec citations are documented, never-serialized internal audit metadata — see file doc above. */
const EXEMPT_FILES = new Set(['src/http/routeTable.ts', 'src/config/config.service.ts']);

function listTsFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      out.push(...listTsFiles(full));
    } else if (entry.endsWith('.ts')) {
      out.push(full);
    }
  }
  return out;
}

/**
 * Strips every `//` line comment and `/* *\/` block comment out of
 * `source`, character-by-character, WITHOUT touching the contents of any
 * string/template literal along the way (a quote character seen while
 * scanning is tracked and its contents are copied through verbatim,
 * escapes included, so a `//` or `/*` inside a real string is never
 * mistaken for a comment start).
 *
 * This step exists specifically because this codebase's JSDoc comments
 * constantly use `` `backtick code formatting` `` for identifiers — a
 * naive "just regex-match quoted literals over the raw file" pass (this
 * scanner's first draft) mistakes those comment-internal backticks for
 * template-literal delimiters and then eats everything up to the NEXT
 * unrelated backtick anywhere later in the file as one giant "string,"
 * producing false positives on every doc comment that happens to mention
 * a spec section. Stripping comments first removes the ambiguity at the
 * source: after this pass, every remaining backtick is a real template
 * literal delimiter.
 */
function stripComments(source: string): string {
  let out = '';
  let i = 0;
  const n = source.length;
  while (i < n) {
    const c = source[i]!;
    const c2 = source[i + 1];
    if (c === '/' && c2 === '/') {
      while (i < n && source[i] !== '\n') i++;
      continue;
    }
    if (c === '/' && c2 === '*') {
      i += 2;
      while (i < n && !(source[i] === '*' && source[i + 1] === '/')) i++;
      i += 2;
      continue;
    }
    if (c === "'" || c === '"' || c === '`') {
      const quote = c;
      out += c;
      i++;
      while (i < n) {
        const ch = source[i]!;
        out += ch;
        if (ch === '\\') {
          i++;
          if (i < n) {
            out += source[i];
            i++;
          }
          continue;
        }
        i++;
        if (ch === quote) break;
      }
      continue;
    }
    out += c;
    i++;
  }
  return out;
}

/**
 * Extracts the raw contents of every single/double/backtick-quoted
 * string or template literal in `source` (comments must already be
 * stripped — see `stripComments` above — or a comment-internal backtick
 * will be misread as a literal delimiter).
 */
function extractStringLiterals(source: string): string[] {
  const pattern = /'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`/g;
  const literals: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(source)) !== null) {
    literals.push(m[0].slice(1, -1));
  }
  return literals;
}

/** A section mark, or the word "spec" used as a citation (e.g. "spec §13.1", "(spec section 13)", "per spec 13.1"). Word-bounded so "specific"/"specify"/"inspect" never false-positive. */
const SECTION_MARK = /§/;
const SPEC_CITATION = /\bspec\b\s*(§|section|document|\.?\s*\d)/i;

export interface CopyViolation {
  file: string;
  literal: string;
}

/** Runs the scan over an arbitrary list of `{ file, source }` pairs — factored out so the test below can run it both against the real tree and against a deliberate fixture violation, proving this is a live scan. */
export function scanForSpecLeaks(sources: Array<{ file: string; source: string }>): CopyViolation[] {
  const violations: CopyViolation[] = [];
  for (const { file, source } of sources) {
    if (EXEMPT_FILES.has(file)) continue;
    for (const literal of extractStringLiterals(stripComments(source))) {
      if (SECTION_MARK.test(literal) || SPEC_CITATION.test(literal)) {
        violations.push({ file, literal });
      }
    }
  }
  return violations;
}

function realTreeSources(): Array<{ file: string; source: string }> {
  const out: Array<{ file: string; source: string }> = [];
  for (const dir of SCAN_DIRS) {
    for (const absPath of listTsFiles(join(SRC_ROOT, dir))) {
      const relPath = relative(join(SRC_ROOT, '..'), absPath).split('\\').join('/');
      out.push({ file: relPath, source: readFileSync(absPath, 'utf8') });
    }
  }
  return out;
}

test('copy guard: no §-marked or spec-cited string literal anywhere under src/services or src/http (except the two documented internal-audit-metadata files)', () => {
  const violations = scanForSpecLeaks(realTreeSources());
  assert.deepEqual(
    violations,
    [],
    `Found ${violations.length} user-facing string(s) containing a section mark or spec citation:\n` +
      violations.map((v) => `  ${v.file}: ${JSON.stringify(v.literal)}`).join('\n'),
  );
});

test('copy guard: the scanner itself actually catches a violation (not a silent no-op)', () => {
  const fixtures = [
    { file: 'src/services/fixture.service.ts', source: "throw new ValidationError('Not allowed here (spec §13.1)');" },
    { file: 'src/services/fixture2.service.ts', source: "throw new ConflictError(`Illegal transition per spec section 9`);" },
    { file: 'src/services/fixture3.service.ts', source: "const ok = 'this mentions a specific spec, but not as a citation';" },
  ];
  const violations = scanForSpecLeaks(fixtures);
  const flaggedFiles = new Set(violations.map((v) => v.file));
  assert.ok(flaggedFiles.has('src/services/fixture.service.ts'), 'a literal §-citation must be flagged');
  assert.ok(flaggedFiles.has('src/services/fixture2.service.ts'), 'a "spec section N" citation must be flagged');
  assert.ok(!flaggedFiles.has('src/services/fixture3.service.ts'), 'the word "specific" must never false-positive');
});

test('copy guard: the two documented internal-audit-metadata files are exempt, but nothing else is', () => {
  const fixtures = [
    { file: 'src/http/routeTable.ts', source: "{ spec: '§24.1, §5' }" },
    { file: 'src/config/config.service.ts', source: "specSection: '§21.4'" },
    { file: 'src/http/routes/somewhere.routes.ts', source: "throw new Error('should be caught (spec §1)');" },
  ];
  const violations = scanForSpecLeaks(fixtures);
  const flaggedFiles = new Set(violations.map((v) => v.file));
  assert.ok(!flaggedFiles.has('src/http/routeTable.ts'), 'routeTable.ts is exempt');
  assert.ok(!flaggedFiles.has('src/config/config.service.ts'), 'config.service.ts is exempt');
  assert.ok(flaggedFiles.has('src/http/routes/somewhere.routes.ts'), 'every other file must still be scanned');
});
