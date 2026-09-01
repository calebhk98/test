# Database normalization audit

**Direct answer:** the schema is in third normal form almost everywhere, and most tables are also in Boyce-Codd normal form (their only candidate keys are the declared primary/unique keys, so no non-key determinant exists). No genuine fourth normal form violation was found: every multivalued relationship (tags, tag intensity, avoid-tags, hard filters, notification preferences, venue staff) is already decomposed one fact per row, keyed correctly.

The exceptions are concentrated in a handful of tables, not spread evenly:

- **`users`** has a real transitive dependency: `trust_level` is computed from `trust_score` (`recalculateTrustScore` in `src/services/trust.service.ts`) and the two are always written together by one code path, so `trust_level` is functionally dependent on `trust_score`, not on `users.id` directly. That is a textbook 3NF violation, kept safe today only because there is a single writer.
- **`users`** also carries `status = 'suspended'` and a separate `suspended` boolean that are meant to always agree (both are set together in `moderation.service.ts` and cleared together in `appeal.service.ts`) but nothing in the schema enforces that. Two independently-writable columns encoding one fact.
- **`post_date_feedback`** has two independent upsert entry points (the legacy `positive` boolean and the newer `outcome` enum) that write different column subsets to the same row via `ON CONFLICT ... DO UPDATE`, with no constraint preventing both from ending up set and disagreeing.
- **`messages.analysis_flags`** is an explicitly self-documented denormalized copy of `message_flags` detail rows.
- A layer of rollup/cache tables (`stats_*`, `compatibility_scores`, `profiles.profile_completeness`, `photo_experiments` counters, `conversations.last_message_at`) is deliberately denormalized for read performance. Most of it is well-behaved; see the denormalization section below for which ones can drift.

No table showed a clean "3NF but not BCNF" case in the classic sense (a non-key attribute determining part of a composite key). The closest thing is the `trust_score` -> `trust_level` dependency above, which is a transitive dependency on the whole table's key, i.e. an ordinary 3NF issue rather than a BCNF-specific one.

## Table-by-table

| Table | NF | Note |
|---|---|---|
| users | 3NF, not strictly | `trust_level` transitively depends on `trust_score`; `status='suspended'`/`suspended` boolean are redundant, kept in sync by convention only |
| user_auth_events | 3NF | append-only log |
| device_fingerprints | 3NF | no code path currently writes `distinct_user_count`/`reputation_score`/`is_vpn`; not linked by FK to `user_auth_events.device_fingerprint` |
| refresh_sessions | 3NF | |
| email_verification_tokens | 3NF | |
| password_reset_tokens | 3NF | |
| user_phones | 3NF | |
| phone_verification_codes | 3NF | `phone_e164` intentionally duplicates `user_phones.phone_e164` as a point-in-time snapshot (documented defense in depth against a race) |
| profiles | 3NF | `profile_completeness` is a derived cache, recomputed and rewritten on every profile update by a single writer |
| user_photos | 3NF, BCNF | |
| photo_experiments | 3NF | `impressions`/`interests_sent`/`interests_accepted` are atomic counters with no source-of-truth event table to reconcile against; retried increments could overcount |
| photo_recommendations | 3NF | `current_position` is a legitimate snapshot of `user_photos.position` at recommendation time |
| interest_tags | 3NF, BCNF | |
| user_tags | 4NF | one row per (user, tag); resolves the multivalued relationship correctly |
| user_tag_intensity | 4NF | |
| user_avoid_tags | 4NF | |
| hard_filters | 3NF | `value` jsonb is opaque per `filter_key`, not queried by internal keys |
| question_bank | 3NF, BCNF | `type_definition` jsonb varies legitimately by `question_type`; `tags` is a plain array used for selector matching, low-cardinality admin data, minor 1NF looseness with low practical risk |
| user_question_answers | 3NF | `question_bank_id` correctly depends on the full (user, slug) key, not slug alone, since it pins a specific answered version |
| question_bank_translations | 3NF | `labels` jsonb is a per-locale override map, read as a whole, not queried by key |
| behavioral_prompt_suggestions | 3NF | `trigger_label` duplicates `interest_tags.name` as static template input, low risk |
| discovery_events | 3NF | `primary_photo_id` is a deliberate historical snapshot of what was shown |
| compatibility_scores | 3NF | materialized pairwise rollup, fully rebuilt by the scheduled refresh job; correct use of denormalization |
| interests | 3NF | status plus four mutually-exclusive nullable `*_at` columns; no CHECK ties the timestamp set to `status` |
| conversations | 3NF | `last_message_at` is updated in the same request path as the triggering message insert |
| messages | 3NF | `analysis_flags` is an explicitly documented denormalized summary of `message_flags`, written once at insert from the same computed flags; can go stale if `message_flags` is later corrected without touching this column |
| message_flags | 3NF, BCNF | source of truth for message-level flags |
| venues | 3NF | `time_slot_config` jsonb is opaque config |
| venue_staff | 3NF, BCNF | |
| admin_users | 3NF, BCNF | |
| date_proposals | 3NF | `policy_snapshot` jsonb is a legitimate opaque snapshot; status plus many nullable `*_at` columns, same unenforced-pairing pattern as `interests` |
| date_attendance_confirmations | 3NF, BCNF | |
| payment_holds | 3NF | same status/timestamp pattern |
| payment_ledger | 3NF | immutable append-only ledger; the venue/user payee exclusivity is enforced by an actual CHECK, a good example of doing this correctly |
| payment_methods | 3NF | `brand`/`last4` are processor-supplied display data, not derivable elsewhere |
| vouchers | 3NF, BCNF | |
| venue_redemptions | 3NF | |
| venue_settlements | 3NF | immutable settlement snapshot; `margin_percent_applied` intentionally freezes `venues.margin_percent` as of settlement time; sum constraint enforced by CHECK |
| post_date_feedback | 3NF, not enforced | two independent `ON CONFLICT` upsert paths (legacy `positive`, new `outcome`/`safety_flag`) can both populate the same row with disagreeing values; nothing constrains them to be consistent |
| post_date_feedback_prompts | 3NF, BCNF | |
| reports | 3NF | |
| blocks | 3NF, BCNF | |
| moderation_actions | 3NF | append-only log |
| automated_moderation_flags | 3NF | append-only log |
| appeals | 3NF | |
| trust_events | 3NF | append-only log; source data that `users.trust_score` is cached from |
| notifications | 3NF | |
| device_tokens | 3NF, BCNF | `device_id` deliberately excluded from the uniqueness key (kept for observability only) |
| notification_preferences | 3NF, BCNF | |
| notification_quiet_hours | 3NF, BCNF | |
| notification_content_preview | 3NF, BCNF | |
| notification_dedup_log | 3NF | `outbox_id` is not an actual FK to `notification_outbox.id`, a referential integrity gap rather than a normalization one |
| notification_outbox | 3NF | `coalesced_count` is a merge counter maintained in place by the enqueue path |
| config_entries | 3NF, BCNF | |
| feature_flags | 3NF | `segments` is a plain text array, small admin config, acceptable 1NF looseness |
| admin_audit_log | 3NF | `before_json`/`after_json` are legitimate opaque audit snapshots |
| user_locale_preferences | 3NF, BCNF | |
| stats_platform_daily | 3NF | rollup, fully overwritten by the aggregation job each run |
| stats_cohort_retention | 3NF | rollup |
| stats_platform_gauges | 3NF, BCNF | rollup |
| stats_aggregation_runs | 3NF | freshness/observability log |
| stats_user_cache | 3NF | cache-aside, recomputed lazily per user |

