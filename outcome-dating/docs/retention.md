# Data retention

This document is the privacy-review-facing table: every data class this
backend accumulates, how long it lives, what happens to it at the end of
that window, and why. It is implemented by
[`src/services/retention.service.ts`](../src/services/retention.service.ts)
(the policy registry + batched enforcement engine) and run on a schedule by
[`src/jobs/retention.job.ts`](../src/jobs/retention.job.ts) (registered in
`src/jobs/registry.ts`, hourly). `tests/unit/retention.test.ts` asserts
this table's policy count matches the code's, so the two cannot silently
drift apart.

## Why this exists

Before this build, nothing in the schema expired: `messages`,
`discovery_events`, `user_auth_events`, `notifications`, `message_flags`,
and every analytics table grew forever — a growing storage cost, and for
sensitive-category data (raw IP/device signals, chat content, one-time
auth codes), a legal exposure in jurisdictions with a data-minimization
requirement (e.g. GDPR Art. 5(1)(e) "storage limitation").

## How to read the table

- **Action** — `delete` (the row is removed outright) or `anonymize` (the
  row/aggregate stays, its identifying payload is cleared).
- **Window** — how long after the "clock" column a row becomes eligible.
- **Batching** — every policy deletes/anonymizes `batchSize` rows per SQL
  statement, up to `maxBatchesPerRun` statements per scheduled run (see
  "Batching and idempotency" below) — this column states each policy's
  configured values so an operator can predict a run's maximum footprint.

## Enforced policies

| Data class | Table(s) | Clock column | Window | Action | Batching (size × cap/run) | Reasoning |
|---|---|---|---|---|---|---|
| Expired email-verification tokens | `email_verification_tokens` | `expires_at` | 7 days | delete | 500 × 50 | One-time token, worthless past expiry. The buffer is for support debugging only. |
| Expired password-reset tokens | `password_reset_tokens` | `expires_at` | 7 days | delete | 500 × 50 | Same as above. |
| Expired phone-verification codes | `phone_verification_codes` | `expires_at` | 7 days | delete | 500 × 50 | Same as above — plus these carry a phone number, so the sensitivity argument for a short window is stronger than the other two. |
| Raw login events (IP + device fingerprint per login) | `user_auth_events` | `login_at` | 90 days | delete | 500 × 50 | Raw device/IP signal — the task brief's explicit "should expire quickly" example. Anything durable it should feed (trust score, a moderation flag) is already written to `trust_events`/`automated_moderation_flags`, both retained forever (see below), by the time this window closes. |
| Revoked or expired refresh-token sessions | `refresh_sessions` | `revoked_at` / `expires_at` | 30 days | delete | 500 × 50 | Inert the moment either condition holds; the 30-day tail is a security-incident-investigation buffer, not a functional need. |
| Discovery-grid impressions | `discovery_events` | `created_at` | 30 days | delete | 500 × 50 | Pure impression log, high volume, near-zero standalone value past the short window the "recently viewed" style features that read it actually need. |
| Per-message automated regex flags | `message_flags` | `created_at` | 180 days | delete | 500 × 50 | Granular per-message evidence; `messages.analysis_flags` already carries a denormalized summary on the message row itself, so the detail rows are redundant past this window. The safety *decision* trail (below) is untouched. |
| Notification idempotency keys | `notification_dedup_log` | `created_at` | 30 days | delete | 500 × 50 | Exists solely to guard against double-enqueuing a retried operation; useful life is on the order of the outbox's own retry horizon, not months. |
| Delivered/dead/dropped push+email outbox rows | `notification_outbox` (status ∈ `sent`, `dead`, `dropped_preference`, `dropped_no_target`, `dropped_rate_limited`) | `created_at` | 30 days | delete | 500 × 50 | Delivery-pipeline exhaust once terminal; `queued`/`held_quiet_hours`/`failed_retryable` rows are still live work and are never touched. |
| In-app notification-center entries, once delivered | `notifications` (status ≠ `pending`) | `created_at` | 90 days | delete | 500 × 50 | User-visible history (unlike the pipeline tables above), hence the longer window; `pending` rows are never touched regardless of age. |
| Device-fingerprint raw signal payload, for dormant devices | `device_fingerprints` | `last_seen_at` | 180 days | **anonymize** | 500 × 50 | An aggregate reputation record shared across every account that used that device — deleting it would erase abuse-pattern memory a still-active bad device deserves to keep. Only the free-form `metadata` jsonb (the raw payload) is cleared; `reputation_score`/`is_vpn`/`is_emulator` (already-derived classification, not raw identifying data) are kept. |
| Message bodies in long-archived (dormant) conversations | `messages` (via `conversations.status = 'archived'`) | `conversations.archived_at` | 730 days | **anonymize** | 200 × 50 | Messages are core relationship content a still-active pair reasonably expects to keep — nothing here touches an `active`/`cooling`/`established` conversation, ever. Only conversations already dormant for two full years get their bodies overwritten with the exact same placeholder `profile.service.ts#deleteMyAccount` already uses for a deleted user's own messages — same "erase content, keep the row" policy, applied on an age trigger instead of a delete-my-account trigger. See caveat below. |

