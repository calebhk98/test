-- 022_drop_old_question_bank.sql
--
-- Finishes the question-system cutover 019_question_cutover.sql could not
-- complete: drops the OLD question bank (`questions`/`answers`,
-- 001_init.sql) outright.
--
-- WHY THIS IS SAFE NOW, WHEN IT WASN'T IN 019: 019's own header explained
-- that four files outside that build's file-ownership boundary still read
-- or wrote `questions`/`answers` directly, so dropping the tables then
-- would have broken them at runtime. This build owns all four of those
-- files and has repointed every one of them at the ONE typed bank
-- (`question_bank`/`user_question_answers`, 008_questions.sql) before this
-- migration runs:
--   - src/http/routes/admin.routes.ts       -- §27 admin question manager
--   - src/services/behavioralPrompt.service.ts
--   - src/services/profile.service.ts        -- completeness count, deletion
--   - src/services/postDateFeedback.service.ts -- matching-signal sweep
-- A repository-wide search (see this build's report for exactly what was
-- searched) turned up no other live code path reading or writing
-- `questions`/`answers`. Everything that showed up was either already on
-- the typed bank or a historical comment.
--
-- ORDER OF OPERATIONS BELOW:
--   1. Repoint `behavioral_prompt_suggestions.question_id`'s foreign key
--      from `questions(id)` to `question_bank(id)`, this table
--      (003_agent_b.sql, not owned by this build, so altered rather than
--      edited in place per this codebase's own migration convention) is
--      the ONE place a foreign key into the old bank survived outside
--      `answers` itself. `behavioralPrompt.service.ts` and
--      `postDateFeedback.service.ts` now write a `question_bank` id into
--      this column (see their own CUTOVER notes), the constraint has to
--      point at the table that id space now belongs to.
--
--      Every EXISTING row is cleared first. This table only ever holds
--      SKIPPABLE, ephemeral suggestion prompts (never a stored user
--      answer, see behavioralPrompt.service.ts's own rule 1/rule 3), so
--      clearing it loses nothing but a pending nudge the next detection
--      sweep will happily recreate; keeping a row whose `question_id`
--      still pointed at the OLD bank's id space would leave it dangling
--      (satisfying no foreign key at all) the moment the new constraint
--      goes on, which is worse than a clean slate.
--
--   2. Clean up `hard_filters` rows keyed on a bare OLD-bank slug.
--      `filter.service.ts`'s bare-slug resolution path (the read-
--      compatibility shim 019 and filter.service.ts's own file doc
--      describe at length) has been removed in this build, a bare,
--      non-`qb:`-prefixed, non-structured filter key now resolves to
--      NOTHING (see filter.service.ts's updated CANDIDATE ATTRIBUTE
--      SOURCING doc), rather than erroring. Left in place, such a row
--      would silently stop excluding anyone it used to (a behavior
--      change with no error to surface it), which is worse than removing
--      it outright and documenting the removal here. A structured
--      attribute key (age_min/age_max/distance_km/gender_preference/
--      relationship_intention/height_cm/weight_g/body_type) is never
--      touched, those never resolved against the old bank in the first
--      place. This is a DELETE, not a migration to an equivalent `qb:`
--      key, because there is no reliable equivalence to migrate to: the
--      old bank's slug space and the typed bank's slug space were never
--      guaranteed to line up 1:1 (the typed bank was seeded fresh, see
--      008_questions.sql's own migration-choice doc), so silently
--      rewriting `smoking` to `qb:smoking` could just as easily point a
--      user's filter at a DIFFERENT, unintended typed-bank question that
--      happens to share a slug. A user who had a bare-slug filter set
--      before this migration will see it disappear from `GET /me/filters`
--      after upgrading, exactly as if they had disabled it, the
--      documented cleanup this migration's header promises.
--
--   3. Drop `answers` (has the only other foreign key into `questions`),
--      then `questions` itself.
-- =========================================================================

-- ---- 1. Repoint behavioral_prompt_suggestions.question_id -------------

DELETE FROM behavioral_prompt_suggestions;

DO $$
DECLARE
  fk_name text;
BEGIN
  SELECT tc.constraint_name INTO fk_name
  FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu
    ON kcu.constraint_name = tc.constraint_name
   AND kcu.table_schema = tc.table_schema
  WHERE tc.table_schema = current_schema()
    AND tc.table_name = 'behavioral_prompt_suggestions'
    AND tc.constraint_type = 'FOREIGN KEY'
    AND kcu.column_name = 'question_id';

  IF fk_name IS NOT NULL THEN
    EXECUTE format('ALTER TABLE behavioral_prompt_suggestions DROP CONSTRAINT %I', fk_name);
  END IF;
END $$;

ALTER TABLE behavioral_prompt_suggestions
  ADD CONSTRAINT behavioral_prompt_suggestions_question_id_fkey
  FOREIGN KEY (question_id) REFERENCES question_bank (id) ON DELETE CASCADE;

-- ---- 2. hard_filters bare-old-bank-slug cleanup ------------------------

DELETE FROM hard_filters
 WHERE filter_key NOT LIKE 'qb:%'
   AND filter_key NOT IN (
     'age_min', 'age_max', 'distance_km', 'gender_preference',
     'relationship_intention', 'height_cm', 'weight_g', 'body_type'
   );

-- ---- 3. Drop the old bank ----------------------------------------------

DROP TABLE IF EXISTS answers;
DROP TABLE IF EXISTS questions;
