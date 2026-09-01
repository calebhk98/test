-- 008_questions.sql
-- Redesigned compatibility question bank (typed questions, value +
-- importance preferences, tag intensity/avoidance). Owned entirely by
-- this build; additive only, nothing here alters or drops a table from
-- 001_init.sql or any other existing migration.
--
-- BACKWARDS-COMPATIBILITY / MIGRATION CHOICE (documented per the task
-- brief's "say which you chose and why"):
--
--   CLEAN BREAK, not an in-place data migration. The OLD `questions`/
--   `answers` tables (001_init.sql) are left completely untouched, both
--   in schema and in the rows they hold, `compatibility.service.ts`,
--   `filter.service.ts`, and `behavioralPrompt.service.ts` (all off
--   limits to this build) keep reading/writing them exactly as before,
--   unmodified, and every test that exercises them keeps passing
--   unchanged.
--
--   Why not migrate old `answers` rows into the new shape? Because the
--   old rows are a flat 1-5 integer with NO type information, there is
--   no way to know, mechanically, whether a given old answer belongs on
--   a `scale` (where 1-5 is meaningful), a `single_choice` (where it was
--   never anything but 5 arbitrary buckets forced onto categorical data,
--   literally the bug this redesign exists to fix), or a `frequency`.
--   Auto-converting `self_value=3` into "the middle option of some
--   invented 5-option single_choice" would silently manufacture meaning
--   that was never there, which is worse than not migrating at all. Nor
--   did the old rows carry any IMPORTANCE data (the whole point of this
--   redesign) to backfill from, every migrated row would need a
--   fabricated default importance, which is exactly the kind of
--   "invented programmatically, not stated by the user" data the task
--   brief's importance model is designed to eliminate.
--
--   So: new tables, new (empty) starting state, new typed bank seeded by
--   `src/seed.ts`. Existing users keep their OLD answers/scores working
--   exactly as before (nothing regresses) and get a clean opportunity to
--   answer the NEW bank going forward. When a later agent wires
--   `compatibility.service.ts` to `src/domain/questions/scoring.ts` (see
--   that file's integration-seam doc), the natural point to retire the
--   old tables is once real users have re-answered enough of the new
--   bank to score meaningfully, a product decision, not a schema one,
--   and out of scope here.

-- =========================================================================
-- question_bank, versioned, typed question definitions.
--
-- One row per (slug, version). Editing a question (text, options, scale
-- labels, ...) inserts a NEW row with `version = old.version + 1` and
-- `is_current = true`, flipping the previous row's `is_current` to
-- false, it is never updated or deleted in place. This is what "answer-
-- version pinning" (see `user_question_answers.question_bank_id` below)
-- relies on: an answer's FK target is immutable for the lifetime of that
-- answer, so editing a question can never silently change what an
-- existing answer meant.
-- =========================================================================
CREATE TABLE question_bank (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug               text NOT NULL,
  version            integer NOT NULL DEFAULT 1 CHECK (version >= 1),
  is_current         boolean NOT NULL DEFAULT true,
  category           text NOT NULL,
  subcategory        text,
  tags               text[] NOT NULL DEFAULT '{}',
  question_type      text NOT NULL CHECK (question_type IN ('scale', 'single_choice', 'multi_choice', 'frequency')),
  question_text      text NOT NULL,
  -- Type-specific shape (ScaleDefinition / SingleChoiceDefinition /
  -- MultiChoiceDefinition / FrequencyDefinition, src/domain/questions/types.ts).
  -- Kept as jsonb (not columns) specifically so a fifth question type can
  -- be added later without a schema migration touching this table, see
  -- that file's "Design the type system so a new type can be added later
  -- without touching the scoring core" requirement.
  type_definition    jsonb NOT NULL,
  base_weight        double precision NOT NULL DEFAULT 1.0 CHECK (base_weight >= 0),
  sensitive          boolean NOT NULL DEFAULT false,
  active             boolean NOT NULL DEFAULT true,
  -- Selector priority signal (src/domain/questions/selector.ts), fraction
  -- of users shown this question who go on to answer rather than skip it.
  answer_rate_hint   double precision NOT NULL DEFAULT 0.5 CHECK (answer_rate_hint BETWEEN 0 AND 1),
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),

  UNIQUE (slug, version)
);

-- Exactly one current version per slug, this is the row the "what should
-- we ask next" selector and the admin bank listing read.
CREATE UNIQUE INDEX uq_question_bank_current_slug ON question_bank (slug) WHERE is_current;
CREATE INDEX idx_question_bank_active_category ON question_bank (category) WHERE active AND is_current;
CREATE INDEX idx_question_bank_slug ON question_bank (slug);
-- Paging the active current bank (600+ questions) without a full scan:
-- question.service.ts's paged listing orders by (category, id) and keys
-- off this index rather than loading every row per request.
CREATE INDEX idx_question_bank_paging ON question_bank (category, id) WHERE active AND is_current;

-- =========================================================================
-- user_question_answers, a user's answer to a new-bank question.
--
-- One row per (user, question SLUG), not per (user, question_bank row),
-- because a user has at most one CURRENT answer to a question regardless
-- of how many versions that question has gone through;
-- `question_bank_id` records exactly which immutable version that answer
-- was given under (the "pin"), while `question_slug` is what lookups and
-- the selector's history/exclusion logic key off (a slug is stable across
-- versions, an id is not).
--
-- `status` has no 'unanswered' value, "never shown/never answered" is
-- represented by the ABSENCE of a row (see src/domain/questions/types.ts
-- `AnswerStatus` for why this is deliberate: the pure domain layer models
-- all four states explicitly for testing/scoring purposes, but persisting
-- a row for "never answered" would mean writing one row per user per
-- question in the bank just to represent nothing, which does not scale
-- to 600+ questions x many users).
-- =========================================================================
CREATE TABLE user_question_answers (
  user_id           uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  question_slug     text NOT NULL,
  question_bank_id  uuid NOT NULL REFERENCES question_bank (id),
  status            text NOT NULL CHECK (status IN ('skipped', 'prefer_not_to_say', 'answered')),
  -- Typed per the pinned version's question_type, validated at the
  -- application layer (src/domain/questions/typeHandlers.ts) before
  -- write, not by a CHECK constraint (the shape varies per type). NULL
  -- unless status = 'answered'.
  self_value        jsonb,
  preference_value  jsonb,
  importance        text CHECK (importance IN ('irrelevant', 'slight', 'important', 'critical', 'deal_breaker')),
  answered_at       timestamptz NOT NULL,
  updated_at        timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (user_id, question_slug),
  CONSTRAINT user_question_answers_answered_shape CHECK (
    (status = 'answered' AND self_value IS NOT NULL AND preference_value IS NOT NULL AND importance IS NOT NULL)
    OR
    (status <> 'answered' AND self_value IS NULL AND preference_value IS NULL AND importance IS NULL)
  )
);