## Retained forever (never touched by any policy)

Repeats — does not re-decide — the exact boundary
[`profile.service.ts#deleteMyAccount`](../src/services/profile.service.ts)
already draws for account deletion (see that function's own doc), so
self-deleting an account and simply waiting out a retention window can
never launder the same data two different ways.

| Data class | Table(s) | Reasoning |
|---|---|---|
| Financial / ledger | `payment_holds`, `payment_ledger` | Tax/dispute/audit obligations outlive the account in most jurisdictions; `payment_ledger` is additionally an append-only immutable ledger by schema design (insert-only, `db/migrations/001_init.sql`). |
| Safety audit trail | `reports`, `moderation_actions`, `trust_events`, `appeals`, `automated_moderation_flags` | Deleting a user's own history here on any timer would let a suspended/banned user launder their record by simply staying quiet long enough to age it out — the exact ban-evasion hole `deleteMyAccount`'s own doc names. `message_flags` (above) gets a window precisely *because* it's the granular signal these five (the decision trail) already summarize — deleting the detail loses nothing the decision trail depends on. |
| Admin action log | `admin_audit_log` | Not the safety trail proper, but the same accountability reasoning one level up: an admin-action log that could be aged out would undermine the auditability it exists to provide. |

## Explicitly out of scope (not a "should be forever", just not this pass)

| Data class | Table(s) | Reasoning |
|---|---|---|
| Photo A/B test aggregates | `photo_experiments`, `photo_recommendations` | Bounded aggregates — one row per (user, photo), not one row per event — that already cascade-delete the moment the photo they reference is removed (`user_photos ... ON DELETE CASCADE`). No independent unbounded-growth problem to solve. |
| Compatibility scores | `compatibility_scores` | Also a bounded, continuously-upserted aggregate (`compatibilityRefresh.job.ts`), and actively owned by a concurrent build cutting the compatibility system over. Left alone to avoid two automated jobs racing each other on the same table mid-cutover. |
| Question bank + answers | `question_bank`, `user_question_answers`, everything under `src/domain/questions/**` | The in-flight typed-question-bank cutover this build is careful not to touch (see `src/domain/i18n/questionLocalization.ts`'s own doc). |
| Core per-user profile data | `users`, `profiles`, `answers` (old bank), `user_tags`, `hard_filters`, `user_photos` | Already governed by the account-deletion boundary on a USER-ACTION trigger, not an age trigger — bounded per-user data (roughly one row per user×question), not the "accumulates forever" log/event problem this pass targets. |

## Batching and idempotency

Every policy runs as a loop of small, independent SQL statements — never
one table-wide `DELETE`:

```sql
WITH victims AS (
  SELECT id FROM <table> WHERE <age column> < $cutoff ORDER BY <age column> LIMIT $batchSize
)
DELETE FROM <table> WHERE id IN (SELECT id FROM victims);
```

Each batch is its own short statement (default 500 rows, 200 for the
`messages` join-based policy), so its lock footprint is small and brief
regardless of how large the table has grown. A policy stops once it has
run `maxBatchesPerRun` batches in one scheduled tick (default 50, i.e. a
25,000-row cap per policy per run at the default batch size) — a huge
backlog is worked down over several scheduled runs rather than one run
trying to do it all and blocking everything else.

`ctx.clock` supplies "now" for the cutoff on every run — never
`Date.now()` — so `tests/unit/retention.test.ts` moves a `ManualClock`
to a window boundary instead of waiting on real time, and can assert a
row expires exactly at its boundary and not one tick before.

**Idempotent by construction, not by a separate "already ran" log**: a
batch's `WHERE` clause only ever matches rows that still satisfy the
policy's condition. Running a policy a second time (same or later clock)
against a database it already fully processed matches zero rows in its
first batch and returns immediately — there is nothing to double-delete
or double-anonymize, so no run-tracking table is needed for correctness.

## Caveat: dormant-chat-content anonymization vs. re-matching

`conversation.service.ts` allows a brand-new mutual match between the
same two users to resurrect an `archived` conversation (`status ->
'active'`, `archived_at -> NULL`). If that happens more than two years
after the conversation was archived, the resurrected thread's older
messages will already read as the placeholder text (their bodies were
anonymized by the `dormant_chat_content` policy before the resurrection).
This is the same visual result a user already sees today when the *other*
participant in a conversation has deleted their account — not a new class
of surprise this build introduces, but worth naming explicitly for a
privacy review: the tradeoff was accepted deliberately (bounding chat
content retention) rather than left as an unexamined side effect.

## Running it

`retentionSweepJob` (`src/jobs/registry.ts`) runs hourly wherever
`JobScheduler#start` runs every job. It can also be invoked directly —
`runRetentionSweep(ctx)` for every policy in one call, or
`runRetentionPolicy(ctx, name)` to exercise a single policy — both
exported from `src/services/retention.service.ts`.
