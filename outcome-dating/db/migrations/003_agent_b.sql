-- 003_agent_b.sql
-- Additive migration owned by Agent B (question/filter/compatibility/
-- discovery/behavioralPrompt).
--
-- 001_init.sql has no table for §17 behavioral-question-trigger
-- suggestions. `moderation_actions`/`trust_events`/`notifications` are all
-- the wrong shape (they're not "a question we want to ask the user and are
-- waiting on an explicit yes/skip response to"). This is genuinely new
-- schema, not a repurposing of an existing table — hence a new migration
-- rather than editing 001_init.sql (frozen) or a sibling's 002/006.
-- Nothing here alters or drops anything from an earlier migration.

-- =========================================================================
-- behavioral_prompt_suggestions                                      §17
-- One row per (user, question, trigger) suggestion `detectPatternsForUser`
-- has surfaced. `status` tracks the explicit response the spec requires
-- (§17 rules 1+3: never assume, always ask explicitly; rule 4: skippable)
-- — there is no path anywhere in `behavioralPrompt.service.ts` that writes
-- to `answers` directly; `respondToSuggestion` forwards a non-skip
-- response to `question.service#putMyAnswers` and only then marks this row
-- `answered`.
-- =========================================================================
CREATE TABLE behavioral_prompt_suggestions (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  question_id    uuid NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
  trigger_kind   text NOT NULL,   -- e.g. "tag" (§17 example: a shared interest_tag pattern)
  trigger_label  text NOT NULL,   -- static-template input, e.g. the tag name ("hiking")
  status         text NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'skipped', 'answered')),
  created_at     timestamptz NOT NULL DEFAULT now(),
  responded_at   timestamptz
);

CREATE INDEX idx_behavioral_prompt_suggestions_user ON behavioral_prompt_suggestions (user_id, status);

-- At most one *pending* suggestion per (user, question) — re-triggering the
-- same pattern while one is already awaiting a response is a no-op, not a
-- duplicate row (a new one may be created again once the existing one is
-- answered/skipped).
CREATE UNIQUE INDEX uq_behavioral_prompt_suggestions_pending
  ON behavioral_prompt_suggestions (user_id, question_id) WHERE status = 'pending';
