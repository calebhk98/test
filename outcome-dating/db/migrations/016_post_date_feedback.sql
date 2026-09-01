-- 016_post_date_feedback.sql
--
-- Post-date check-in (product owner: "There 100% needs to be a post-date
-- check-in... it serves safety, outcome truth, and future matching signal
-- at once"). Extends the EXISTING `post_date_feedback` table
-- (001_init.sql) rather than duplicating it — that table already carries
-- one row per (date_proposal_id, user_id), which is exactly the
-- one-row-per-side shape a "usable even when only one side responds"
-- check-in needs. Nothing here alters or drops anything from an earlier
-- migration; every change is additive/nullable-or-defaulted so every
-- existing row, and `dateProposal.service#submitPostDateFeedback`'s
-- existing INSERT (frozen per INTERFACES.md — untouched by this build),
-- keeps working unmodified.
--
-- New columns on `post_date_feedback`:
--
--   outcome  — the four-way "did the date even happen, and how did it
--     go" distinction the product owner asked for (did_not_happen /
--     happened_bad / happened_fine / happened_good). Deliberately NOT the
--     same axis as the legacy `positive` boolean (kept, now nullable —
--     see below): collapsing "didn't happen" and "happened but bad" into
--     one boolean is exactly the conflation the product owner's brief
--     says must not happen. NULL for any row that only ever went through
--     the legacy `positive`-only path.
--
--   safety_flag  — 'none' | 'concern' | 'incident'. Fully separate from
--     `outcome`: a date can be `happened_good` and still carry a safety
--     flag (something happened after a fine-seeming evening), and a
--     `happened_bad` date very often carries no safety flag at all (bad
--     chemistry is not a safety problem). This column, and
--     `safety_details`, are the two fields
--     `postDateFeedback.service.ts` guarantees are NEVER returned by any
--     serializer/route to anyone but the row's own `user_id` — see that
--     file's module doc for the full isolation argument (routed into
--     `report.service#submitReport`, which already guarantees the
--     reporter's identity is never exposed to the reported party, rather
--     than surfaced as a distinguishable "post-date safety flag" through
--     any trust/aggregate view).
--
--   safety_details  — optional free text the user supplies alongside a
--     concern/incident flag. Same isolation as `safety_flag`. Cleared
--     server-side whenever `safety_flag = 'none'`.
--
--   report_id  — set once (at most) when a safety flag has been routed
--     into `reports` via `report.service#submitReport`, so a resubmission
--     of the same check-in row never files a second report for the same
--     declared incident. Nullable, no ON DELETE action needed beyond the
--     default (reports are never deleted).
--
--   matching_signal_processed_at  — marks a `happened_good`/`happened_bad`
--     row as already considered by `postDateFeedback.service
--     #runMatchingSignalSweep` (the §17 behavioral-prompt-suggestion
--     signal derived from outcome data), so the sweep never reprocesses
--     the same date twice and never accumulates unbounded work.
--
-- `positive` (existing, was NOT NULL) is relaxed to nullable: the new
-- richer submission path leaves it NULL and relies on `outcome` instead,
-- rather than lossily approximating a 4-way outcome as a boolean. The
-- legacy path is unaffected — it always supplies a boolean explicitly, so
-- relaxing the constraint only permits something new, it can never break
-- an existing call.
-- =========================================================================

ALTER TABLE post_date_feedback
  ALTER COLUMN positive DROP NOT NULL,
  ADD COLUMN outcome text
    CHECK (outcome IN ('did_not_happen', 'happened_bad', 'happened_fine', 'happened_good')),
  ADD COLUMN safety_flag text NOT NULL DEFAULT 'none'
    CHECK (safety_flag IN ('none', 'concern', 'incident')),
  ADD COLUMN safety_details text,
  ADD COLUMN report_id uuid REFERENCES reports (id),
  ADD COLUMN matching_signal_processed_at timestamptz;

-- Retaliation-weighting reads a submitter's own recent outcome history
-- (postDateFeedback.service#negativeFeedbackRetaliationWeight) and the
-- safety-corroboration check counts distinct flaggers against a target
-- (postDateFeedback.service#countDistinctSafetyFlaggersAgainst) — both hot
-- paths on every check-in submission.
CREATE INDEX idx_post_date_feedback_user_outcome
  ON post_date_feedback (user_id, created_at DESC) WHERE outcome IS NOT NULL;

CREATE INDEX idx_post_date_feedback_safety_flagged
  ON post_date_feedback (date_proposal_id) WHERE safety_flag <> 'none';

-- Matching-signal sweep candidate scan (postDateFeedback.service
-- #runMatchingSignalSweep): unprocessed happened_good/happened_bad rows.
CREATE INDEX idx_post_date_feedback_matching_signal_pending
  ON post_date_feedback (user_id)
  WHERE outcome IN ('happened_good', 'happened_bad') AND matching_signal_processed_at IS NULL;

-- =========================================================================
-- post_date_feedback_prompts
--
-- Timing state for the "prompt after scheduled end, with a window, and a
-- reminder — do not prompt endlessly" requirement
-- (postDateFeedback.service#runCheckInPromptSweep /
-- #ensureCheckInPromptSent). One row per (date_proposal, user) —
-- independent of `post_date_feedback` itself: a user may be prompted and
-- reminded and simply never answer, in which case no `post_date_feedback`
-- row for them ever exists at all (one-sided-by-default is the normal
-- case, not an edge case).
-- =========================================================================
CREATE TABLE post_date_feedback_prompts (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  date_proposal_id   uuid NOT NULL REFERENCES date_proposals (id) ON DELETE CASCADE,
  user_id            uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  prompt_count       integer NOT NULL DEFAULT 0,
  first_prompted_at  timestamptz,
  last_prompted_at   timestamptz,

  UNIQUE (date_proposal_id, user_id)
);

CREATE INDEX idx_post_date_feedback_prompts_date_proposal ON post_date_feedback_prompts (date_proposal_id);
