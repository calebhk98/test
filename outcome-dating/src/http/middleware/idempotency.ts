/**
 * src/http/middleware/idempotency.ts, mobile-readiness wiring: an
 * `Idempotency-Key` header on a write endpoint so a phone that retries
 * after losing signal (before ever seeing the first response) cannot
 * double-send an interest, double-post a message, or double-run any other
 * write this build wires it into.
 *
 * REUSES THE NOTIFICATION OUTBOX'S OWN DEDUPLICATION APPROACH (task
 * brief), rather than inventing a second one: `notification_outbox`'s
 * `notification_dedup_log` (db/migrations/011_notifications.sql) claims a
 * stable key via `INSERT ... ON CONFLICT (dedup_key) DO NOTHING`, the
 * atomic "have I seen this before" check `enqueueNotification` runs before
 * doing anything else (see `src/services/notifications/outbox.ts`'s own
 * doc). `idempotency_keys` (db/migrations/030_wiring.sql) is the identical
 * pattern, generalized to an arbitrary HTTP write and scoped per
 * `(endpoint, caller)` rather than a single global string, and it stores
 * the COMPLETED RESPONSE, not just a claim, because a retry must get back
 * the same response the original call produced, not merely "no second
 * effect happened" with nothing to hand the client.
 */
import type { FastifyRequest } from 'fastify';
import type { Ctx } from '../../lib/ctx.js';
import { ConflictError } from '../../lib/errors.js';
import { sha256Hex } from '../../lib/hash.js';

/** Reads the caller-supplied `Idempotency-Key` request header, if any. Absent means "no idempotency requested for this call", the handler just runs normally, exactly like every write endpoint before this build. */
export function idempotencyKeyHeader(req: FastifyRequest): string | undefined {
  const header = req.headers['idempotency-key'];
  if (Array.isArray(header)) return header[0];
  return header || undefined;
}

interface IdempotencyRow {
  status: 'in_progress' | 'completed';
  request_hash: string;
  response_status: number | null;
  response_body: unknown;
}

/** Scopes the same key string per-caller, so two different callers (or two different actor types) can legally reuse the identical key with zero collision risk, see this file's own doc. */
function actorKey(ctx: Ctx): string {
  switch (ctx.actor.type) {
    case 'user':
      return `user:${ctx.actor.userId}`;
    case 'venue_staff':
      return `venue_staff:${ctx.actor.venueStaffId}`;
    case 'admin':
      return `admin:${ctx.actor.adminId}`;
    case 'system':
      return `system:${ctx.actor.job}`;
  }
}

export interface IdempotentOutcome<T> {
  status: number;
  body: T;
  /** True when this call did NOT re-run `fn`, the stored response from an earlier call with the same key was replayed verbatim instead. */
  replayed: boolean;
}

/**
 * Runs `fn` (a route handler's own service call plus the HTTP status it
 * intends to reply with) under idempotency-key protection when `key` is
 * present, otherwise runs it straight through with no behavior change.
 *
 * Three outcomes for a present `key`:
 *  1. First time this `(scope, actor, key)` has been seen: claims the row
 *     atomically (`INSERT ... ON CONFLICT DO NOTHING`), runs `fn`, records
 *     the response, returns it, `replayed: false`.
 *  2. Same `(scope, actor, key)` seen before with the SAME request body
 *     hash, and that earlier call already completed: returns the stored
 *     response verbatim, WITHOUT running `fn` again, `replayed: true`.
 *     This is the actual retry-safety guarantee: a phone that resends the
 *     identical request after never seeing the first response gets the
 *     first call's real outcome back, not a second side effect and not an
 *     error.
 *  3. Same `(scope, actor, key)` but a DIFFERENT request body hash: a
 *     caller bug (the same idempotency key can only ever mean "this exact
 *     request"), rejected with `ConflictError` rather than silently
 *     processed as either the old or the new request.
 *
 * A same-key request that is still `in_progress` (a genuine concurrent
 * retry racing the still-running original) also gets `ConflictError`,
 * the client should back off and retry again shortly, exactly the
 * `outbox.ts`-style "claim, don't double-process" discipline this reuses.
 *
 * If `fn` itself throws, the claim is released (deleted) rather than left
 * stuck `in_progress` forever, so a retry after a genuine, transient
 * failure can still succeed.
 */
export async function withIdempotencyKey<T>(
  ctx: Ctx,
  opts: { scope: string; key: string | undefined; requestBody: unknown },
  fn: () => Promise<{ status: number; body: T }>,
): Promise<IdempotentOutcome<T>> {
  if (!opts.key) {
    const result = await fn();
    return { ...result, replayed: false };
  }

  const requestHash = sha256Hex(JSON.stringify(opts.requestBody ?? null));
  const actor = actorKey(ctx);

  const { rows: claimed } = await ctx.db.query<IdempotencyRow>(
    `INSERT INTO idempotency_keys (scope, actor_id, idempotency_key, request_hash, status, created_at)
     VALUES ($1, $2, $3, $4, 'in_progress', now())
     ON CONFLICT (scope, actor_id, idempotency_key) DO NOTHING
     RETURNING status, request_hash, response_status, response_body`,
    [opts.scope, actor, opts.key, requestHash],
  );

  if (claimed.length === 0) {
    const { rows: existingRows } = await ctx.db.query<IdempotencyRow>(
      `SELECT status, request_hash, response_status, response_body
       FROM idempotency_keys WHERE scope = $1 AND actor_id = $2 AND idempotency_key = $3`,
      [opts.scope, actor, opts.key],
    );
    const existing = existingRows[0];
    if (existing && existing.request_hash !== requestHash) {
      throw new ConflictError(
        'This idempotency key was already used for a different request. Use a new key for a genuinely new request.',
      );
    }
    if (existing?.status === 'completed') {
      return { status: existing.response_status ?? 200, body: existing.response_body as T, replayed: true };
    }
    throw new ConflictError('A request with this idempotency key is already being processed.');
  }

  try {
    const result = await fn();
    await ctx.db.query(
      `UPDATE idempotency_keys
       SET status = 'completed', response_status = $4, response_body = $5::jsonb, completed_at = now()
       WHERE scope = $1 AND actor_id = $2 AND idempotency_key = $3`,
      [opts.scope, actor, opts.key, result.status, JSON.stringify(result.body ?? null)],
    );
    return { ...result, replayed: false };
  } catch (err) {
    await ctx.db.query(
      `DELETE FROM idempotency_keys WHERE scope = $1 AND actor_id = $2 AND idempotency_key = $3 AND status = 'in_progress'`,
      [opts.scope, actor, opts.key],
    );
    throw err;
  }
}