(`questions`/`answers`, the original 001_init.sql question bank, were fully replaced by `question_bank`/`user_question_answers` in migration 008 and dropped outright in migration 022 once every reader was repointed; no duplication survives between the two systems in the current schema.)

## Deliberate denormalization and drift risk

- **`users.trust_score`/`trust_level`**: cached rollup of `trust_events.delta`, recomputed by `recalculateTrustScore` (§25.6 batch job) and written atomically together. Justified: computing a running sum on every trust check would be expensive. Drift risk is low and bounded: a user's score is only stale between a new `trust_events` row and the next recompute sweep, not silently wrong forever.
- **`profiles.profile_completeness`**: recomputed and rewritten on every profile update by a single writer (`profile.service.ts`). Low drift risk.
- **`conversations.last_message_at`**: updated in the same code path as the message insert. Low drift risk, but there is no DB constraint forcing every message-insert path to do this, so a future bypass would silently desync ordering.
- **`messages.analysis_flags`** vs **`message_flags`**: both written from the same computed value at insert time, but nothing keeps them in sync afterward. If `message_flags` is ever corrected (e.g. an admin clears a false positive), `analysis_flags` will not reflect it. Moderate risk since it feeds moderation-facing summaries.
- **`photo_experiments`** counters: pure atomic increments with no underlying event table to reconcile against. A retried request could double-count an impression or accept, which would feed directly into the A/B photo-ranking decision. This is the counter most likely to silently disagree with reality, because there is nothing to compare it against.
- **`compatibility_scores`** and the **`stats_*`** family: read-heavy rollups, fully rebuilt on a schedule (migrations 018 and 020). This is the correct engineering tradeoff, not a design flaw; staleness is bounded and, for stats, explicitly surfaced via `stats_aggregation_runs`.
- **`venue_settlements`**: an immutable historical snapshot of `venues.margin_percent`, with the payout arithmetic enforced by a database CHECK. This is denormalization done right.
- **`device_fingerprints`**: not a drift risk today only because nothing populates it; the aggregate columns exist in the schema with no live writer, which is a different problem (unfinished feature) worth noting to whoever picks it up.

## Worth changing, ranked by real corruption risk

1. **`post_date_feedback`**: add a CHECK (or merge the two submission paths) so `positive` and `outcome` cannot both be set with contradictory meaning. Right now a user can legitimately trigger both upserts and end up with a row that says two different things about the same date.
2. **`users.status`/`suspended`**: either drop the boolean and derive it from `status`, or add `CHECK ((status = 'suspended') = suspended)`. Two independently-writable columns encoding one fact is exactly the setup that produces a user who is suspended by one check and not by the other.
3. **`users.trust_level`**: either make it a generated column derived from `trust_score`, or stop storing it and compute it at read time. It is presently safe only because one function is disciplined about writing both together.
4. **`interests`/`date_proposals`/`payment_holds`**: the status-plus-nullable-timestamps pattern (four to seven columns per table) has no CHECK tying the populated timestamp to the current status. Not urgent, but a single stray UPDATE could leave `status='pending'` with `accepted_at` set and nothing would catch it.
5. **`notification_dedup_log.outbox_id`**: add the missing foreign key to `notification_outbox(id)`. Cheap fix, closes a real integrity gap.
