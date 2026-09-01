/**
 * src/lib/cursor.ts, shared `(timestamp, id)` keyset-pagination cursor
 * codec.
 *
 * Every list endpoint that pages newest-first over a `(created_at, id)` (or
 * equivalent) ordering encodes its cursor the same way:
 * `base64url("<ISO-8601 timestamp>|<id>")`. Before this module existed,
 * five services each hand-rolled their own `encodeCursor`/`decodeCursor`
 * pair against that identical wire format, and they'd already drifted:
 * `timeline.service.ts` and `matches.service.ts` checked the decoded date
 * for `Invalid Date` and threw a clean `ValidationError`; `notification`,
 * `message`, and `interest` did not, so a malformed-but-parseable cursor
 * (e.g. a corrupted or hand-tampered date component) sailed through as a
 * real `Date` object straight into a parameterized SQL query, where
 * node-postgres throws a raw `RangeError: Invalid time value` that the
 * generic HTTP error handler turns into an unintended 500, for what is
 * really ordinary bad client input (see docs/duplication.md finding 3).
 *
 * `decodeTimestampIdCursor` below is the ONE validated decoder: it always
 * throws `ValidationError` (-> HTTP 400 via src/http/errors.ts) for any
 * malformed, truncated, tampered, wrong-type, or null/invalid-date cursor,
 * so every endpoint that adopts it gets the same 400 (never a 500) for bad
 * input, without re-deriving the validation itself.
 *
 * Adopting this module changes no already-issued cursor's wire format for
 * a service that already uses the plain `base64url("iso|id")` scheme
 * (notification/message/interest/matches/timeline), it only tightens
 * validation. `ledger.service.ts` uses a different, JSON-array wire format
 * and ID-only schemes (`question.service.ts`) or offset-integer cursors
 * (`discovery`/`trust#listMyTrustEvents`/`moderation`/`venueSettlement`)
 * are out of scope for this helper, see docs/duplication.md findings 3/4/8.
 */
import { ValidationError } from './errors.js';

export interface TimestampIdCursor {
  ts: Date;
  id: string;
}

const CURSOR_ERROR = 'Invalid pagination cursor.';

/** Encodes a `(timestamp, id)` pair as the shared opaque cursor string. */
export function encodeTimestampIdCursor(ts: Date, id: string): string {
  return Buffer.from(`${ts.toISOString()}|${id}`, 'utf8').toString('base64url');
}

/**
 * Decodes and STRICTLY validates a cursor produced by
 * `encodeTimestampIdCursor`. Throws `ValidationError`, never returns a
 * value that would let an invalid `Date` reach a query, for:
 *  - a non-string input (wrong type: number, null, undefined, object, ...)
 *  - an empty string
 *  - a string that, once base64url-decoded, has no `|` separator, or has
 *    nothing on one side of it (truncation that ate the separator or a
 *    whole field; tampering that corrupted the delimiter)
 *  - a timestamp component that does not parse to a valid `Date` (a
 *    literal `"null"`/`"undefined"`/garbage date, or any other corrupted-
 *    but-decodable timestamp), this is the check three of the five
 *    pre-existing per-service decoders were missing.
 *
 * Deliberately accepts `unknown` (not `string`) so callers can hand it a
 * query-string value straight from validated-but-loosely-typed input
 * without a separate type-guard step.
 */
export function decodeTimestampIdCursor(cursor: unknown): TimestampIdCursor {
  if (typeof cursor !== 'string' || cursor.length === 0) {
    throw new ValidationError(CURSOR_ERROR);
  }

  let decoded: string;
  try {
    decoded = Buffer.from(cursor, 'base64url').toString('utf8');
  } catch {
    throw new ValidationError(CURSOR_ERROR);
  }

  const sepIndex = decoded.indexOf('|');
  if (sepIndex <= 0 || sepIndex === decoded.length - 1) {
    throw new ValidationError(CURSOR_ERROR);
  }

  const iso = decoded.slice(0, sepIndex);
  const id = decoded.slice(sepIndex + 1);

  const ts = new Date(iso);
  if (Number.isNaN(ts.getTime())) {
    throw new ValidationError(CURSOR_ERROR);
  }

  return { ts, id };
}