-- Sparse-answer lookups: "every user who answered question X" (used by
-- e.g. answer-rate stat computation) without scanning every user's row.
CREATE INDEX idx_user_question_answers_slug ON user_question_answers (question_slug);
-- Deal-breaker filter derivation (src/domain/questions/dealBreakers.ts)
-- scans one user's own deal breakers only, PK already covers that via
-- (user_id, question_slug), but importance is filtered on, so index it
-- for the common "this user's deal breakers" query.
CREATE INDEX idx_user_question_answers_deal_breakers ON user_question_answers (user_id) WHERE importance = 'deal_breaker';

-- =========================================================================
-- user_tag_intensity, "I bake" is not one thing: how often/how much.
-- Meaningful alongside a held `user_tags` row for the same tag (not
-- enforced by FK, a user can set intensity before/independently of
-- visibility bookkeeping, and `user_tags` is owned by the pre-existing
-- §8.4 reciprocal-disclosure code path this build does not touch).
-- =========================================================================
CREATE TABLE user_tag_intensity (
  user_id     uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  tag_id      uuid NOT NULL REFERENCES interest_tags (id) ON DELETE CASCADE,
  intensity   text NOT NULL CHECK (intensity IN ('rarely', 'occasionally', 'regularly', 'frequently', 'daily')),
  updated_at  timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (user_id, tag_id)
);

-- =========================================================================
-- user_avoid_tags, "do not show me people who list <tag>". A hard
-- exclusion, symmetric with `user_tags` (same PK shape) but semantically
-- opposite: presence here means "avoid", not "hold".
-- =========================================================================
CREATE TABLE user_avoid_tags (
  user_id     uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  tag_id      uuid NOT NULL REFERENCES interest_tags (id) ON DELETE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (user_id, tag_id)
);

CREATE INDEX idx_user_avoid_tags_tag ON user_avoid_tags (tag_id);
