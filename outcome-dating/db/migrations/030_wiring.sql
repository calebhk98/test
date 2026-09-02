-- 030_wiring.sql
--
-- Schema support for wiring item 6 (mobile readiness): a per-caller,
-- per-endpoint idempotency ledger so a phone that retries a write after
-- losing signal cannot double-send an interest, double-post a message, or
-- double-run any other write this build wires it into
-- (`src/http/middleware/idempotency.ts`).
--
-- DELIBERATELY THE SAME SHAPE AS THE EXISTING DEDUPLICATION APPROACH
-- (task brief: "reuse the deduplication approach the notification outbox
-- already uses rather than inventing a second one"): `notification_outbox`
-- (db/migrations/011_notifications.sql)'s `notification_dedup_log` is a
-- one-row-per-stable-key table, claimed via
-- `INSERT ... ON CONFLICT (dedup_key) DO NOTHING`, the atomic "have I seen
-- this before" check `enqueueNotification` performs before doing anything
-- else. `idempotency_keys` below is the identical pattern generalized to
-- an arbitrary HTTP write: the key is `(scope, actor_id, idempotency_key)`
-- rather than a single `dedup_key` string, because the SAME client-chosen
-- idempotency key string must never collide across two different callers
-- or two different endpoints (a UUID a phone generates for "propose this
-- date" must not accidentally dedupe against the same UUID reused for
-- "send this interest", or against a different user who happened to pick
-- the same key), and it stores the completed response (`response_status`/
-- `response_body`), not just an id, because a retry must get back the
-- SAME response the original call produced, not merely "no second effect"
-- with no way to tell the caller what happened.
CREATE TABLE IF NOT EXISTS idempotency_keys (
  -- Which write this claims, convention "<METHOD> <route-table path>"
  -- (e.g. "POST /interests"), so the same key string is scoped per
  -- endpoint, never global.
  scope             text NOT NULL,
  -- The caller: 'user:<uuid>' / 'venue_staff:<uuid>' / 'admin:<uuid>' /
  -- 'system:<job>' (src/http/middleware/idempotency.ts's own `actorKey`),
  -- so two different callers can legally reuse the identical key string
  -- with zero collision risk.
  actor_id          text NOT NULL,
  -- The caller-supplied `Idempotency-Key` header value.
  idempotency_key   text NOT NULL,
  -- SHA-256 of the request body. A SECOND request reusing the same key
  -- with a DIFFERENT body is a caller bug (the whole point of the key is
  -- "this is the same request"), never silently replayed or silently
  -- treated as new; the middleware rejects it with a 409.
  request_hash      text NOT NULL,
  status            text NOT NULL DEFAULT 'in_progress'
                      CHECK (status IN ('in_progress', 'completed')),
  -- Populated only once status = 'completed': the exact response a retry
  -- with the same key must replay verbatim.
  response_status   integer,
  response_body     jsonb,
  created_at        timestamptz NOT NULL DEFAULT now(),
  completed_at      timestamptz,

  PRIMARY KEY (scope, actor_id, idempotency_key)
);

-- Retention-sweep-friendly: same "index the age column a batched cleanup
-- filters by" discipline db/migrations/021_retention_i18n.sql's PART 1
-- already established for every other high-volume, terminal-status table
-- in this codebase. No sweep is added by this build (out of the six
-- items), the index is here so one can be added later without a further
-- migration.
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_created_at ON idempotency_keys (created_at);
