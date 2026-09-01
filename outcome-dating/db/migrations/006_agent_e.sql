-- 006_agent_e.sql
-- Agent E (trust/moderation/report/appeal) schema addition.
--
-- `moderation.service#recordAutomatedFlag` (spec §18.2, §24.13) ingests one
-- automated signal at a time (a user report's computed score, message
-- velocity, device reputation, no-show, negative post-date feedback, ...).
-- None of the 26 spec tables + implied tables added in 001_init.sql is a
-- fit for this: `moderation_actions` records a DECISION already taken
-- (spec §23.23), `message_flags` is scoped to one message only (§23.15),
-- and `reports` is reporter-submitted structured reports only (§23.22).
-- `moderation.computeModerationScore` (spec §18.5) needs a durable,
-- queryable log of every raw signal that has been ingested for a user so
-- it can be summed — this table is that log.
--
-- Append-only, same shape as `trust_events` (§23.24) for the same reason:
-- "why is this user's moderation score what it is" must be reconstructable
-- without mutating history in place.

CREATE TABLE automated_moderation_flags (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  signal_type  text NOT NULL, -- e.g. "user_report", "message_velocity", "device_reputation" (§18.2)
  weight       double precision NOT NULL,
  metadata     jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_automated_moderation_flags_user_id ON automated_moderation_flags (user_id, created_at DESC);
