# Conformance checklist

**Read this first, then decide whether to keep reading.** This is a 411-row, spec-section-by-spec-section obligation checklist derived from `SPEC.md` (`C-<section>.<n>` IDs), each row naming the exact test type and oracle a test should be checked against, plus a "Definition of Done" coverage map at the end tying the spec's 20 top-level DoD items back to specific rows. It is not a defect list and not a status report: it doesn't say whether a row currently has a test, only what a correct test for that row would assert. For which rows actually have tests today and how strong they are, read `docs/test-audit.md` instead. Use this document when writing a new test and wanting to know what "done" looks like, or when checking whether a spec rule has a test at all.

This is a machine-checkable test plan derived from `SPEC.md` v1.0 (§1 to §34). It contains
no test code and no product code, it is the ground-truth obligation list another agent
implements `tests/**` from.

## How to read this document

- **ID scheme**: `C-<spec section>.<sequence>`. IDs are stable, do not renumber once
  another agent has started writing tests against them. State-machine transition rows use
  `C-<section>.SM.L<n>` (legal) / `C-<section>.SM.I<n>` (illegal).
- **MUST/SHOULD/MAY** column: copied from the spec's own normative word for that sentence
  (§0 preamble: MUST = mandatory, SHOULD = recommended unless a documented constraint
  applies, MAY = optional/configurable). Where a row paraphrases several spec sentences,
  the strongest verb used governs.
- **Test type**: `unit` (pure function, no DB), `integration` (DB + service, real
  transaction), `state-machine` (transition legality), `property` (holds over many
  generated inputs, see `test-strategy.md` for what "property" means without
  `fast-check`), `negative` (asserts an action is rejected / a thing does NOT happen),
  `fixture-data` (schema/enum/config shape assertion, no business logic).
- **Oracle**: the exact observable result that proves the row. Where the spec gives a
  formula but not a worked answer, arithmetic is worked out by hand in
  [§16.2](#c-162-compatibility-score-formula-worked-examples), [§6.1](#c-61-trust-score-bands),
  [§14.7](#c-147-cancellation-and-refunds-worked-examples), [§18.5](#c-185-report-scoring),
  and [§21.4](#c-214-config-variables-defaults-table) so the test author has ground truth,
  not a re-derivation task.
- Grounding note: where useful, oracles reference the actual stub contracts already in
  `src/` (e.g. `FakeProcessor`'s magic-substring failure injection, `ManualClock`, the
  `ConfigKeyRegistry` defaults, `StubMediaModerationAdapter`'s URL-substring triggers,
  DB `CHECK`/`UNIQUE` constraints in `db/migrations/001_init.sql`) since those are the
  real seams the test suite will drive through. This document does not modify any of
  those files.

---

# §1 Product Overview

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-1.1 | §1 | Users answer structured compatibility questions (dual 5-point scale, not free text). | MUST | integration | `PUT /me/answers` persists `(userId, questionId) -> {selfValue, partnerValue}` rows; see §8 for detail. |
| C-1.2 | §1 | Hard filters are strictly enforced. | MUST | integration | Same test as C-9.1.1. |
| C-1.3 | §1 | The algorithm sorts candidates only; it does not override filters. | MUST | negative | Same test as C-9.1.2 / C-16.1.1. |
| C-1.4 | §1 | Users do not mass-swipe: discovery is browse + limited match requests, not unlimited swipe actions. | MUST | negative | No "swipe" endpoint exists; `POST /interests` is rate-limited per C-11.2.*. |
| C-1.5 | §1 | Mutual match unlocks chat. | MUST | state-machine | Same test as C-12.1.1. |
| C-1.6 | §1 | Users can propose structured dates. | MUST | integration | Same test as C-13.1.1. |
| C-1.7 | §1 | Date acceptance triggers refundable escrow holds. | MUST | integration | Same test as C-14.2.2. |
| C-1.8 | §1 | Date completion is verified through venue redemption or structured post-date feedback (no-scan fallback). | MUST | state-machine | Same test as C-15.3.3 / C-15.4.1. |
| C-1.9 | §1 | The app does not use generative LLM text to write to users. | MUST | negative | Same test as C-20.0.1 / C-12.4.2. |
| C-1.10 | §1 | The app uses static UI copy, structured prompts, regex-based text analysis, and automated moderation (not free-form NLP). | MUST | fixture-data | Every `Notification.templateKey` maps to a static string table with no interpolated free-form LLM output; `textscan.service.ts` output is `TextScanResult` built only from regex/keyword matches. |
| C-1.11 | §1 | The app MUST NOT require mandatory government ID verification. | MUST NOT | negative | Same test as C-5.3.1. |
| C-1.12 | §1 | The app MUST NOT require mandatory phone-number verification. | MUST NOT | negative | Same test as C-5.2.1. |
| C-1.13 | §1 | The app MUST NOT implement social vouching. | MUST NOT | negative | No API surface accepts "vouch for user X"; `TrustEvent.eventType` catalog contains no vouching-type event; §5.4/§6.2 factor lists contain no vouching factor. |
| C-1.14 | §1 | The app MUST NOT implement profile boosts. | MUST NOT | negative | No `POST` endpoint purchases or applies a visibility boost; `DiscoveryCandidate` sort key is `compatibilityScore` + the fixed tie-breaker chain only (C-10.3.*), never a purchasable multiplier. |
| C-1.15 | §1 | The app MUST NOT implement pay-to-win visibility. | MUST NOT | negative | Discovery ordering is provably independent of `payment_methods`/ledger state for any two otherwise-identical candidates (property test: swap payment-method presence, sort order unchanged). |
| C-1.16 | §1 | The app MUST NOT allow unlimited low-effort liking. | MUST NOT | negative | Same test as C-11.2.1 to C-11.2.4 (outgoing/daily interest caps enforced, return 429/`rate_limited`). |
| C-1.17 | §1 | The app MUST NOT have hidden filter behavior. | MUST NOT | negative | Same test as C-10.3.4 (no compatibility-threshold hides a candidate who passes hard filters) and C-9.1.2. |
| C-1.18 | §1 | The app MUST NOT depend on human moderation as a core dependency. | MUST NOT | negative | Same test as C-18.1.1. |

# §2 Core User Flow

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-2.1 | §2 | The full happy-path loop (register → answer questions → set filters → browse → send interest → mutual accept → chat → propose date → both holds authorized → capture → ticket → venue redemption → post-date feedback → established chat) completes end-to-end with no manual/human step. | MUST | integration | One long-form integration test drives all 12 steps via the service layer against a real (test) Postgres DB and the `FakeProcessor`; asserts final state `conversation.status === 'established'`, `dateProposal.status === 'completed'`, `voucher.status === 'redeemed'`, and a balanced ledger (C-CC.4). |

# §3 Non-Goals for MVP

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-3.1 | §3.1 | No generative AI text anywhere in the MVP. | MUST NOT | negative | Same test as C-20.0.1. |
| C-3.2 | §3.2 | No video calling. | MUST NOT | negative | No route under §24 initiates a video/WebRTC session; `domain/types.ts` has no call/session type. |
| C-3.3 | §3.3 | No live streaming. | MUST NOT | negative | Same as C-3.2 (no live-stream route/type). |
| C-3.4 | §3.4 | No social feed. | MUST NOT | negative | No route returns a cross-user activity feed; `discovery_events` are private per-viewer, never a public feed. |
| C-3.5 | §3.5 | No public like counts. | MUST NOT | negative | Same test as C-10.1.4. |
| C-3.6 | §3.6 | No profile boosts. | MUST NOT | negative | Same test as C-1.14. |
| C-3.7 | §3.7 | No unlimited likes. | MUST NOT | negative | Same test as C-1.16. |
| C-3.8 | §3.8 | No human moderation queues required for the app to operate. | MUST NOT | negative | Same test as C-18.1.1. |
| C-3.9 | §3.9 | No mandatory government ID. | MUST NOT | negative | Same test as C-5.3.1. |
| C-3.10 | §3.10 | No mandatory phone verification. | MUST NOT | negative | Same test as C-5.2.1. |
| C-3.11 | §3.11 | No in-app payments for subscriptions (only the date-escrow payment flow exists). | MUST NOT | negative | No route/config key represents a subscription product; `payment_ledger.type` enum (§14.8) has no `subscription` type. |
| C-3.12 | §3.12 | Milestone bounty verification is absent unless explicitly added behind a feature flag in a later phase. | MUST NOT (unless flagged) | negative | `KNOWN_FLAGS.MILESTONE_BOUNTIES` exists but defaults `enabled:false, rollout_percent:0` (seeded by `seedKnownFlags`); with the flag off, no bounty-verification code path is reachable. |

# §4 User Roles

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-4.1.1 | §4.1 | A regular user can perform every listed action (account, answers, filters, browse, interests, chat post-match, propose/accept dates, report/block, view trust). | MUST | integration | Each action's own dedicated row elsewhere in this document (§5, §8, §9, §10, §11, §12, §13, §18.3, §6.3) collectively proves this; no separate row needed beyond the RBAC negative below. |
| C-4.2.1 | §4.2 | Venue staff can view upcoming vouchers for their venue. | MUST | integration | `GET` on a venue-staff voucher list (implementation detail of `/venue/*`) returns vouchers where `venue_id` matches the staff member's assigned venue only. |
| C-4.2.2 | §4.2 | Venue staff can scan/redeem vouchers. | MUST | integration | Same test as C-15.3.1. |
| C-4.2.3 | §4.2 | Venue staff can mark dates completed (via redemption). | MUST | integration | Same test as C-15.3.3. |
| C-4.2.4 | §4.2 | Venue staff MUST NOT see user chats. | MUST NOT | negative | A venue-staff-authenticated request to any `/conversations/*` or `/conversations/*/messages` route returns 403 `forbidden`. |
| C-4.2.5 | §4.2 | Venue staff MUST NOT see user emails. | MUST NOT | negative | The voucher/redemption payload returned to venue staff contains `user names` only (per §15.1), never `email`; property test asserts no response field on any venue-staff-reachable route matches `/email/i` key name carrying a real address. |
| C-4.2.6 | §4.2 | Venue staff MUST NOT see payment card details. | MUST NOT | negative | Same test as C-28.4.1, additionally scoped to venue-staff role: no venue-staff-reachable route returns `payment_methods`/`payment_holds` rows at all. |
| C-4.3.1 | §4.3 | Admin can edit configuration variables. | MUST | integration | `PATCH /admin/config` as admin succeeds and is reflected by `ConfigService.get`. |
| C-4.3.2 | §4.3 | Admin can manage questions. | MUST | integration | `POST /admin/questions`, `PATCH /admin/questions/{id}` as admin succeed. |
| C-4.3.3 | §4.3 | Admin can manage venues. | MUST | integration | `POST /admin/venues`, `GET /admin/venues` as admin succeed. |
| C-4.3.4 | §4.3 | Admin can view analytics. | MUST | integration | `GET /admin/analytics/overview` as admin returns the §26 metric set. |
| C-4.3.5 | §4.3 | Admin can review automated moderation actions. | MUST | integration | `GET /admin/moderation/actions` as admin lists `moderation_actions` rows. |
| C-4.3.6 | §4.3 | Admin can override payment disputes only where legally necessary. | MAY (constrained) | integration | An admin-only dispute-override path exists and is logged (C-28.6.1); regular users cannot reach it (403). |
| C-4.3.7 | §4.3 | Admin should not be required for normal moderation; the system must assume zero human moderators. | MUST | negative | Same test as C-18.1.1: the full moderation pipeline (report → score → automated action) runs to completion in an integration test where no admin endpoint is ever called. |
| C-4.RBAC.1 | §4 | A regular user calling any `/admin/*` route is rejected. | MUST | negative | 403 `forbidden` for every `/admin/*` route when caller role ≠ admin. |
| C-4.RBAC.2 | §4 | A regular user calling `/venue/redeem` or other venue-staff routes is rejected. | MUST | negative | 403 `forbidden` when caller is not an active `venue_staff` row for that venue. |

# §5 Account Creation and Verification

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-5.1.1 | §5.1 | Signup MUST require email. | MUST | negative | `POST /auth/register` without `email` → 400 `validation_error`. |
| C-5.1.2 | §5.1 | Signup MUST require password. | MUST | negative | Missing `password` → 400 `validation_error`. |
| C-5.1.3 | §5.1 | Signup MUST require date of birth. | MUST | negative | Missing `birthdate` → 400 `validation_error`. |
| C-5.1.4 | §5.1 | Signup MUST require acceptance of terms. | MUST | negative | `termsAccepted !== true` → 400 `validation_error`. |
| C-5.1.5 | §5.1 | Signup MUST require location permission or a manually entered city. | MUST | negative | Neither `locationPermission` nor `city` supplied → 400 `validation_error`. |
| C-5.1.6 | §5.1 | User MUST be at least 18 years old; age is computed from birthdate. | MUST | unit + negative | `birthdate` = today − 18y exactly → **accepted**; `birthdate` = today − 18y + 1 day (i.e. 17y 364d) → **rejected**, 400. DB-level backstop: `users_min_age CHECK (birthdate <= CURRENT_DATE - INTERVAL '18 years')` (`db/migrations/001_init.sql`), an INSERT bypassing the service layer with a 17-year-old birthdate must raise a Postgres check-violation. |
| C-5.1.7 | §5.1 | Duplicate email is rejected. | MUST (implied by `UNIQUE` constraint) | negative | Second `POST /auth/register` with an already-registered email → 409 `conflict` (maps from the `users.email UNIQUE` violation). |
| C-5.2.1 | §5.2 | Phone number is NOT required at any point in registration or later gating. | MUST NOT require | negative | Registration succeeds with no phone field in the payload at all; no later endpoint 403s for lack of a verified phone. |
| C-5.3.1 | §5.3 | Government ID is NOT required at any point. | MUST NOT require | negative | Registration and full onboarding succeed with no government-ID upload; no discovery/interest/date endpoint gates on an ID-verification flag. |
| C-5.4.1 | §5.4 | Verified email is an available trust signal. | SHOULD | integration | `user.emailVerifiedAt` set → positive `TrustEvent` (`event_type` reflecting email verification) with `delta > 0`. |
| C-5.4.2 | §5.4 | Verified payment method is an available trust signal. | SHOULD | integration | Adding a `payment_methods` row with `verifiedAt` set → positive trust event. |
| C-5.4.3 | §5.4 | Device reputation is an available trust signal. | SHOULD | integration | `device_fingerprints.reputation_score` feeds trust recalculation (§25.6). |
| C-5.4.4 | §5.4 | Behavioral consistency is an available trust signal. | SHOULD | integration | Consistent login device/IP over time contributes a positive trust factor (vs. C-6.2.neg.* below). |
| C-5.4.5 | §5.4 | Optional selfie liveness check is available and MAY be used, e.g. in appeals. | MAY | integration | Same appeal-method test as C-18.6.1. |
| C-5.4.6 | §5.4 | Optional connected accounts (Spotify/Strava) are opt-in only, never required. | MAY | negative | No endpoint gates on a connected-account being present; connecting one is a distinct opt-in action the user can decline entirely. |
| C-5.4.7 | §5.4 | No vouching system exists. | MUST NOT | negative | Same test as C-1.13. |

# §6 Trust System

## C-6.1 Trust score bands

Worked ground truth for `trustScore -> trustLevel`, using the code-level defaults
(`config.service.ts`: `trust.level_standard_min=40`, `trust.level_trusted_min=70`,
`trust.level_elite_min=90`), which match the §6.1 table exactly:

| trustScore | Expected trustLevel |
|---:|---|
| 0 | limited |
| 39 | limited |
| 40 | standard |
| 69 | standard |
| 70 | trusted |
| 89 | trusted |
| 90 | elite |
| 100 | elite |

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-6.1.1 | §6.1 | `trustScore` is stored/represented as an integer 0 to 100. | MUST | unit | Same DB constraint as `users.trust_score CHECK (trust_score BETWEEN 0 AND 100)`; a compute path that would produce <0 or >100 is clamped before persist. |
| C-6.1.2 | §6.1 | trustScore→trustLevel mapping matches the table above at every boundary (39/40, 69/70, 89/90) plus the extremes (0, 100). | MUST | unit + property | All 8 rows of the worked table above pass; property test over `trustScore ∈ [0,100]` asserts the mapping is monotonic non-decreasing and has exactly 3 breakpoints at 40/70/90. |
| C-6.1.3 | §6.1 | The exact numeric trustScore is NOT shown to the user unless product explicitly decides otherwise (default: level only). | SHOULD | integration | Default config: `GET /me/trust` response's primary display field is `trustLevel`; `trustScore` presence is gated by an explicit flag/config (default off), see Open Question OQ-7. |
| C-6.2.1 | §6.2 | Each listed positive factor (verified email, verified payment, completed profile, completed dates, positive post-date feedback, account age, low report rate, normal message velocity, consistent location/device) produces a trust event with `delta > 0` when it occurs. | MUST | integration | For each of the 9 factors, trigger the underlying event and assert a `trust_events` row with positive `delta` is written (§25.6 recalculation triggers: report, date completed, payment failure, profile change, verification change). |
| C-6.2.2 | §6.2 | Each listed negative factor (reports, no-shows, spam-like messages, off-platform-solicitation patterns, fake-looking photos, rapid account creation, suspicious device/IP, payment failures/chargebacks) produces a trust event with `delta < 0`. | MUST | integration | For each of the 8 factors, trigger the underlying event and assert a `trust_events` row with negative `delta`. |
| C-6.3.1 | §6.3 | Users MUST be able to see why their trust level is limited (actionable items). | MUST | integration | `GET /me/trust` for a Limited-level user returns a non-empty `actionableImprovements: string[]`. |
| C-6.3.2 | §6.3 | The exact trust-score formula/weights MUST NOT be exposed. | MUST NOT | negative | `TrustSummary` response never includes per-factor numeric weights or the raw event→delta mapping; only static template strings (e.g. "Add a clear face photo") and counts. |
| C-6.3.3 | §6.3 | Recent negative events are shown as plain, non-technical bullet text. | SHOULD | fixture-data | `recentNegativeEvents` entries match the static template catalog (e.g. `"1 missed date"`, `"1 report for spam-like messaging"`), never a raw `event_type` enum string or internal id. |
| C-6.4.1 | §6.4 | Limited users: "Send interests" is restricted (not full access). | MUST | integration | A Limited-trust user's effective outgoing-interest cap is lower than a Standard user's (config-driven; see Open Question OQ-4 re: exact numeric definition of "limited"). |
| C-6.4.2 | §6.4 | Limited users: sending links in chat is disabled entirely ("no"). | MUST | negative | A Limited-trust user's message containing a URL is flagged `link`, and the link renders non-clickable regardless of hour count (0 links/hour, `chat.max_links_per_hour_low_trust=0`). |
| C-6.4.3 | §6.4 | Standard users: links are allowed but show a warning ("warning only"). | MUST | integration | A Standard-trust user's message containing a link from an unknown domain renders with a warning banner (§19.4) but is not blocked. |
| C-6.4.4 | §6.4 | Trusted/Elite users: links are fully allowed. | MUST | integration | No warning/velocity gate blocks a Trusted or Elite user's link beyond the shared `chat.max_links_per_hour_standard_trust=5` rate. |
| C-6.4.5 | §6.4 | Limited users: date proposals require a verified payment method. | MUST | negative | A Limited-trust user with no verified payment method attempting `POST /conversations/{id}/date-proposals` → rejected (payment-method-required error), not merely a later payment failure. |
| C-6.4.6 | §6.4 | Standard/Trusted/Elite users: date proposals do not require pre-verification beyond having a usable payment method at authorization time. | MUST | integration | Same proposal succeeds for a Standard user without a pre-verified (but present) payment method. |
| C-6.4.7 | §6.4 | Browse grid and Chat are available to all four trust levels (Limited included). | MUST | integration | Discovery and chat-send succeed for a Limited-trust user (absent other restrictions like shadowban). |

# §7 Profile System

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-7.1.1 | §7.1 | Profile schema includes all 12 listed fields (display name, age, city/approx location, photos, bio, structured prompts, interest tags, private tags, lifestyle attributes, relationship intentions, trust level, completeness score). | MUST | fixture-data | `Profile`/`UserPhoto`/`UserTag` shapes in `domain/types.ts` collectively carry every field; a profile-read endpoint returns all of them. |
| C-7.1.2 | §7.1 | Exact location MUST NOT be shown to other users; only approximate distance. | MUST NOT | negative | Same test as C-28.5.1 (cross-cutting invariant CC-3). |
| C-7.2.1 | §7.2 | At least one photo is required before discovery visibility. | MUST | negative | A profile with zero photos is excluded from `GET /discovery` results and from `discoverable` visibility checks (C-10.2.4). |
| C-7.2.2 | §7.2 | The first (primary) photo must contain a visible face, detected by CV. | MUST | integration | Using `StubMediaModerationAdapter`: `imageUrl` containing `"noface"` uploaded as primary → `analyzePhoto` returns `faceDetected:false`, `rejectionReasons` includes `"primary_photo_missing_face"`, `moderationStatus:'rejected'`; `user_photos.moderation_status='rejected'`, photo does not count toward "has ≥1 approved photo" for discovery eligibility. |
| C-7.2.3 | §7.2 | Nudity, weapons, and known illegal imagery MUST be automatically blocked. | MUST | negative | `"nsfw"` in URL → `nudityDetected:true`, `moderationStatus:'rejected'`. `"weapon"` → `weaponsDetected:true`, `'rejected'`. `"illegal"` → `illegalContentDetected:true`, `'rejected'`. All three: no human review step required for the rejection to take effect. |
| C-7.2.4 | §7.2 | Duplicate or known-scam images SHOULD be flagged via perceptual hash matching. | SHOULD | integration | Two photos uploaded (by different users) with `imageUrl` containing the same `"dup:<n>"` token produce the same `perceptualHash`; `photo.service.ts` cross-user hash lookup flags the second upload (`moderationStatus:'flagged'` or a `message_flags`-equivalent signal, see §18.2). |
| C-7.2.5 | §7.2 | No human moderation step is required for any photo decision. | MUST NOT depend on human | negative | Same test as C-18.1.1, scoped to photos: every `PhotoAnalysisResult.moderationStatus` is derived purely from `StubMediaModerationAdapter` output, no `admin_review_pending` gate exists in the photo pipeline. |
| C-7.3.1 | §7.3 | The app MUST NOT rely only on generic photo advice. | MUST NOT | negative | No static "photo tips" copy is the *only* mechanism; the A/B pipeline (below) exists and is reachable once a user has ≥3 photos. |
| C-7.3.2 | §7.3 | With ≥3 photos, the app MAY run an A/B test showing different viewers different primary photos. | MAY | integration | With `KNOWN_FLAGS.PHOTO_AB_TESTING` enabled for a user with 3 photos, `discovery_events` for that candidate record varying `primary_photo_id` across different viewers. |
| C-7.3.3 | §7.3 | The app records impressions, profile views, interests sent, interests accepted per photo. | MUST | integration | `photo_experiments` row for each photo accumulates all 4 counters correctly as the corresponding events occur. |
| C-7.3.4 | §7.3 | The primary success metric is accepted interests, not raw profile views. | MUST | unit | The photo-ranking function (§25.5) sorts/recommends by `interestsAccepted` (or an accepted-rate normalized by impressions), never by `impressions` alone; a fixture where photo A has more views but fewer accepted interests than photo B ranks B higher. |
| C-7.3.5 | §7.3 | After enough data, the app recommends or auto-reorders photos, with an example lift percentage shown. | SHOULD | integration | `PhotoRecommendation.acceptedInterestLiftPercent` is computed from real counters (e.g. photo A: 10/50 accepted-rate vs photo B: 14/50 → **lift = (14/50 − 10/50)/(10/50) = 40%**, not the spec's illustrative "42%", the illustrative figure in §7.3 is scaffolding text only, not a fixed target). |
| C-7.3.6 | §7.3 | The user should be able to approve or reject the recommendation, unless product decides on automatic reordering. | SHOULD | integration | Default (no override config): recommendation is surfaced via `GET /me/photo-test-results` and requires an explicit approve action before `position`/`is_primary` changes; an "auto-reorder" mode is only active when a config/flag explicitly opts in. |

# §8 Compatibility Questions

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-8.1.1 | §8.1 | Every question has both a self answer and a partner answer. | MUST | fixture-data | `answers` schema/`Answer` type carries both `selfValue` and `partnerValue` per `(userId, questionId)`. |
| C-8.1.2 | §8.1 | All answers use a 5-point scale (1 to 5). | MUST | negative | `PUT /me/answers` with `selfValue: 6` or `0` → 400 `validation_error`; DB `CHECK (self_value BETWEEN 1 AND 5)` / same for `partner_value` is the backstop. |
| C-8.2.1 | §8.2 | Question metadata carries all 12 listed fields (id, slug, category, text, 4 labels, weight, polarity, sensitivity, private-visibility option, active flag). | MUST | fixture-data | `Question` type / `questions` table carry every field; `GET /questions` returns them. |
| C-8.3.1 | §8.3 | The app MAY observe behavior and suggest a question, but MUST NOT assume/auto-fill an answer from behavior. | MUST NOT (assume) | negative | After a behavioral trigger fires (§17), no `answers` row is written automatically; only a `BehavioralPromptSuggestion` is created, and `answers` remains unchanged until the user explicitly responds. |
| C-8.3.2 | §8.3 | The app MUST NOT silently change a user's existing preference based on behavior. | MUST NOT | negative | Same oracle as C-8.3.1, an `answers.partner_value` that existed before the trigger is byte-identical after the trigger fires and before the user acts on the suggestion. |
| C-8.4.1 | §8.4 | Users can mark an interest tag `public` or `private_reciprocal` ("visible only to people who share this interest"). | MUST | fixture-data | `UserTag.visibility ∈ {'public','private_reciprocal','hidden'}` (`TagVisibility`), settable via profile API. |
| C-8.4.2 | §8.4 | A `private_reciprocal` tag does NOT appear on the profile as seen by a viewer who does not share that tag. | MUST NOT | negative | Viewer B (no matching tag) fetching viewee A's profile via `GET /profiles/{userId}` does not see A's `private_reciprocal` tag in the response. |
| C-8.4.3 | §8.4 | A `private_reciprocal` tag DOES appear when the viewer also has that tag. | MUST | integration | Viewer B (has the same tag, any visibility) fetching A's profile sees the tag surfaced. |
| C-8.5.1 | §8.5 | Sensitive questions allow "explicit answer". | MUST | integration | A `sensitive:true` question accepts a normal 1 to 5 `selfValue`/`partnerValue`. |
| C-8.5.2 | §8.5 | Sensitive questions allow "prefer not to say". | MUST | integration | `selfValue: null` (per `AnswerValue = 1\|2\|3\|4\|5\|null`) is accepted and persisted for a sensitive question. |
| C-8.5.3 | §8.5 | Sensitive questions allow a private answer (visible only to self / not surfaced to counterpart raw). | MUST | integration | A sensitive answer is never returned verbatim in another user's view of the profile, only its contribution to compatibility scoring and/or hard-filter matching is observable. |
| C-8.5.4 | §8.5 | "Prefer not to say" is treated as neutral in compatibility scoring... | MUST | unit | `null` `selfValue`/`partnerValue` excludes that question from the pair's weighted sum (equivalent to a 0-weight/neutral contribution), see §16.2 "too few shared answered questions" handling. |
| C-8.5.5 | §8.5 | ...UNLESS it conflicts with a hard filter, in which case the hard filter still applies. | MUST | negative | If User A has a hard filter `wants_children >= 4` and User B answered "prefer not to say" on the corresponding self-question, B is still excluded from A's discovery (hard filter cannot be satisfied by a null/neutral answer), see Open Question OQ-2 for exactly how a null self-answer is treated by a hard-filter comparator. |

# §9 Filters

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-9.1.1 | §9.1 | Filters MUST be enforced strictly. | MUST | property | For every hard filter a user has enabled, zero candidates violating it ever appear in that user's `GET /discovery` response, across a randomized fixture population (property test, see test-strategy.md). |
| C-9.1.2 | §9.1 | The algorithm MUST NOT override a user's hard filter (no candidate that fails a hard filter is ever surfaced regardless of compatibility score). | MUST NOT | negative | A candidate with `compatibilityScore = 1.0` (perfect match) but failing one hard filter is absent from discovery output. **Cross-cutting invariant CC-1.** |
| C-9.2.1 | §9.2 | Each named example hard filter key (age range, has children, wants children, smoking, drinking, drug use, religion, relationship intention, gender preference, max distance) is enforceable. | MUST | property | Table-driven test: for each filter key, a candidate on the wrong side of the configured operator/value is excluded; one on the right side is not excluded by that filter. |
| C-9.2.2 | §9.2 | Admin-defined filters beyond the built-in list are supported. | MUST | integration | An admin-created custom `filter_key` behaves identically to a built-in one once present in `hard_filters`. |
| C-9.2.3 | §9.2 | Users MAY set many filters; filter slots are NOT blocked/limited. | MAY / MUST NOT limit | negative | Setting 20+ simultaneous hard filters for one user succeeds (`PATCH /me/filters`), no "max filters" error exists. |
| C-9.2.4 | §9.2 | If the pool becomes too small, the app shows the result count rather than silently preventing/ignoring filters. | MUST | integration | Same test as C-30.1.1, filters that yield 0 candidates still apply exactly as configured; the UI-facing count is 0, filters are not auto-relaxed. |
| C-9.3.1 | §9.3 | Reality dashboard shows X = "people who match your filters". | SHOULD | unit | `RealityDashboard.matchesMyFilters` = count of users passing viewer's hard filters (irrespective of whether viewer passes theirs). |
| C-9.3.2 | §9.3 | Reality dashboard shows Y = "people whose filters you match". | SHOULD | unit | `RealityDashboard.whoseFiltersIMatch` = count of users whose hard filters the viewer satisfies. |
| C-9.3.3 | §9.3 | Reality dashboard shows Z = "mutual match pool". | SHOULD | unit | `RealityDashboard.mutualMatchPool` = count where both directions of filter-passing hold, i.e. `Z ≤ min(X, Y)` always (property invariant). |
| C-9.4.1 | §9.4 | Discovery default requires mutual filter passing: candidate must satisfy my filters AND I must satisfy candidate's filters. | MUST (default) | integration | If viewer fails candidate's hard filter (even though candidate passes viewer's), candidate is excluded from viewer's discovery (and vice versa). |
| C-9.4.2 | §9.4 | Any one-sided-filtering ("browse-only") mode must be explicit/opt-in; mutual passing is the default and MUST NOT silently become one-sided. | MUST | negative | With no explicit browse-only flag set, discovery never surfaces a candidate failing a mutual check in either direction. |

# §10 Discovery Grid

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-10.1.1 | §10.1 | The discovery UI/data is a grid (not a swipe deck): candidates are returned as a list/page, not a one-at-a-time swipe queue. | MUST | fixture-data | `GET /discovery` returns a paginated array (`Page<DiscoveryCandidate>`), no "next card" single-item endpoint exists. |
| C-10.1.2 | §10.1 | Each card exposes primary photo, name, age, approximate distance, and at most one shared interest. | MUST | fixture-data | `DiscoveryCandidate` shape matches exactly: `primaryPhotoUrl`, `displayName`, `age`, `approximateDistanceKm`, `sharedInterestTag: string \| null` (never an array of >1). |
| C-10.1.3 | §10.1 | No public like count is shown. | MUST NOT | negative | `DiscoveryCandidate` has no `likeCount`/similar field; no route exposes it. |
| C-10.1.4 | §10.1 | No popularity score is shown. | MUST NOT | negative | Same, no `popularityScore` field anywhere in a non-admin response. |
| C-10.1.5 | §10.1 | No boost badge is shown. | MUST NOT | negative | Same, no `boosted`/`badge` field. |
| C-10.2.1 | §10.2 | Visible only if account is active. | MUST | negative | A `status:'suspended'` or `'deleted'` user never appears as a candidate. |
| C-10.2.2 | §10.2 | Visible only if not shadowbanned. | MUST | negative | A `shadowbanned:true` user never appears as a candidate to others (still usable by self, C-18.4.SM note). |
| C-10.2.3 | §10.2 | Visible only if profile is "complete enough". | MUST | negative | A profile below the configured completeness threshold is excluded. |
| C-10.2.4 | §10.2 | Visible only if the user has at least one **approved** photo. | MUST | negative | A user whose only photo is `moderation_status='pending'`/`'rejected'`/`'flagged'` is excluded (stricter than C-7.2.1's "at least one photo", must be *approved*). |
| C-10.2.5 | §10.2 | Visible only if incoming pending interests < incoming interest cap. | MUST | negative | Same test as C-30.3.1. |
| C-10.2.6 | §10.2 | Visible only if active conversations < active conversation cap (`chat.active_limit`, default 15). | MUST | negative | A user with 15 active conversations is excluded from being shown as a new candidate to others until one conversation leaves `active`. |
| C-10.2.7 | §10.2 | Visible only if viewer passes candidate's hard filters. | MUST | negative | Same as C-9.4.1 (direction 1). |
| C-10.2.8 | §10.2 | Visible only if candidate passes viewer's hard filters. | MUST | negative | Same as C-9.4.1 (direction 2). |
| C-10.2.9 | §10.2 | Visible only if neither user has blocked the other. | MUST | negative | A block row in either direction (`blocker_id`/`blocked_id`) removes the candidate from discovery for both parties. **Cross-cutting.** |
| C-10.3.1 | §10.3 | Grid is sorted by `compatibilityScore` descending as the primary key. | MUST | unit | Sorting a fixed candidate list by the documented comparator yields strictly descending `compatibilityScore` order (ties broken per below). |
| C-10.3.2 | §10.3 | Tie-break order is exactly: trust score → profile completeness → recent activity → response rate. | MUST | unit | Fixture with two candidates tied on `compatibilityScore`: higher `trustLevel`/`trustScore` sorts first; if also tied, higher `profileCompleteness`; if also tied, more recent `lastActiveAt`; if also tied, higher response rate. |
| C-10.3.3 | §10.3 | No candidate who passes hard filters is hidden by a compatibility-score floor. | MUST NOT | negative | Same as C-9.1.2 / C-1.17 / CC-1. |
| C-10.3.4 | §10.3 | Sorting is the ONLY effect of compatibility score on visibility (i.e. it never determines inclusion, only order). | MUST | property | Property test: shuffling `compatibilityScore` values across an otherwise-fixed, filter-passing candidate set changes the *order* of `GET /discovery` results but never the *set* (same ids returned). |

# §11 Match Interests

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-11.1.1 | §11.1 | An interest is a request to start a chat, not a date proposal. | MUST | fixture-data | `Interest` type has no venue/date/escrow fields; those live only on `DateProposal`. |
| C-11.1.2 | §11.1 | Sending an interest does NOT require payment. | MUST NOT | negative | `POST /interests` succeeds for a user with zero `payment_methods` on file. |
| C-11.2.1 | §11.2 | Default outgoing pending interest limit = 5. | MUST | unit | `ConfigKeyRegistry['interest.outgoing_pending_limit'].default === 5`; 6th concurrent pending outgoing interest is rejected (429 `rate_limited`) while 5 are already pending. |
| C-11.2.2 | §11.2 | Default incoming pending interest limit = 10. | MUST | unit | `ConfigKeyRegistry['interest.incoming_pending_limit'].default === 10`; recipient with 10 pending incoming interests stops appearing in senders' discovery (C-10.2.5) / an 11th send is rejected. |
| C-11.2.3 | §11.2 | Default interest expiry = 48 hours. | MUST | unit | `ConfigKeyRegistry['interest.expiry_hours'].default === 48`. |
| C-11.2.4 | §11.2 | Default daily outgoing interest limit = 20. | MUST | unit | 21st `POST /interests` within a rolling/calendar 24h window → 429 `rate_limited`, even if the outgoing-pending cap (5) has headroom because some expired/were declined. |
| C-11.3.1 | §11.3 | An interest MUST NOT include free text before match. | MUST NOT | negative | `POST /interests` payload schema has no `message`/`body` field; any such field, if present, is ignored/rejected. |
| C-11.3.2 | §11.3 | After match, chat is free-text. | MUST | integration | Same test as C-12.2.1. |
| C-11.4.1 | §11.4 | Sender cancel while pending → `interest = canceled`. | MUST | state-machine | See legal transition table below. |
| C-11.4.2 | §11.4 | Recipient accept → `interest = accepted`, `conversation = active`. | MUST | state-machine | See legal transition table below; a `conversations` row is created/activated in the SAME transaction as the interest update (atomicity, DB tx wraps both). |
| C-11.4.3 | §11.4 | Recipient decline → `interest = declined`. | MUST | state-machine | See legal transition table below. |
| C-11.4.4 | §11.4 | Sender sees a generic decline message, never harsh/specific detail. | MUST | fixture-data | Decline notification's `templateKey` renders exactly `"They passed on this match."`-equivalent static copy; no per-decline free-text reason field is ever surfaced to the sender. |
| C-11.4.5 | §11.4 | Recipient non-response before expiry → `interest = expired`. | MUST | state-machine | See legal transition table below; driven by §25.1 background job using `ManualClock`. |
| C-11.4.6 | §11.4 | On expiry, sender's outgoing slot is freed. | MUST | integration | After expiry, the sender's outgoing-pending count used for C-11.2.1 decreases by 1 and a 6th interest (previously blocked) can now be sent. |

## Interest state machine (§11.4)

States: `pending, accepted, declined, expired, canceled`. `accepted`, `declined`, `expired`, `canceled` are all terminal, no further transition is legal out of any of them.

| ID | From → To | Trigger | Side effects |
|---|---|---|---|
| C-11.4.SM.L1 | `pending → accepted` | recipient accepts | `conversation.status = 'active'` created/reused (same tx) |
| C-11.4.SM.L2 | `pending → declined` | recipient declines | generic decline notice to sender only (C-11.4.4) |
| C-11.4.SM.L3 | `pending → expired` | background job, `now ≥ expiresAt` | sender's outgoing slot freed (C-11.4.6) |
| C-11.4.SM.L4 | `pending → canceled` | sender cancels | sender's outgoing slot freed |

| ID | Illegal transition | Must be rejected because |
|---|---|---|
| C-11.4.SM.I1 | `accepted → declined` | terminal state |
| C-11.4.SM.I2 | `accepted → canceled` | terminal state (cancel endpoint only valid while `pending`) |
| C-11.4.SM.I3 | `declined → accepted` | terminal state |
| C-11.4.SM.I4 | `expired → accepted` | recipient cannot accept after expiry, even in the same request race |
| C-11.4.SM.I5 | `canceled → accepted` | terminal state |
| C-11.4.SM.I6 | `pending → pending` (double-accept race) | idempotency: concurrent accept+decline (or accept+accept) must resolve to exactly one terminal state, second writer gets `conflict` |
| C-11.4.SM.I7 | sender calling `accept`/`decline` on their own sent interest | role violation, only the `recipient_id` may accept/decline; only the `sender_id` may cancel |

# §12 Chat System

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-12.1.1 | §12.1 | Chat unlocks ONLY after mutual match (interest accepted). | MUST | negative | `POST /conversations/{id}/messages` for a conversation not yet `active`/`established` (e.g. no accepted interest exists between the two users) → 403/404; no message send path exists prior to match. |
| C-12.2.1 | §12.2 | Messages support plain text and emoji. | MUST | integration | A message body containing emoji unicode persists and returns unmodified. |
| C-12.2.2 | §12.2 | Messages MAY support predefined prompt cards. | MAY | integration | A prompt-card message type, if implemented, references a static card id, never free-generated text. |
| C-12.2.3 | §12.2 | MVP MUST NOT support images, audio, or video messages. | MUST NOT | negative | `POST /conversations/{id}/messages` accepts only a text `body`; no attachment/media field exists in the schema. |
| C-12.3.1 | §12.3 | Default max messages per user per hour = 120. | MUST | unit | `ConfigKeyRegistry['chat.max_messages_per_hour'].default === 120`; the 121st message within a rolling hour from the same sender → 429 `rate_limited`. |
| C-12.3.2 | §12.3 | Default max external links/hour for low (Limited) trust = 0. | MUST | unit | `ConfigKeyRegistry['chat.max_links_per_hour_low_trust'].default === 0`; same as C-6.4.2. |
| C-12.3.3 | §12.3 | Default max external links/hour for standard trust = 5. | MUST | unit | `ConfigKeyRegistry['chat.max_links_per_hour_standard_trust'].default === 5`; a Standard user's 6th link-bearing message within an hour is flagged/limited per policy (spec does not say "blocked", see C-19.3.1, links are never hard-blocked, only rate-limited for *clickability*, not for send). |
| C-12.4.1 | §12.4 | The app MAY use regex, keyword lists, domain lists, rate-based heuristics for text analysis. | MAY | fixture-data | `TextScanResult.flags[].matchedPattern` traces to a regex/keyword/domain rule, never a model call. |
| C-12.4.2 | §12.4 | The app MUST NOT use LLM-generated responses/analysis anywhere in text handling. | MUST NOT | negative | `message.service.ts`/`textscan.service.ts` have zero network calls to any generative model provider; `TextScanResult` is a pure function of `(body, ruleset)`, same input always produces the same output (determinism proves no model call). |
| C-12.5.1 | §12.5 | A message containing an Instagram handle, phone number, Snapchat/Telegram/WhatsApp reference, or URL is NOT blocked by default. | MUST NOT (block) | negative | Such a message still sends successfully (`201`), `analysisFlags` includes `external_contact`/`link`, but delivery is not prevented. |
| C-12.5.2 | §12.5 | Instead, a static notice is shown below the message. | MUST | fixture-data | The static template text (`"Booking your first date through the app includes venue perks and safety verification."`-equivalent) is attached via `safetyBannerTemplateKey`, not generated per-message. |
| C-12.6.1 | §12.6 | 72h after first message with no date proposal → show date prompt. | MUST | state-machine | `ManualClock` advanced 72h past `conversation`'s first message with no `date_proposals` row → §25.3 job marks/emits the date-prompt notification; conversation `status` unchanged (still `active`). |
| C-12.6.2 | §12.6 | 14 days with no date proposal → conversation moves to `cooling`. | MUST | state-machine | `ManualClock` advanced 14d, no proposal → `conversations.status = 'cooling'`. |
| C-12.6.3 | §12.6 | 21 days with no date proposal → conversation is `archived`. | MUST | state-machine | `ManualClock` advanced 21d, no proposal → `conversations.status = 'archived'`. |
| C-12.6.4 | §12.6 | If a date is completed at any point, the conversation becomes `established` and does NOT decay thereafter. | MUST | negative | A conversation with a `completed` date proposal, then `ManualClock` advanced 21+ more days → `status` remains `'established'`, never reverts to `cooling`/`archived`. **Cross-cutting invariant CC-6.** |
| C-12.7.1 | §12.7 | Established chats do not expire. | MUST NOT | negative | Same as C-12.6.4. |
| C-12.7.2 | §12.7 | Established chats do not count against pre-date chat slots (`chat.active_limit`). | MUST NOT | negative | A user with 15 `established` conversations plus a new mutual match still gets a 16th conversation created (established ones are excluded from the `chat.active_limit` count used in C-10.2.6). |
| C-12.7.3 | §12.7 | Established chats remain active unless a user blocks/archives explicitly. | MUST | negative | No background job transitions an `established` conversation away from that status; only an explicit user action (block, `POST /conversations/{id}/archive`) changes it. |

# §13 Date Proposals

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-13.1.1 | §13.1 | A date proposal can only be created from an active (or established) conversation. | MUST | negative | `POST /conversations/{id}/date-proposals` on a conversation not yet matched (never existed / still just a pending interest) → 403/404. |
| C-13.1.2 | §13.1 | Proposal includes venue, date, time slot, optional note, escrow amount, policy version (snapshot). | MUST | fixture-data | `DateProposal` carries `venueId, scheduledStart, scheduledEnd, optionalNote, escrowAmountCents, policySnapshot`. |
| C-13.1.3 | §13.1 | The app provides structured venue choices (not free-text venue entry). | MUST | negative | `venueId` must reference an existing `venues` row (`active:true`); a free-text venue name is rejected. |
| C-13.2.1 | §13.2 | Venue categories are exactly the 10 listed (coffee, dessert, drinks, walk, museum, arcade, live_music, comedy, class_activity, food_market). | MUST | fixture-data | `VenueCategory` union type / DB `CHECK` enumerates exactly these 10 values; a venue with an 11th category is rejected. |
| C-13.2.2 | §13.2 | Each venue carries id, name, address, lat/long, category, active flag, time slots, margin percentage, redemption method. | MUST | fixture-data | `Venue` type / `venues` table match. |
| C-13.3.1 | §13.3 | The 13 (14 incl. `completed_unverified`) listed statuses are the full `DateProposalStatus` enum, no others. | MUST | fixture-data | DB `CHECK (status IN (...))` in `db/migrations/001_init.sql` enumerates exactly the `DateProposalStatus` union in `domain/types.ts`. |

(Full legal/illegal transition table for the date-proposal state machine is under **§14 State Machine** below, since transitions are driven by the payment rules in §14 and §15.)

# §14 Payment and Escrow Flow

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-14.0.1 | §14 | Use a processor supporting authorization holds + manual capture. | MUST | fixture-data | `PaymentProcessor` port exposes distinct `authorize`/`capture`/`cancel`/`refund` methods; `capture` is never implicit in `authorize`. |
| C-14.0.2 | §14 | Do not store full card numbers; use tokens. | MUST NOT | negative | Same as C-28.4.1. |
| C-14.1.1 | §14.1 | Default escrow amount = $20/person = 2000 cents. | MUST | unit | `ConfigKeyRegistry['date.escrow_amount_cents'].default === 2000`. |
| C-14.1.2 | §14.1 | Amount is stored/handled as integer minor units (cents), never floating-point dollars. | MUST | unit | `escrowAmountCents`/`amountCents`/`amount_cents` are all `bigint`/`integer` columns (`db/migrations/001_init.sql`); no arithmetic path divides by 100 and stores a float. **Money hazard, flagged for minor-unit integer math.** |
| C-14.1.3 | §14.1 | Escrow amount MUST be configurable. | MUST | integration | Admin sets `date.escrow_amount_cents = 3000`; a *new* proposal created after the change uses 3000; see C-14.1.4 for existing-object behavior. |
| C-14.1.4 | §21.3/§21.4 | `date.escrow_amount_cents` is `scope: 'snapshot'`, an EXISTING (already-created) proposal must keep the escrow amount captured at its own creation time, even if config changes later. | MUST | integration | Create proposal P1 while config = 2000 → change config to 3000 → P1.`escrowAmountCents` and P1.`policySnapshot['date.escrow_amount_cents']` both remain 2000; a new proposal P2 created after the change uses 3000. **Money + config-snapshot hazard.** |
| C-14.2.1 | §14.2 Step 1 | Proposer sends date proposal → system authorizes proposer's payment method → `proposer_payment_hold = authorized`, `date_proposal = pending_acceptance`. No charge yet. | MUST | integration | `FakeProcessor.authorize` called with proposer's token → `payment_holds` row `status='authorized'`; `date_proposals.status='pending_acceptance'`; `FakeProcessor._debugGetIntent` shows `status:'authorized'`, never `'captured'`. |
| C-14.2.2 | §14.2 Step 2 | Recipient accepts → system authorizes recipient's payment method → `recipient_payment_hold = authorized`, `date_proposal = accepted`. | MUST | integration | Second `authorize` call for recipient; both holds now `authorized`; status transitions to `'accepted'`. |
| C-14.2.3 | §14.2 Step 3 | Once BOTH holds are authorized, system captures BOTH payments → both `payment` = `captured`, `date_proposal = charged`. | MUST | integration + ordering | `capture` is called for proposer's intent AND recipient's intent, both succeed; status becomes `'charged'` only after both captures return `status:'captured'`. **Ordering hazard: capture must never be attempted while only one hold is authorized (see CC-2).** |
| C-14.2.4 | §14.2 Step 4 | After successful capture, ticket/voucher is issued → `voucher = issued`, `date_proposal = ticketed`; ticket appears in both users' wallets. | MUST | integration | `vouchers` row created with `status='issued'` immediately (same tx) as `date_proposals.status` flips to `'ticketed'`; `GET /tickets` for BOTH proposer and recipient returns it. |
| C-14.3.1 | §14.3 | The actual charge (capture) happens ONLY after all four conditions in order: proposer hold authorized → recipient accepts → recipient hold authorized → both holds captured successfully. | MUST | ordering / negative | No code path calls `capture` before both `payment_holds` rows are `status='authorized'`. **Cross-cutting invariant CC-2.** |
| C-14.4.1 | §14.4 | Users get the ticket ONLY after both payments are captured successfully. | MUST | negative | No `vouchers` row exists while `date_proposals.status ∈ {'draft','pending_acceptance','accepted','payment_failed'}`; a voucher query before capture returns nothing. **Cross-cutting invariant CC-3.** |
| C-14.5.1 | §14.5 | Proposer authorization fails → `date_proposal = payment_failed`; notify proposer to update payment method. | MUST | negative | `FakeProcessor` token containing `"fail_authorize"` for proposer → `authorize` returns `status:'failed'`; `date_proposals.status='payment_failed'`; a `payment_failed`-type notification queued for proposer only. |
| C-14.5.2 | §14.5 | Recipient authorization fails → `date_proposal = payment_failed`, AND the proposer's already-authorized hold is released; notify BOTH users. | MUST | integration + ordering | Proposer authorizes fine, recipient token contains `"fail_authorize"` → recipient `authorize` fails → `cancel` is called on proposer's intent (`status:'released'`) in the SAME transaction as `date_proposals.status='payment_failed'`; notifications queued for both proposer and recipient. **Ordering/partial-failure hazard.** |
| C-14.5.3 | §14.5 | Capture fails after both authorizations succeed → `date_proposal = payment_failed`; ALL holds released (not captured). | MUST | integration + ordering | Both authorize succeed; one token contains `"fail_capture"` → that `capture` returns `'failed'` → the OTHER side's successful/pending capture must be rolled back to `cancel`/`release`, never left `captured` alone. **Critical partial-failure hazard: proves "do not charge one person without completing the pair" (CC-2).** Test: capture proposer succeeds, capture recipient fails (`fail_capture` token) → assert proposer's hold ends `released` (or refunded if capture already went through, see Open Question OQ-5) and recipient's ends `failed`, `date_proposals.status='payment_failed'`, and **no voucher is ever created**. |
| C-14.6.1 | §14.6 | If recipient does not accept within `date.accept_expiry_hours` (default 48h) → `date_proposal = expired`, proposer hold released. | MUST | state-machine | `ManualClock` advanced 48h past `createdAt` with no acceptance → §25.2 job sets `status='expired'`, `payment_holds` (proposer) → `cancel` called, `status='released'`. Boundary: at exactly 47h59m59s, still `pending_acceptance`; at exactly 48h00m00s, eligible for expiry. |
| C-14.7.1 | §14.7 | Config defaults: `full_refund_cutoff_hours=24`, `late_cancel_refund_percent=0`, `no_show_refund_percent=0`. | MUST | unit | Matches `ConfigKeyRegistry` exactly (see worked table below). |
| C-14.7.2 | §14.7 | Before acceptance, proposer cancels → proposer hold released, `date_proposal=canceled`. | MUST | state-machine | `cancel` called on proposer's authorized intent; recipient hold never existed yet (nothing to release there). |
| C-14.7.3 | §14.7 | After acceptance (i.e. once captured), cancel MORE than `full_refund_cutoff_hours` before `scheduledStart` → refund BOTH users in full, `voucher=canceled`, `date_proposal=refunded`. | MUST | state-machine + numeric | See worked example below. |
| C-14.7.4 | §14.7 | After acceptance, cancel LESS than `full_refund_cutoff_hours` before `scheduledStart` → no refund by default, `voucher = canceled or retained per policy`, `date_proposal = canceled`. | MUST | state-machine + numeric | See worked example below. |
| C-14.7.5 | §14.7 | This entire cancellation policy MUST be configurable. | MUST | integration | Changing `date.late_cancel_refund_percent` to a non-zero value changes the refund computed for a NEW cancellation event (existing/settled cancellations are not retroactively recomputed, snapshot semantics per §21.3). |
| C-14.8.1 | §14.8 | Every payment event is recorded in an immutable ledger with all 9 listed fields. | MUST | fixture-data | `LedgerEntry` type carries `id, userId, dateProposalId, paymentHoldId, type, amountCents, currency, processorReference, metadata, createdAt`, 10 fields (spec's 9 plus `paymentHoldId` which the code adds for traceability; superset is fine). |
| C-14.8.2 | §14.8 | Ledger `type` is exactly one of: authorization, capture, release, refund, dispute, chargeback. | MUST | fixture-data | DB `CHECK (type IN (...))` matches `LedgerEntryType` exactly. |
| C-14.8.3 | §14.8 | The ledger is append-only / immutable, no UPDATE or DELETE of a ledger row, ever. | MUST | negative | Same as cross-cutting invariant CC-4: no service function issues `UPDATE payment_ledger` or `DELETE FROM payment_ledger`; every state change writes a NEW row. |

## §14.7 Cancellation and Refunds, worked examples

Escrow = 2000 cents/person (default). `full_refund_cutoff_hours = 24`. `late_cancel_refund_percent = 0`. `no_show_refund_percent = 0`.

| Case | Time of cancel relative to `scheduledStart` | Expected `date_proposal` status | Refund per user (cents) | Retained per user (cents) |
|---|---|---:|---:|---:|
| C-14.7.W1 | 25h before (more than cutoff) | `refunded` | `2000 * 100/100 = 2000` | 0 |
| C-14.7.W2 | exactly 24h00m00s before (**boundary, see OQ-1**) | recommended: `refunded` (treat cutoff as inclusive) | 2000 | 0 |
| C-14.7.W3 | 23h59m59s before (less than cutoff) | `canceled` | `2000 * 0/100 = 0` | 2000 |
| C-14.7.W4 | no-show (post-date, one user never attends) | `no_show` (see Open Question OQ-3 on how this status is actually entered) | `2000 * 0/100 = 0` | 2000 |
| C-14.7.W5 | Config changed to `late_cancel_refund_percent=50`, cancel at 12h before | `canceled` | `2000 * 50/100 = 1000` | 1000 |
| C-14.7.W6 | Non-exact-percent money-rounding case: escrow=1999 cents, `late_cancel_refund_percent=33`, cancel inside cutoff | `canceled` | `floor(1999 * 33 / 100) = floor(659.67) = 659` | `1999 - 659 = 1340` |

C-14.7.W6 asserts the **rounding rule**: the spec never states a rounding direction for a
percent that doesn't divide evenly into whole cents. This test plan's recommendation
(recorded in Open Questions OQ-6) is **floor** (round down the refund, so the platform/venue
never pays out more than the percent allows), the test author should treat `659` as the
oracle unless product overrides this in writing.

# §15 Ticket/Voucher System

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-15.1.1 | §15.1 | Ticket includes all 8 listed fields (voucher id, date proposal id, venue id, user names, scheduled time, amount/value, QR payload, expiration). | MUST | fixture-data | `Voucher` + joined `DateProposal`/`Venue`/user display names collectively expose all 8. |
| C-15.2.1 | §15.2 | QR payload is a signed JWT-or-similar signed token. | MUST | integration | `voucher.qrPayload` verifies against `src/lib/signing.ts`'s signature check; a tampered payload fails verification. |
| C-15.2.2 | §15.2 | QR payload does NOT include full payment card data. | MUST NOT | negative | Decoded `VoucherQrPayload` fields are exactly `{voucher_id, venue_id, date_proposal_id, expires_at}` (+ signature), no `card`/`pan`/`payment` field. Same test as C-28.4.1 scoped to vouchers. |
| C-15.3.1 | §15.3 | Venue staff scans/enters code; redemption records voucher id, venue staff id, timestamp, method. | MUST | fixture-data | `VenueRedemption` type/`venue_redemptions` table carry all 4 fields. |
| C-15.3.2 | §15.3 | On redemption: `voucher = redeemed`. | MUST | state-machine | See voucher state machine below. |
| C-15.3.3 | §15.3 | On redemption: `date_proposal = completed`. | MUST | state-machine | See date-proposal state machine below. |
| C-15.3.4 | §15.3 | On redemption: `conversation = established`. | MUST | state-machine | Same transaction as C-15.3.2/3, atomic 3-way state change. |
| C-15.4.1 | §15.4 | If venue doesn't scan and BOTH users confirm attendance within 72h (`date.no_scan_confirmation_hours`) of the scheduled date → `date_proposal = completed_unverified`, `conversation = established`. | MUST | state-machine + boundary | Both `AttendanceConfirmation` rows created with `confirmedAt` within 72h of `scheduledEnd` → status transitions; at exactly 72h00m01s after `scheduledEnd` with only one/no confirmation, the window has closed (see C-15.4.3). |
| C-15.4.2 | §15.4 | `completed_unverified` does NOT automatically settle venue payment. | MUST NOT | negative | No venue-payout/settlement ledger entry (there is no such `LedgerEntryType` at all, see Open Question OQ-8) is created as a side effect of `completed_unverified`; user-side capture already happened at C-14.2.3 and is unaffected either way. |
| C-15.4.3 | §15.4 | If only ONE user confirms (within the window, and the venue never scanned) → `date_proposal = disputed`. | MUST | state-machine | One `AttendanceConfirmation` row, window closes with no second confirmation and no scan → `status='disputed'`. |
| C-15.4.4 | §15.4 | Disputed proposals receive "automated handling... according to policy" (no human required). | MUST | negative | Same as C-18.1.1 scoped to disputes, resolution is reachable via automated rule/job only; see Open Question OQ-3 for the exact resolution rule the spec never states. |

## Voucher state machine (§15 / §23.20)

States: `issued, redeemed, expired, canceled`. `redeemed`, `expired`, `canceled` are terminal.

| ID | From → To | Trigger |
|---|---|---|
| C-15.SM.L1 | `issued → redeemed` | venue staff scan/manual-code redemption (C-15.3.2) |
| C-15.SM.L2 | `issued → expired` | §25.8 voucher-expiry job, unredeemed past `voucher.expiry_hours_after_date_end` (default 72h after `scheduledEnd`) |
| C-15.SM.L3 | `issued → canceled` | the underlying date proposal is canceled/refunded after ticketing (C-14.7.3/4 late paths reaching a `ticketed` proposal) |

| ID | Illegal transition |
|---|---|
| C-15.SM.I1 | `redeemed → expired` / `redeemed → canceled`, a redeemed voucher is terminal, cannot un-redeem |
| C-15.SM.I2 | `expired → redeemed`, venue cannot scan a code past its expiry |
| C-15.SM.I3 | `canceled → redeemed`, a canceled proposal's voucher cannot later be scanned |
| C-15.SM.I4 | scanning the same voucher twice (`redeemed → redeemed`), second scan must be rejected as `conflict`, not silently accepted |

# §16 Compatibility Algorithm

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-16.1.1 | §16.1 | The algorithm sorts only; it does not hide filter-passing candidates, EXCEPT for: capacity limits, moderation restrictions, blocking, incomplete profile, geographic limits. | MUST | negative | Same as C-9.1.2/CC-1, with the 5 named exceptions enumerated as the ONLY legitimate exclusion reasons, a property test asserts every excluded-but-filter-passing candidate's exclusion reason is one of exactly these 5. |
| C-16.2.* | §16.2 | Compatibility score formula, see worked examples below. | MUST | unit | n/a |
| C-16.3.1 | §16.3 | For MVP, score MAY be computed on demand. | MAY | unit | `compatibility.service.ts` exposes a pure `computeScore(a, b, questions)` callable synchronously per-pair. |
| C-16.3.2 | §16.3 | For scale, scores MAY be precomputed nightly/incrementally into `compatibility_scores` (`user_id, candidate_id, score, computed_at`). | MAY | integration | §25.4 job populates `compatibility_scores` rows matching on-demand computation for the same inputs (consistency between the two paths is itself a property test). |

## §16.2 Compatibility score formula, worked examples

Formula (verbatim from spec, per question `i`):

```
satisfaction_A_with_B = 1 - abs(A.partner_answer[i] - B.self_answer[i]) / 4
satisfaction_B_with_A = 1 - abs(B.partner_answer[i] - A.self_answer[i]) / 4
pair_satisfaction[i]  = (satisfaction_A_with_B + satisfaction_B_with_A) / 2
question_weight[i]    = base_weight[i] * importance_multiplier[i]
importance_multiplier = 1 + abs(partner_answer - 3) * 0.25
compatibility_score   = sum(pair_satisfaction[i] * question_weight[i]) / sum(question_weight[i])
```

Reversed polarity: `transformed_value = 6 - original_value`, applied to a question's raw
answers **before** the satisfaction formula runs. Note the arithmetic identity
`|(6-x)-3| = |3-x| = |x-3|`, the importance multiplier's magnitude is unaffected by
whether it's computed from the raw or the polarity-transformed value, so the ambiguity
about which one §16.2 means does not change the final number (still worth a unit test
asserting both give the identical `question_weight`, see C-16.2.W5).

Because the spec's `importance_multiplier` formula references a single `partner_answer`
but two different partner answers exist per question (A's and B's), this test plan
resolves the ambiguity as: **compute the multiplier once per direction (from each side's
own partner_answer) and average the two** to get one `question_weight` per question. This
is recorded as Open Question OQ-9, flag it to product, but use the averaged value as the
test oracle below unless overridden.

**Worked fixture, two questions:**

Q1 "Pets": `base_weight = 2`, `polarity = standard`.
- `A.partner_answer[Q1] = 5`, `B.self_answer[Q1] = 2` → `satisfaction_A_with_B = 1 - |5-2|/4 = 1 - 0.75 = 0.25`
- `B.partner_answer[Q1] = 4`, `A.self_answer[Q1] = 5` → `satisfaction_B_with_A = 1 - |4-5|/4 = 1 - 0.25 = 0.75`
- `pair_satisfaction[Q1] = (0.25 + 0.75)/2 = 0.5`
- `multiplier_A[Q1] = 1 + |5-3|*0.25 = 1.5`; `multiplier_B[Q1] = 1 + |4-3|*0.25 = 1.25`; averaged = `1.375`
- `question_weight[Q1] = 2 * 1.375 = 2.75`

Q2 "Smoking": `base_weight = 4`, `polarity = reversed`. Raw stored values: `A.partner_answer_raw=1, B.self_answer_raw=2, B.partner_answer_raw=1, A.self_answer_raw=1`. Transformed (`6-x`): `A.partner_answer=5, B.self_answer=4, B.partner_answer=5, A.self_answer=5`.
- `satisfaction_A_with_B = 1 - |5-4|/4 = 0.75`
- `satisfaction_B_with_A = 1 - |5-5|/4 = 1.0`
- `pair_satisfaction[Q2] = (0.75+1.0)/2 = 0.875`
- `multiplier_A[Q2] = 1+|5-3|*0.25 = 1.5`; `multiplier_B[Q2] = 1+|5-3|*0.25 = 1.5`; averaged = `1.5`
- `question_weight[Q2] = 4 * 1.5 = 6`

**Final score:**
```
compatibility_score = (0.5*2.75 + 0.875*6) / (2.75 + 6)
                     = (1.375 + 5.25) / 8.75
                     = 6.625 / 8.75
                     = 53/70
                     ≈ 0.757142857...
```

| ID | Assertion |
|---|---|
| C-16.2.W1 | Given the Q1+Q2 fixture above, `computeScore(A,B) === 53/70` (assert with a small epsilon, e.g. `Math.abs(score - 53/70) < 1e-9`). |
| C-16.2.W2 | Perfect match boundary: every question's `partner_answer === counterpart.self_answer` in both directions (`abs diff = 0`) → `pair_satisfaction = 1` for every question → `compatibility_score === 1.0` regardless of weights. |
| C-16.2.W3 | Worst-case boundary: every question's `partner_answer` and counterpart's `self_answer` are 4 apart (e.g. partner_answer=5, self_answer=1) → `pair_satisfaction = 0` for every question → `compatibility_score === 0.0`. |
| C-16.2.W4 | Reversed-polarity transform: `transformed_value(1) === 5`, `transformed_value(3) === 3` (fixed point), `transformed_value(5) === 1`. |
| C-16.2.W5 | Importance-multiplier magnitude is identical whether computed pre- or post-polarity-transform (arithmetic identity above), regression test pinning this so a future refactor doesn't silently break it. |
| C-16.2.W6 | "Too few shared answered questions" → score defaults per Open Question OQ-2 (spec says "0 or neutral", genuinely ambiguous, both a hard zero and a ~0.5 "neutral" are plausible readings). Test both an explicit config-driven default and the literal `0` fallback are each achievable and documented; pick ONE as the shipped oracle (this plan recommends `0`, treated as "no evidence of compatibility" rather than "neutral," to avoid falsely inflating sort position for data-sparse profiles, see OQ-2). |
| C-16.2.W7 | Score is always clamped to `[0, 1]` inclusive (property test over random weight/answer fixtures). |

# §17 Behavioral Question Trigger

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-17.1 | §17 r.1 | The app MUST NOT assume the answer from a detected behavioral pattern. | MUST NOT | negative | Same as C-8.3.1. |
| C-17.2 | §17 r.2 | The app MUST NOT silently change sorting/scoring based on the pattern alone. | MUST NOT | negative | `compatibility_scores`/live score computation is unchanged until the user explicitly answers the suggested question; same underlying oracle as C-8.3.2. |
| C-17.3 | §17 r.3 | The app MUST ask the user explicitly (a `BehavioralPromptSuggestion` is surfaced, referencing a real `questionId`). | MUST | integration | Triggering the pattern (e.g. accepting several profiles sharing a tag) creates a `BehavioralPromptSuggestion` row visible to the user, never an auto-answer. |
| C-17.4 | §17 r.4 | The user MUST be able to skip the suggested question. | MUST | integration | A "skip" action on the suggestion leaves `answers` untouched and does not re-prompt indefinitely (dismissal is recorded so the same suggestion isn't repeated every request). |

# §18 Moderation and Safety

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-18.1.1 | §18.1 | The system MUST assume zero human moderators, every moderation action is reachable via automated code paths alone. | MUST | negative | An end-to-end integration test drives report → score → automated action → (optional) automated appeal → resolution with **no** admin-authenticated call in the sequence at all; the only admin-touching route in the whole suite is the read-only "review" route (C-4.3.5), never a required step. **Cross-cutting invariant CC-7 / proves DoD #17.** |
| C-18.1.2 | §18.1 | Moderation is automated. | MUST | negative | Same as C-18.1.1. |
| C-18.1.3 | §18.1 | Moderation is rule-based. | MUST | fixture-data | Every automated action traces to an explicit rule/threshold (§18.5), never an opaque ML classifier making the final call. |
| C-18.1.4 | §18.1 | Moderation is threshold-based. | MUST | unit | Same as C-18.5 worked table. |
| C-18.1.5 | §18.1 | Moderation is community-report-driven. | MUST | integration | `POST /reports` is a first-class, load-bearing input to the scoring pipeline (C-18.5). |
| C-18.1.6 | §18.1 | Appeals are automated where possible. | SHOULD | integration | Same as C-18.6.*. |
| C-18.2.1 | §18.2 | All 11 listed signals feed the moderation pipeline (reports, block count, message velocity, repeated identical messages, regex scam patterns, nudity/violence image detection, duplicate photo hashes, device reputation, payment fraud signals, no-shows, negative post-date feedback). | MUST | fixture-data | Each signal has a concrete producer in the codebase (e.g. `Block` rows feed a block-count signal, `MessageFlag` feeds pattern signals) that is included in the §18.5 score aggregation, even if weighted differently. |
| C-18.3.1 | §18.3 | Reports MUST be structured (one of the 10 listed categories). | MUST | negative | `POST /reports` with `category` outside the `ReportCategory` enum → 400 `validation_error`; DB `CHECK` is the backstop. |
| C-18.3.2 | §18.3 | The app MUST NOT rely only on free-text reports, `category` is mandatory, `details` free text is supplementary only. | MUST NOT (rely on text alone) | negative | `POST /reports` with `details` but no `category` → 400 `validation_error`; scoring never parses `details` as the primary signal. |
| C-18.4.1 | §18.4 | Automated action set is exactly: `none, warning, restriction, shadowban, suspension`. | MUST | fixture-data | `ModerationActionType` / DB `CHECK` matches exactly. |
| C-18.4.2 | §18.4 | Restriction MAY reduce discovery visibility. | MUST (as one of the possible restriction effects) | integration | A `restriction` action lowers/zeroes the restricted user's presence in others' `GET /discovery`. |
| C-18.4.3 | §18.4 | Restriction MAY limit outgoing interests. | MUST | integration | A `restriction` action reduces the restricted user's effective `interest.outgoing_pending_limit` below the unrestricted default. |
| C-18.4.4 | §18.4 | Restriction MAY disable links. | MUST | integration | A `restriction` action forces link-clickability off regardless of trust level (overrides C-6.4.3/4). |
| C-18.4.5 | §18.4 | Restriction MAY require additional verification. | MUST | integration | A `restriction` action gates some action (e.g. sending a new interest) behind an appeal-style verification step. |
| C-18.4.6 | §18.4 | Shadowbanned user can still use the app... | MUST | integration | A `shadowbanned:true` user can still log in, browse, chat in existing conversations, send messages. |
| C-18.4.7 | §18.4 | ...but is not shown to others. | MUST NOT | negative | Same as C-10.2.2. |
| C-18.4.8 | §18.4 | Suspension blocks access entirely. | MUST | negative | A `suspended:true` user's authenticated requests (beyond `/auth/*` and appeal routes) are rejected. |
| C-18.4.9 | §18.4 | Suspension is used only for severe/repeated automated violations (i.e. is the top of the escalation, reachable only at the highest score band). | MUST | unit | Same as C-18.5 worked table, suspension threshold (`moderation.auto_suspension_score`, default 95) is strictly the highest of the three configured thresholds (50 < 80 < 95). |
| C-18.5.1 | §18.5 | Report score depends on: category, reporter trust, reporter/reported relationship, count of previous reports, recency. | MUST | fixture-data | The score-aggregation function's input signature includes all 5 factors; a fixture varying only `reporterTrust` changes the resulting score. |
| C-18.5.2 | §18.5 | A scam report from a trusted reporter is weighted HIGH. | SHOULD | unit | Fixture: `category='scam_money_request'`, `reporterTrust='trusted'` → resulting per-report score is at or near the top of the configured weight range. |
| C-18.5.3 | §18.5 | A duplicate report from the same social cluster is weighted LOWER (reduced) than an independent one. | SHOULD | unit | Two reports against the same user from accounts sharing a device/IP cluster contribute less combined score than two reports from unrelated accounts. |
| C-18.5.4 | §18.5 | A no-show report after a COMPLETED date is weighted MEDIUM. | SHOULD | unit | Fixture: `category='no_show'` tied to a `date_proposals.status='completed'`/`no_show` record → mid-range weight, distinct from the scam-report high weight and a routine `spam` report's lower weight. |
| C-18.5.5 | §18.5 | If score exceeds `moderation.auto_restriction_score` (default 50) → `restriction`. | MUST | unit + boundary | See worked table below. |
| C-18.5.6 | §18.5 | If score is higher still, exceeding `moderation.auto_shadowban_score` (default 80) → `shadowban`. | MUST | unit + boundary | See worked table below. |
| C-18.5.7 | §18.5 | If severe, exceeding `moderation.auto_suspension_score` (default 95, an implementation addition; not itself in the §21.4 table but required by §18.5's "if severe: suspension" clause) → `suspension`. | MUST | unit + boundary | See worked table below. |
| C-18.5.8 | §18.5 | All thresholds MUST be configurable. | MUST | integration | Changing `moderation.auto_restriction_score` changes the boundary used by the NEXT recalculation (live scope, not snapshot, §21.4 marks these `live`). |
| C-18.6.1 | §18.6 | Appeal steps MAY include: liveness check, verify payment method, cooldown wait, confirm identity via existing signals. | MAY | fixture-data | `AppealMethod` union matches these 4. |
| C-18.6.2 | §18.6 | If appeal passes, account is restored. | MUST | state-machine | `Appeal.status='approved'` → the triggering `moderation_actions` effect is lifted (e.g. `shadowbanned` flips back to `false`). |
| C-18.6.3 | §18.6 | If appeal fails, restriction is maintained. | MUST | state-machine | `Appeal.status='rejected'` → no change to the user's restricted state. |
| C-18.6.4 | §18.6 | Appeals are automated (no human moderation dependency). | MUST | negative | Same as C-18.1.1, scoped to the appeal path specifically, `resolveAppeal` never blocks on an admin action. |

## §18.5 Report scoring, worked threshold table

Using code defaults `moderation.auto_restriction_score=50`, `moderation.auto_shadowban_score=80`, `moderation.auto_suspension_score=95`:

| Cumulative score | Expected action | Note |
|---:|---|---|
| 0 | `none` | |
| 49 | `none` | just below restriction threshold |
| 50 | **see Open Question OQ-10** | spec says "exceeds" (strict `>`); this plan recommends inclusive `>=` for consistency with the §6.1 level-band convention, test author must pick one and pin it; this plan's oracle: `restriction` |
| 51 | `restriction` | unambiguous |
| 79 | `restriction` | just below shadowban threshold |
| 80 | `shadowban` (recommended inclusive, same OQ-10 caveat) |  |
| 94 | `shadowban` | just below suspension threshold |
| 95 | `suspension` (recommended inclusive, same OQ-10 caveat) |  |
| 100 | `suspension` | |

| ID | Assertion |
|---|---|
| C-18.5.W1 | Score-to-action mapping matches every row of the table above using the recommended inclusive (`>=`) semantics. |
| C-18.5.W2 | Recalculation only ESCALATES automatically; a later drop in score (e.g. old reports aging out under "recency") does NOT automatically de-escalate an existing `suspension`/`shadowban`/`restriction`, de-escalation happens only via the explicit appeal path (C-18.6.2). This is an inferred rule (spec doesn't say directly), flagged as Open Question OQ-11, recommended because §18.6 exists specifically to be the de-escalation mechanism. |

# §19 Scam Prevention

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-19.1.1 | §19.1 | Escrow acts as an economic deterrent (design rationale, not independently unit-testable). | n/a | n/a | Not independently testable; subsumed by §14's escrow-flow tests. |
| C-19.2.1 | §19.2 | Device fingerprinting, IP reputation, emulator detection, VPN/proxy detection, and rate limiting are all used as signals. | MUST | fixture-data | `device_fingerprints` schema (`user_auth_events`, `device_fingerprint`, `ip_address`) captures these; rate limiting is exercised throughout §11/§12. |
| C-19.3.1 | §19.3 | Regex/keyword rules exist for: crypto, gift cards, wire transfer, cashapp/venmo/zelle, emergency money, investment offers, telegram/whatsapp links, adult-content promotion. | MUST | unit | Table-driven test: one representative message per category matches a rule and produces a `money_request`/`crypto`/`spam_pattern` flag as appropriate. |
| C-19.3.2 | §19.3 | These messages are NOT auto-blocked by default. | MUST NOT | negative | A message matching a scam pattern still sends (`201`); it is flagged internally, never rejected outright. |
| C-19.3.3 | §19.3 | Instead: flagged internally. | MUST | integration | A `message_flags` row is created. |
| C-19.3.4 | §19.3 | Instead: safety banner shown if appropriate. | MUST | integration | `TextScanResult.showSafetyBanner === true` for a matched pattern. |
| C-19.3.5 | §19.3 | Instead: fraud score increases if the pattern repeats. | MUST | integration | Repeated matches from the same sender increase a fraud-related trust-negative signal (feeds C-6.2.2) over a single occurrence. |
| C-19.4.1 | §19.4 | Links display as plain text by default. | MUST | integration | A link in a message body renders as text, not an auto-linked anchor, absent the clickability rule below. |
| C-19.4.2 | §19.4 | For low-trust (Limited) users, links are NOT clickable. | MUST | negative | Same as C-6.4.2/C-12.3.2. |
| C-19.4.3 | §19.4 | For standard/trusted users, links MAY be clickable but show a warning if the domain is unknown. | MUST | integration | Same as C-6.4.3; an unknown-domain link carries a warning flag distinct from a known/allowlisted domain. |

# §20 Notification System

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-20.0.1 | §20 | ALL notification text MUST be static or template-based; no generated natural language anywhere. | MUST | negative | Every `Notification.templateKey` resolves through a fixed, enumerable template map; no notification-sending code path calls a generative model or does free-form string interpolation of arbitrary user-authored content into a "natural" sentence beyond named-slot substitution (e.g. `{displayName}`) into a fixed template. |
| C-20.1.1 | §20.1 | All 16 listed notification events are covered by the `NotificationEventType` enum and each is actually emitted at the right trigger point. | MUST | integration | Table-driven: trigger each of the 16 events (interest received/accepted/declined/expiring-soon, chat opened, date proposal received, date accepted, payment hold authorized, payment failed, ticket issued, date reminder, venue redeemed, post-date feedback request, chat cooling, trust level changed, safety notice) and assert a matching `Notification` row is queued. |
| C-20.2.1 | §20.2 | Channels used: push, email, in-app notification center. | MUST | fixture-data | `NotificationChannel` union matches exactly `push \| email \| in_app`. |
| C-20.2.2 | §20.2 | SMS is NOT used by default. | MUST NOT | negative | `NotificationChannel` has no `'sms'` member at all; no code path sends via a phone-number/SMS gateway. |

# §21 Configuration System

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-21.1.1 | §21.1 | `config_entries` carries key, value_json, description, version, updated_by, updated_at. | MUST | fixture-data | Matches `config_entries` migration + `ConfigService.set` write shape. |
| C-21.2.1 | §21.2 | Config service caches values. | MUST | unit | A second `ConfigService.get(key)` call does not re-hit the DB (mock/spy the `db.query` call count = 1 across 2 `get`s). |
| C-21.2.2 | §21.2 | Config service invalidates cache on change. | MUST | unit | After `set(key, newValue)`, the very next `get(key)` (same process) returns `newValue`, not the stale cached one. |
| C-21.2.3 | §21.2 | Config service supports versioning. | MUST | integration | `set` increments `version` by 1 on each write (`INSERT...ON CONFLICT DO UPDATE SET version = version + 1`); first write is version 1. |
| C-21.2.4 | §21.2 | Config service supports environment scope. | SHOULD | fixture-data | Config loading is environment-aware (dev/test/prod do not cross-contaminate), at minimum, tests run against an isolated DB per test-strategy.md so this is structurally guaranteed even if the table itself has no explicit `environment` column in the current schema (flag as a possible schema gap if truly absent, see Open Questions). |
| C-21.2.5 | §21.2 | Config service logs changes. | MUST | integration | `set` calls `logger.info('config.changed', {key, version, updatedBy, at})`, same event backs C-28.6.3 (audit log of config changes). |
| C-21.3.1 | §21.3 | Sending an interest stores a policy snapshot with (at least) `interest_expiry_hours, escrow_amount_cents [n/a for interest], full_refund_cutoff_hours [n/a], incoming_interest_limit`. | MUST | integration | `Interest.policySnapshot` = exactly `INTEREST_POLICY_KEYS`'s live values at creation time: `interest.expiry_hours, interest.outgoing_pending_limit, interest.incoming_pending_limit`. (Spec's illustrative JSON example in §21.3 mixes interest and date keys in one object; this plan treats it as illustrative, not literal, each object type gets its OWN relevant subset, per `INTEREST_POLICY_KEYS` / `DATE_PROPOSAL_POLICY_KEYS` in `config.service.ts`.) |
| C-21.3.2 | §21.3 | Sending a date proposal stores a policy snapshot with the 6 `DATE_PROPOSAL_POLICY_KEYS`. | MUST | integration | `DateProposal.policySnapshot` = exactly those 6 keys' live values at creation time. |
| C-21.3.3 | §21.3 | Existing objects must NOT unexpectedly change rules when config changes later, this is what "existing keep original" means for `scope:'snapshot'` keys. | MUST NOT | negative | Same test pattern as C-14.1.4, generalized across every `scope:'snapshot'` key in the registry (7 of them: `interest.expiry_hours`, `date.escrow_amount_cents`, `date.accept_expiry_hours`, `date.full_refund_cutoff_hours`, `date.late_cancel_refund_percent`, `date.no_show_refund_percent`, `date.no_scan_confirmation_hours`). **Cross-cutting invariant CC-8.** |
| C-21.4.* | §21.4 | Config variable defaults table. | MUST | unit | See worked table below. |

## §21.4 Config variables, defaults table

Every value below is the literal `ConfigKeyRegistry[...].default` in `src/config/config.service.ts`, which is the executable source of truth and matches the spec's own §21.4 table for the 13 keys the spec explicitly tabulates (rows marked "§21.4" below); the remaining rows are keys the spec requires elsewhere (§11.2, §12.3, §14.7, §15.4, §18.5, §18.6, §6.1) that the implementation centralizes here too, flagged `(extra)`.

| ID | Key | Default | Scope | In spec's own §21.4 table? |
|---|---|---:|---|---|
| C-21.4.1 | `interest.outgoing_pending_limit` | 5 | live | yes |
| C-21.4.2 | `interest.incoming_pending_limit` | 10 | live | yes |
| C-21.4.3 | `interest.expiry_hours` | 48 | **snapshot** | yes ("existing keep original") |
| C-21.4.4 | `chat.active_limit` | 15 | live | yes |
| C-21.4.5 | `chat.date_prompt_hours` | 72 | live | yes |
| C-21.4.6 | `chat.pre_date_archive_days` | 21 | live | yes |
| C-21.4.7 | `date.escrow_amount_cents` | 2000 | **snapshot** | yes |
| C-21.4.8 | `date.accept_expiry_hours` | 48 | **snapshot** | yes |
| C-21.4.9 | `date.full_refund_cutoff_hours` | 24 | **snapshot** | yes |
| C-21.4.10 | `date.late_cancel_refund_percent` | 0 | **snapshot** | yes |
| C-21.4.11 | `moderation.auto_restriction_score` | 50 | live | yes |
| C-21.4.12 | `moderation.auto_shadowban_score` | 80 | live | yes |
| C-21.4.13 | `trust.link_min_level` | `'standard'` | live | yes |
| C-21.4.14 | `interest.daily_outgoing_limit` | 20 | live | (extra, from §11.2) |
| C-21.4.15 | `chat.max_messages_per_hour` | 120 | live | (extra, from §12.3) |
| C-21.4.16 | `chat.max_links_per_hour_low_trust` | 0 | live | (extra, from §12.3) |
| C-21.4.17 | `chat.max_links_per_hour_standard_trust` | 5 | live | (extra, from §12.3) |
| C-21.4.18 | `date.no_show_refund_percent` | 0 | **snapshot** | (extra, from §14.7) |
| C-21.4.19 | `date.no_scan_confirmation_hours` | 72 | **snapshot** | (extra, from §15.4) |
| C-21.4.20 | `voucher.expiry_hours_after_date_end` | 72 | **snapshot** | (extra, from §25.8) |
| C-21.4.21 | `moderation.auto_suspension_score` | 95 | live | (extra, from §18.5 "if severe") |
| C-21.4.22 | `moderation.appeal_cooldown_hours` | 24 | live | (extra, from §18.6) |
| C-21.4.23 | `trust.level_standard_min` | 40 | live | (extra, from §6.1) |
| C-21.4.24 | `trust.level_trusted_min` | 70 | live | (extra, from §6.1) |
| C-21.4.25 | `trust.level_elite_min` | 90 | live | (extra, from §6.1) |

# §22 Feature Flags

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-22.1 | §22 | Flag fields: key, enabled, rollout_percent, target_user_segments, created_at, updated_at. | MUST | fixture-data | `FeatureFlag` type matches (code names the target field `segments`, spec calls it `target_user_segments`, semantically identical, not a conflict). |
| C-22.2 | §22 | An unknown/never-created flag key defaults OFF (never silently on). | MUST | negative | `isEnabled('nonexistent_flag')` → `false`. |
| C-22.3 | §22 | `enabled:false` forces off regardless of `rollout_percent`. | MUST | unit | `enabled:false, rolloutPercent:100` → `isEnabled() === false`. |
| C-22.4 | §22 | Empty `segments` = no segment gating (flag applies to everyone, subject to rollout). | MUST | unit | `segments: []` → segment check is skipped entirely. |
| C-22.5 | §22 | Non-empty `segments` requires the caller's segment list to intersect. | MUST | unit | `segments: ['beta']`, caller `segments: ['beta_testers']` (no overlap) → `false`; caller `segments: ['beta']` → proceeds to rollout check. |
| C-22.6 | §22 | `rollout_percent >= 100` → always on (post segment/enabled checks). | MUST | unit | `rolloutPercent: 100` → `true` for any `userId`. |
| C-22.7 | §22 | `rollout_percent <= 0` → always off. | MUST | unit | `rolloutPercent: 0` → `false` for any `userId`. |
| C-22.8 | §22 | Rollout bucketing is deterministic per `(flagKey, userId)`, same user always gets the same bucket for a given flag. | MUST | unit | `bucketFor('flag_x', 'user_1')` returns the identical number across repeated calls (pure function of `sha256('flag_x:user_1')` first 4 bytes mod 100, worked example: compute the literal sha256 hex of `"photo_ab_testing:11111111-1111-1111-1111-111111111111"`, take first 4 bytes as big-endian uint32, mod 100, and pin that exact number as the regression oracle). |
| C-22.9 | §22 | A percent rollout with no `userId` in context evaluates to NOT enabled (never randomly). | MUST | negative | `isEnabled('flag', { segments: [] })` (no `userId`), `rolloutPercent: 50` → `false`, deterministically, every call. |
| C-22.10 | §22 | Feature flags gate the specific risky features named in §22 (photo A/B testing, behavioral question prompts, new venue categories, new report categories, chat decay, post-date feedback, milestone bounties). | MUST | fixture-data | `KNOWN_FLAGS` enumerates exactly these 7 keys. |

# §23 Database Schema

Table-by-table shape coverage is folded into the section that defines each table's
business meaning (§5 to §22 above); this section instead captures the concrete DB-level
constraints that are themselves independently testable negative cases, grounded in
`db/migrations/001_init.sql`.

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-23.1 | §23.1 | `users.status` is one of exactly `active, suspended, deleted`. | MUST | negative | Insert with an out-of-enum status → Postgres check violation. |
| C-23.2 | §23.1 | `users.trust_score` is clamped 0 to 100 at the DB layer as a backstop to C-6.1.1. | MUST | negative | Insert/update with `trust_score = 101` or `-1` → check violation. |
| C-23.3 | §23.1 | Users must be ≥18 at the DB layer (backstop to C-5.1.6). | MUST | negative | Insert with `birthdate` 17 years ago → `users_min_age` check violation. |
| C-23.4 | §23.4 | Only one photo per user may be `is_primary`. | MUST | negative | `uq_user_photos_one_primary` partial unique index, attempting to mark a 2nd photo primary without first un-setting the first → unique violation (service layer must do this as an atomic swap). |
| C-23.5 | §23.12 | An interest sender/recipient pair cannot have two simultaneously-pending interests in the same direction. | MUST | negative | `uq_interests_pending_pair`, a second `pending` interest from the same sender to the same recipient while the first is still `pending` → unique violation (service must map this to a friendly `conflict`, not a raw 500). |
| C-23.6 | §23.12 | An interest cannot target yourself. | MUST | negative | `interests_not_self` check, `sender_id = recipient_id` → violation. |
| C-23.7 | §23.13 | Exactly one `conversations` row exists per unordered user pair, canonically ordered `user_a_id < user_b_id`. | MUST | negative | `uq_conversations_pair` + `conversations_ordered_pair`, attempting to create a second conversation row for the same pair (in either id order) → violation; service must always canonicalize the pair before insert/lookup. |
| C-23.8 | §23.13 | A conversation cannot be between a user and themself. | MUST | negative | `conversations_not_self` check. |
| C-23.9 | §23.17 | A date proposal cannot target yourself. | MUST | negative | `date_proposals_not_self` check. |
| C-23.10 | §23.17 | `scheduled_end` must be after `scheduled_start`. | MUST | negative | `date_proposals_end_after_start` check, an inverted or equal pair → violation. |
| C-23.11 | §23.18 | Exactly one `payment_holds` row per `(date_proposal_id, user_id)`, proposer's and recipient's holds are distinct rows, never duplicated. | MUST | negative | `UNIQUE (date_proposal_id, user_id)`, a second authorize attempt for the same user on the same proposal must be idempotent (update the existing row / reuse via `idempotencyKey`) rather than insert a duplicate. |
| C-23.12 | §23.20 | Exactly one voucher per date proposal. | MUST | negative | `vouchers.date_proposal_id UNIQUE`, a second ticketing attempt for the same proposal must not create a second voucher. |
| C-23.13 | §23.22 | A report cannot target yourself. | MUST | negative | `reports_not_self` check. |
| C-23.14 | §23.related | A block cannot target yourself, and a given (blocker, blocked) pair is unique. | MUST | negative | `blocks_not_self` + `UNIQUE (blocker_id, blocked_id)`. |

# §24 API Specification

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-24.1 | §24.1 | Auth routes (`register, login, logout, refresh, forgot-password, reset-password`) are reachable without a prior access token. | MUST | integration | Each route responds without requiring `Authorization` header (as appropriate, `logout`/`refresh` need the refresh token itself, not an access token). |
| C-24.2 | §24 (all non-auth groups) | Every other documented route REQUIRES a valid access token. | MUST | negative | Any `/me/*`, `/discovery`, `/interests/*`, `/conversations/*`, `/date-proposals/*`, `/tickets/*`, `/payment-methods*`, `/reports`, `/admin/*` route with no/garbage `Authorization` header → 401 `unauthorized`. |
| C-24.3 | §24.9 | `POST /venue/redeem` requires the `venue_staff` role, not a generic user token. | MUST | negative | Same as C-4.RBAC.2. |
| C-24.4 | §24.13 | Every `/admin/*` route requires the `admin` role. | MUST | negative | Same as C-4.RBAC.1. |
| C-24.5 | §24.10 | `POST /webhooks/payments` validates the processor's webhook signature before trusting the payload. | MUST | negative | A payload with a missing/invalid signature is rejected (not silently processed as a real capture/refund event), relevant when `PAYMENT_PROCESSOR=stripe`; for `fake`, the equivalent contract test lives in the port-contract suite (see test-strategy.md). |
| C-24.6 | §24.2 to §24.12 | Each documented route group (`profile, questions, filters, discovery, interests, conversations, dates, tickets, payments, trust, reports`) has at least one happy-path integration test exercising its documented method+path. | MUST | integration | Route-by-route smoke coverage; not enumerated as 60+ individual rows here, see `test-strategy.md` for how route smoke tests are organized (one file per route group). |

# §25 Background Jobs

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-25.1.1 | §25.1 | Interest-expiry job finds pending interests past `expiresAt`, sets `expired`, frees the outgoing slot. | MUST | state-machine | Same as C-11.4.5/6, run via the actual job function (not the inline service call) against `ManualClock`. |
| C-25.2.1 | §25.2 | Date-proposal-expiry job finds `pending_acceptance` proposals past `accept_expiry_hours`, sets `expired`, releases the proposer hold. | MUST | state-machine | Same as C-14.6.1, run via the job function. |
| C-25.3.1 | §25.3 | Chat cooling/archival job implements the exact 72h/14d/21d thresholds and NEVER archives an `established` conversation. | MUST | state-machine + negative | Same as C-12.6.*/C-12.6.4, run via the job function; a fixture with an `established` conversation 100 days old is untouched by the job. |
| C-25.4.1 | §25.4 | Compatibility-score-refresh job updates `compatibility_scores` nightly or on major answer changes. | SHOULD | integration | Running the job after an answer change updates that pair's `compatibility_scores.score`/`computed_at`. |
| C-25.5.1 | §25.5 | Photo A/B stats job aggregates impressions/accepted-interests and updates photo ranking. | SHOULD | integration | `photo_experiments` counters roll up into a ranking consistent with C-7.3.4. |
| C-25.6.1 | §25.6 | Trust score recalculates on: report, date completed, payment failure, profile change, verification change (exactly these 5 triggers). | MUST | integration | Each of the 5 triggers independently causes a fresh `trust_events`/`trustScore` recompute; an unrelated event (e.g. viewing a profile) does NOT trigger recalculation. |
| C-25.7.1 | §25.7 | Moderation-score job aggregates reports/flags and applies restrictions/shadowbans when thresholds are crossed, fully automatically. | MUST | integration | Same as C-18.5.W1, run via the job function on a schedule/trigger rather than inline. |
| C-25.8.1 | §25.8 | Voucher-expiry job expires vouchers after the configurable period. | MUST | state-machine | Same as C-15.SM.L2. |
| C-25.9.1 | §25.9 | Payment-reconciliation job compares processor webhooks against the local ledger and flags mismatches. | MUST | integration | A fixture where `FakeProcessor`'s intent state and `payment_ledger` are deliberately made to disagree (e.g. a ledger `capture` entry with no matching `_debugGetIntent` captured status) is flagged by the job, not silently ignored. |

# §26 Analytics and Metrics

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-26.1 | §26.1 | All 18 listed core metrics are computable from stored data (not fabricated/estimated). | MUST | fixture-data | Each metric maps to a concrete query over real tables (e.g. "interests accepted" = `count(interests where status='accepted')`). |
| C-26.2 | §26.2 | All 8 listed quality metrics are computable. | MUST | fixture-data | Same pattern, e.g. "date completion rate" = `completed / (completed+no_show+disputed+...)` over a defined denominator, denominator definition should be pinned in the implementation and tested for stability. |
| C-26.3 | §26 | Metrics are tracked internally but NOT exposed publicly (non-admin users never see aggregate metrics). | MUST NOT | negative | No non-admin-reachable route returns any of the §26 metrics; only `GET /admin/analytics/overview` (admin-gated, C-24.4) does. |

# §27 Admin Panel Requirements

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-27.1 | §27 | All 12 listed admin panel capabilities are backed by a real, working admin API endpoint (not just a UI mock). | MUST | integration | Each of the 12 (config editor, flag manager, question manager, venue manager, user lookup, trust event viewer, moderation action viewer, payment ledger viewer, report trend dashboard, date completion dashboard, photo A/B results, funnel analytics) has a corresponding `/admin/*` route from §24.13 (or a documented extension of it) that returns real data. |
| C-27.2 | §27 | Admin actions MUST be logged. | MUST | integration | Same as C-28.6.1. |

# §28 Security Requirements

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-28.1.1 | §28.1 | Passwords are hashed with Argon2id or bcrypt, never stored/compared in plaintext. | MUST | negative | `users.password_hash` never equals the raw submitted password; the hash has a recognizable bcrypt (`$2b$`/`$2a$`) or argon2 (`$argon2id$`) prefix (repo currently depends on `bcryptjs`, consistent with the spec's allowed algorithm list). |
| C-28.2.1 | §28.2 | Access tokens are short-lived. | MUST | unit | `AccessTokenPayload.exp - iat` equals the configured short TTL (`ACCESS_TOKEN_TTL_MINUTES`, default 15 minutes per `env.ts`), never e.g. equal to the refresh TTL. |
| C-28.2.2 | §28.2 | Refresh tokens are rotated (a used refresh token cannot be replayed). | MUST | negative | Calling `POST /auth/refresh` twice with the SAME refresh token: first succeeds and issues a new one, second use of the now-superseded token is rejected, `RefreshTokenPayload.sessionId` stays stable across rotation so reuse-after-rotation is detectable and MAY revoke the whole session family (defensive reuse detection). |
| C-28.3.1 | §28.3 | Sensitive data is encrypted at rest. | MUST | n/a | Infrastructure-level (DB/disk encryption or column-level encryption), **not unit/integration testable in this suite**; flagged as an operational/deployment requirement to verify by configuration review, not automated test. See test-strategy.md "not automatically testable." |
| C-28.3.2 | §28.3 | TLS is used in transit. | MUST | n/a | Infrastructure-level (reverse proxy / load balancer TLS termination), **not testable in this codebase's test suite**; same flag as above. |
| C-28.4.1 | §28.4 | The app MUST NOT store full card numbers anywhere. | MUST NOT | negative | No table/type anywhere in `domain/types.ts`/migrations has a PAN-shaped column; `PaymentMethodSummary` carries only `brand`/`last4`/`processor` token references; a property test scans every string field ever persisted in a payment-adjacent write path and asserts none matches a 13 to 19-digit card-number-shaped regex. **Cross-cutting invariant CC-5.** |
| C-28.4.2 | §28.4 | A PCI-compliant processor is used (via the port abstraction, never raw card handling in-app). | MUST | fixture-data | `PaymentProcessor.authorize` accepts only `paymentMethodToken` (opaque), never `cardNumber`/`cvv`/`expiry` fields, enforced by the `AuthorizeParams` type shape itself. |
| C-28.5.1 | §28.5 | Approximate location only is stored/exposed; exact coordinates are never sent to other users. | MUST NOT | negative | `DiscoveryCandidate` and `GET /profiles/{userId}` never include raw `latitude`/`longitude`; only `approximateDistanceKm` (already fuzzed/bucketed) appears. A property test: two users at slightly different exact coordinates that fuzz to the same rounded distance bucket are indistinguishable from the response alone. **Cross-cutting invariant CC-3.** |
| C-28.6.1 | §28.6 | Admin actions are logged. | MUST | integration | Every `/admin/*` mutating call writes an auditable log entry (actor, action, target, timestamp). |
| C-28.6.2 | §28.6 | Moderation actions are logged. | MUST | integration | Every automated action (§18.4) writes a `moderation_actions` row, this is structural, not an add-on log. |
| C-28.6.3 | §28.6 | Config changes are logged. | MUST | integration | Same as C-21.2.5. |

# §29 Privacy Requirements

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-29.1 | §29 | Account deletion is supported. | SHOULD | integration | An authenticated "delete my account" action succeeds and is irreversible from the user's perspective. |
| C-29.2 | §29 | Data export is supported. | SHOULD | integration | A data-export action returns the user's own stored data in a structured (e.g. JSON) form. |
| C-29.3 | §29 | Consent management is supported. | SHOULD | fixture-data | Consent flags are stored and updatable per user. |
| C-29.4 | §29 | Marketing opt-out is supported. | SHOULD | fixture-data | A `marketingOptOut`-equivalent flag suppresses marketing-channel notifications specifically (not transactional ones). |
| C-29.5 | §29 | Cookie/tracking disclosure is supported. | SHOULD | n/a | Primarily a client/legal-copy concern; not backend-unit-testable beyond "a disclosure-acknowledged flag exists," flagged as largely out of this backend suite's scope. |
| C-29.6 | §29 | Privacy policy acceptance is captured at signup. | MUST | negative | Same underlying field as C-5.1.4 (`termsAccepted`), if privacy policy acceptance is a distinct flag from terms acceptance, it gets its own required-field test identical in shape to C-5.1.4. |
| C-29.7 | §29 | Deletion removes the profile from discovery. | MUST | negative | Post-deletion, the (former) user never appears in anyone's `GET /discovery`. |
| C-29.8 | §29 | Deletion blocks new messages to/from the account. | MUST | negative | Post-deletion, `POST /conversations/{id}/messages` on any of the deleted user's conversations is rejected for both parties. |
| C-29.9 | §29 | Deletion retains financial records as legally required (the ledger is NOT deleted). | MUST | negative | Post-deletion, `payment_ledger` rows referencing the deleted user's `date_proposal_id`s are untouched (append-only invariant CC-4 still holds even across deletion). |
| C-29.10 | §29 | Deletion anonymizes analytics where possible. | SHOULD | integration | Post-deletion, analytics aggregates no longer expose PII (e.g. `email`/`displayName`) tied to that former user, while counts remain stable. |

# §30 Edge Cases

| ID | Spec § | Requirement | M/S/M | Test type | Oracle |
|---|---|---|---|---|---|
| C-30.1.1 | §30.1 | Zero candidates: exact static copy shown ("No candidates currently match your filters. Try widening distance or age range."), plus the reality-dashboard counts. | MUST | fixture-data | `GET /discovery` with an over-constrained filter set returns `items: []` plus `RealityDashboard` populated (not omitted). |
| C-30.1.2 | §30.1 | No fake/synthetic profiles are ever shown to fill an empty grid. | MUST NOT | negative | Every `DiscoveryCandidate` id returned traces to a real `users` row; no synthetic/bot filler logic exists anywhere in `discovery.service.ts`. |
| C-30.2.1 | §30.2 | At the outgoing interest limit, the send action is rejected with the specified static copy, not merely a generic error. | MUST | integration | Same underlying oracle as C-11.2.1, plus the client-facing error carries the specific static-copy template key. |
| C-30.3.1 | §30.3 | A user whose incoming inbox is full is NOT shown in others' discovery (rather than being shown and then failing on send). | MUST | negative | Same as C-10.2.5, the exclusion happens at discovery-list time, not just at send time. |
| C-30.4.1 | §30.4 | An interest accepted while the SENDER is (now) shadowbanned: the resulting conversation MAY remain, but the shadowbanned user's future discovery visibility stays restricted. | MUST | negative | Existing `active`/`established` conversations survive a shadowban applied after acceptance; the shadowbanned user still doesn't appear as a NEW candidate to anyone else (C-10.2.2 still holds). |
| C-30.5.1 | §30.5 | Date proposal accepted but payment fails (either side): proposal is canceled/failed and the OTHER side's hold is released, never one side charged alone. | MUST | integration | Same as C-14.5.2/3, duplicate cross-reference for edge-case traceability. |
| C-30.6.1 | §30.6 | Admin can mark a venue inactive (e.g. after it closes). | MUST | integration | `PATCH /admin/venues/{id}` (or equivalent) sets `active:false`; venue no longer offered as a NEW proposal choice (C-13.1.3). |
| C-30.6.2 | §30.6 | If a date tied to a now-inactive venue was never redeemed, the affected users can be refunded or rescheduled (operational failure doesn't punish users). | MUST | integration | An admin-triggered refund/reschedule path exists for a `ticketed` proposal whose venue went inactive before the scheduled time. |
| C-30.7.1 | §30.7 | Changing hard filters does NOT retroactively affect/erase EXISTING conversations. | MUST NOT | negative | Two users matched under old filters; one changes filters such that the other would now fail them → the existing `active`/`established` conversation is untouched. |
| C-30.7.2 | §30.7 | Future discovery uses the NEW filters. | MUST | integration | A NEW candidate evaluation for that user after the filter change uses the updated filter set, not the one in effect at match time. |
| C-30.8.1 | §30.8 | Changing a "critical field" answer shows a confirmation warning before saving. | SHOULD | integration | `PUT /me/answers` changing a high-weight/`sensitive` question's value returns/requires an explicit confirmation step (e.g. a `confirm:true` flag on retry) rather than silently overwriting on the first call. |
| C-30.9.1 | §30.9 | Reporting a matched user preserves the conversation for automated investigation (it is NOT deleted/hidden from the moderation pipeline). | MUST | negative | `POST /profiles/{userId}/report` (or `/reports`) does not delete/archive the underlying `conversations`/`messages` rows; they remain queryable by the moderation pipeline. |
| C-30.9.2 | §30.9 | The reported user is NEVER notified of the reporter's identity. | MUST NOT | negative | No notification, API response, or moderation-action side-effect visible to the reported user ever contains `reporter_id`/reporter display name/reporter-identifying metadata. **Cross-cutting invariant CC-9.** |

# §31 Implementation Phases (traceability only)

Phase exit criteria are not new independent obligations, each phase's exit criteria are
fully covered by the functional rows above and by the §34 DoD mapping at the end of this
document. Listed here only so per-phase coverage is auditable in one place:

| ID | Phase | Exit criteria covered by |
|---|---|---|
| C-31.1 | Phase 1, Core Account and Profile | C-5.*, C-7.* |
| C-31.2 | Phase 2, Questions and Filters | C-8.*, C-9.* |
| C-31.3 | Phase 3, Discovery and Interests | C-10.*, C-11.* |
| C-31.4 | Phase 4, Chat | C-12.* |
| C-31.5 | Phase 5, Dates and Payments | C-13.*, C-14.*, C-15.* |
| C-31.6 | Phase 6, Trust and Safety | C-6.*, C-18.*, C-19.* |
| C-31.7 | Phase 7, Admin and Analytics | C-21.*, C-22.*, C-26.*, C-27.*, C-28.6.* |

# §32 Recommended Stack (non-functional, out of automated scope)

§32 specifies infrastructure capabilities (relational DB, background jobs, webhooks, file
storage, push, payment auth/capture, admin panel, config mgmt, audit logging) rather than
testable product behavior. Each capability is exercised indirectly by the functional rows
above (e.g. background jobs by §25, webhooks by C-24.5, audit logging by C-28.6.*). No
separate rows are added here to avoid pure duplication; see test-strategy.md for how
infra-shaped requirements (queues, real Stripe, TLS termination) are handled as
port-contract tests instead of full integration tests.

# §33 Major Product Decisions (traceability only)

Every row in the §33 decisions table is the *rationale* for a mechanism already covered by
a specific numbered section above (e.g. "No swipe deck" → §10.1/C-10.1.1; "Capture after
both accept" → §14.2/C-14.2.3; "No threshold hiding" → §10.3/C-10.3.3). No new rows are
needed; this section exists in the spec as narrative justification, not as additional
obligations.

---

# Cross-Cutting Invariants

These properties MUST hold across every operation in the system, not just the section
that first introduces them. Each should have its own dedicated property/negative test in
addition to being implied by the section-specific rows above, because a regression in any
ONE of these is exactly the kind of bug that a single-feature test suite misses.

| ID | Invariant | Proven by (primary rows) | Suggested standalone test |
|---|---|---|---|
| CC-1 | No candidate who fails either party's hard filters is EVER returned by discovery, regardless of compatibility score, trust level, or any other sorting input. | C-9.1.2, C-10.3.3, C-16.1.1, C-1.3, C-1.17 | Property test: generate random filter sets + random candidate pools; assert the intersection of "returned by discovery" and "fails a hard filter" is always empty. |
| CC-2 | No user is ever CHARGED (captured) for a date unless BOTH proposer's and recipient's holds were successfully authorized first, and capture of one side never proceeds/persists without the other succeeding too. | C-14.2.3, C-14.3.1, C-14.5.2, C-14.5.3 | Exhaustive fault-injection matrix over `{proposer authorize, recipient authorize, proposer capture, recipient capture} × {succeed, fail}` (16 combinations), for every combination where NOT both captures succeed, assert **zero** `payment_holds` rows end in `status='captured'` that don't have a captured counterpart, and the ledger never contains an orphaned `capture` entry for one user with no matching entry for the other. |
| CC-3 | No ticket/voucher exists before both payments are captured. | C-14.4.1 | Property test: for every `date_proposals.status` NOT in `{charged, ticketed, completed, completed_unverified, no_show, disputed}` (i.e. earlier or failed states), no `vouchers` row references that proposal. |
| CC-4 | The payment ledger is append-only and balanced: every `capture` has a corresponding `authorization`; every `refund` doesn't exceed its `capture`; sum of `authorization − release` for a still-open hold matches the hold's `amount_cents`; no row is ever updated/deleted. | C-14.8.3, C-23.11, C-23.12, C-29.9 | Property test over generated payment event sequences: replaying every ledger entry for a given `date_proposal_id` never leaves an unaccounted-for cent (sum of captures − sum of refunds ≥ 0, sum of authorizations ≥ sum of captures + sum of releases for that hold). |
| CC-5 | No full card number (or CVV) is ever persisted, logged, or returned anywhere in the system. | C-28.4.1, C-15.2.2, C-4.2.6 | Property test / static scan: every string ever written to the DB or logger in the payment path is checked against a PAN-shaped regex; port types (`AuthorizeParams` etc.) structurally cannot carry a card number field. |
| CC-6 | An `established` conversation is NEVER archived, put into cooling, or otherwise decayed by any background job, ever, no matter how much time passes. | C-12.6.4, C-12.7.1, C-25.3.1 | Property test: run the chat-decay job repeatedly with `ManualClock` advanced arbitrarily far past `firstDateCompletedAt`; `status` stays `'established'` on every run. |
| CC-7 | Every automated moderation action (warning/restriction/shadowban/suspension) and its resolution (appeal) is reachable through fully automated code paths, no code path requires an admin action to complete. | C-18.1.1, C-4.3.7, C-18.6.4 | Integration test suite for §18 as a whole runs with zero `/admin/*` calls in the happy/unhappy paths; a "no admin credentials constructed anywhere in this test file" lint/assertion. |
| CC-8 | A config key marked `scope:'snapshot'` never changes the effective rule for an object created before the config change; a config key marked `scope:'live'` always reflects the current value for every object, past or present. | C-14.1.4, C-21.3.3 | Property test: for each of the 7 snapshot keys, create object → change config → re-derive the rule from the object's own `policySnapshot`/`escrowAmountCents` (not a fresh config read) → unaffected. For each `live` key, two objects created before/after a config change both observe the NEW value when the rule is evaluated live (e.g. `chat.active_limit`). |
| CC-9 | A reported user is never informed, directly or indirectly, of who reported them. | C-30.9.2 | Property test: for every API response and notification reachable by the reported user after a report is filed, no field/derived value equals or leaks the reporter's id/handle. |
| CC-10 | Exact GPS coordinates never leave the API boundary to any OTHER user (self viewing own profile is fine). | C-7.1.2, C-28.5.1 | Property test: serialize every response shape reachable by user B about user A; assert no field is A's raw `latitude`/`longitude`. |
| CC-11 | Money is always minor-unit integers (cents); no floating-point cent values are ever computed or stored. | C-14.1.2, C-14.7.W6 | Static/property check: every `*Cents`/`amount_cents` value produced by any computation is `Number.isInteger(x)` (or a `bigint`) at the point it's persisted. |
| CC-12 | Time-based transitions (expiry, decay, voucher expiry) are driven exclusively by the injected `Clock`, never by `Date.now()`/`new Date()` directly, so tests are fully deterministic. | all §25 rows, C-11.4.5, C-14.6.1, C-12.6.* | Static check: no `src/**` file outside `src/lib/time.ts` calls `Date.now()`/`new Date()` with zero args. |

---

# Open Questions / Spec Conflicts

These are places where the spec is ambiguous, internally inconsistent, or silent on a
detail a test needs a concrete oracle for. Each carries this plan's recommended
resolution, used as the oracle throughout the rows above, plus the reasoning, so the
test author has one answer to code against instead of re-litigating it mid-implementation.
Product should review these; until they do, treat the recommendation as binding for the
test suite so the suite is internally consistent.

**OQ-1, DECIDED, IMPLEMENTED.** Product confirmed the recommendation below: the refund
cutoff (and every other score/threshold comparison in the codebase, see OQ-10) is
inclusive (`>=`). `dateProposal.service#cancelDateProposal` already computes
`isFullRefund = hoursUntilDate >= cutoffHours`, matching this exactly; no code change was
needed, only an audit (see the decision-layer final report) confirming every threshold
comparison in `src/services/*` already reads this way and the boundary tests
(C-14.7.W2, `tests/unit/dateProposal.test.ts`'s "exactly 24h" case) already assert the
inclusive reading.

**OQ-1, §14.7 boundary at exactly the refund cutoff.** The spec defines "more than 24
hours before" (full refund) and "less than 24 hours before" (no refund) but never states
what happens at exactly 24h00m00s, neither bucket's wording covers equality.
*Recommendation:* treat the cutoff as inclusive of the full-refund side (`hoursBefore >=
full_refund_cutoff_hours` → full refund), consistent with how §6.1's own level bands are
written as inclusive lower bounds ("70 to 89" includes 70). Test: C-14.7.W2.

**OQ-2, §16.2 "too few shared answered questions" default: 0 *or* neutral?** The spec
literally says "score defaults to 0 or neutral", these are different values (0.0 vs.
something like 0.5) with different sort implications (0 sinks a data-sparse profile to the
bottom; "neutral" keeps it mid-pack). *Recommendation:* default to `0`, on the reasoning
that a candidate with no comparable answered questions has NO evidence of compatibility,
not neutral evidence, and §16.1's "sorting is preference, filters are the boundary"
framing means sinking low-evidence profiles in sort order (never removing them, since
hard filters still gate visibility per CC-1) is the safer interpretation. This should be a
single named config constant (e.g. `compatibility.no_data_default_score`) so product can
flip it without touching code. Test: C-16.2.W6.

**OQ-3, DECIDED, IMPLEMENTED.** Product confirmed the recommendation below, with concrete
numbers: `no_show` fires automatically when `date.no_scan_confirmation_hours` (72h,
unchanged) closes with ZERO attendance confirmations and no venue scan
(`dateProposal.service#sweepTicketedCompletionWindows`), refund follows the FROZEN
policy snapshot's `date.no_show_refund_percent`, applied symmetrically to both parties
(nobody proved attendance, so there's no "the other party showed up" fact to make anyone
whole on). `disputed` (exactly one confirmation) auto-resolves after a new
`date.dispute_auto_resolve_hours` config key (default 72h, snapshot-scoped) via
`disputeResolution.service#resolveDueDisputes`: an implicit `no_show`-category report is
filed against the non-confirming party through the real `report.service#submitReport` (the
confirming party is impersonated as reporter, see that module's header), which drives the
existing `moderation.service` scoring pipeline unmodified, plus a direct
`trust.service#recordTrustEvent`/`recalculateTrustScore` call. `disputed` itself stays
terminal (§13.3), only `date_proposals.dispute_resolved_at` marks the automated
resolution as done, idempotently. Both sweeps are pure functions of `Ctx`/`ctx.clock`, safe
to re-run, with no `admin` actor anywhere in either path (spec §18.1), see
`tests/unit/dateOutcomeSweep.test.ts`. Full details, including the two new notification
event types this needed, are in the decision-layer final report.

**OQ-3, What actually sets `date_proposals.status = 'no_show'`, and how is `'disputed'`
resolved?** `no_show` is a listed status (§13.3) and feeds the no-show refund config
(§14.7) and trust negative factors (§6.2) and report category (§18.3), but no section
of the spec states the rule that PRODUCES it. Likewise §15.4 says a `disputed` proposal
gets "automated handling... according to policy" without naming that policy anywhere.
*Recommendation:* (a) `no_show` is entered automatically when the no-scan-confirmation
window (`date.no_scan_confirmation_hours`, default 72h after `scheduledEnd`) closes with
**zero** confirmations from either user and no venue scan occurred (distinct from
`disputed`'s "exactly one confirmed" case); (b) `disputed` is resolved automatically by
the same §18.5 report-scoring machinery, treating an unresolved dispute past a configured
cooldown as an implicit `no_show` report against the non-confirming party, feeding trust
recalculation (§25.6) rather than staying `disputed` forever. This needs a new config key,
e.g. `date.dispute_auto_resolve_hours`. Flag prominently for product, this is a real gap,
not just a wording nit.

**OQ-4, §6.4 "Limited: Send interests = limited" vs. §12.3 link-limit table: what
NUMBER is "limited"?** The §6.4 restriction table uses the word "limited" for Limited-tier
outgoing interests without a number, while §21.4/§11.2 give ONE global
`interest.outgoing_pending_limit` (5) with no separate lower cap for Limited-trust users.
This is the conflict the task specifically asked to check (§6.4 restriction table vs.
§12.3 link limits), generalized: **§6.4 implies trust-tiered numeric caps exist for
BOTH interests and links, but §21.4's config registry only actually parameterizes a
trust-tiered cap for LINKS (`chat.max_links_per_hour_low_trust` vs.
`..._standard_trust`), not for interests.** *Recommendation:* add a second config key,
`interest.outgoing_pending_limit_limited_tier` (suggested default: 2, i.e. 40% of the
standard 5), used only for Limited-trust users, so §6.4's "limited" cell has a concrete
number and passes C-6.4.1. Until product picks a number, C-6.4.1 should assert only the
*relative* claim ("Limited's effective cap < Standard's cap"), not a specific value.

**OQ-5, §14.5 "capture fails after authorization: release ALL holds", but what if ONE
side's capture already succeeded before the other's failed?** §14.2 says capture happens
for "both" once both are authorized, implying a single atomic step, but `FakeProcessor`
(and any real processor) executes two separate `capture` calls that can't be perfectly
atomic. If proposer's capture SUCCEEDS and recipient's capture then FAILS, "release all
holds" can't apply to the proposer's hold anymore, it's already `captured`, not
`authorized`; releasing means refunding, not canceling. *Recommendation:* the capture
step MUST be implemented as: attempt capture A, only attempt capture B if A succeeded; if
B fails, **refund** A (not cancel, the money already moved) via `PaymentProcessor.refund`,
producing a `refund` ledger entry, not a `release` one, for the side that had already been
captured. Document this explicitly in the date-proposal service so the ledger `type`
recorded for the already-captured side's reversal is correct. Test: C-14.5.3.

**OQ-6, §14.7 refund rounding when a percent doesn't divide evenly into cents.** Not
addressed anywhere in the spec. *Recommendation:* floor (round down) the refund amount, so
the platform never pays out fractional-cent-rounded-up refunds; document as
`Math.floor(amountCents * percent / 100)`. Test: C-14.7.W6.

**OQ-7, §6.1 "not shown as an exact number unless product decides" is a decision point
the spec explicitly punts.** *Recommendation:* default OFF (never show the raw score);
gate exposure behind an explicit config/flag (e.g. `trust.expose_raw_score`, default
`false`) so the default behavior is testable and the override path is too. Test: C-6.1.3.

**OQ-8, DECIDED, IMPLEMENTED, reversed from this document's original "out of scope"
recommendation.** Product decided venue settlement IS in scope: built in
`src/services/venueSettlement.service.ts` (new file), `db/migrations/007_decisions.sql`
(new `venue_settlements` table; `payment_ledger.type` extended with `venue_payout`, plus a
new nullable `venue_id` column since a venue payout pays a venue, not a user, see the
migration's own comments). Settlement is earned ONLY by a venue-VERIFIED completion
(`status = 'completed'` AND a `venue_redemptions` row exists), `completed_unverified`,
`no_show`, `canceled`, `refunded`, and `disputed` are excluded by construction (the
settlement-candidate query filters on exactly that), proven negatively for each status in
`tests/unit/venueSettlement.test.ts`, which was this decision's whole point (§15.4). Payout
math is integer-only: `venuePayoutCents = Math.floor(grossCents * marginPercent / 100)`,
`platformCents = grossCents - venuePayoutCents`, so the two always sum to gross exactly,
unit-tested directly, including the non-exact-percent rounding case (gross=1999,
margin=33% -> 659/1340). Settlement is idempotent (one settlement row per date proposal,
ever, `UNIQUE` + `ON CONFLICT DO NOTHING`). The job body is `settleDueVenuePayouts(ctx)`;
it is not registered anywhere in `src/jobs/**` by this decision layer, see the final
report for the exact name the jobs owner should schedule.

**OQ-8, §15.4's "does not automatically settle venue payment" implies a venue-payout
concept that is never defined anywhere else in the spec.** There is no `venue_payout`
`LedgerEntryType` (§14.8's 6 types are user-facing: authorization/capture/release/
refund/dispute/chargeback), no venue-settlement schema, and no API route for it (§24, §27
have no venue-payout endpoint). This looks like a genuine spec gap: venues presumably get
paid their `margin_percent` (§13.2/§23.16) of the escrow eventually, but the mechanism,
timing, and ledger representation are entirely unspecified. *Recommendation:* treat venue
settlement as explicitly OUT OF SCOPE for the MVP backend under test (no code path
attempts it), and the only testable assertion is the negative one already captured in
C-15.4.2 (`completed_unverified` doesn't trigger *something that doesn't exist*, so this
is trivially satisfiable, but flag to product that "venue payment" is a real unbuilt
feature, not just an untested one).

**OQ-9, §16.2 `importance_multiplier = 1 + abs(partner_answer - 3) * 0.25` references
"partner_answer" singular, but the formula section computes satisfaction in BOTH
directions per question (A→B and B→A), each with its own partner_answer.** Is
`question_weight` computed once per question (using which side's partner_answer?) or
per-direction? *Recommendation:* average the two directions' multipliers into one
`question_weight` per question (used in C-16.2's worked example), this keeps the
formula symmetric (compatibility(A,B) === compatibility(B,A)), which the spec's framing
("mutual filter passing," "pair_satisfaction") strongly implies is an intended property.
Note the arithmetic identity proven in C-16.2.W5 means the polarity-transform ambiguity
that would otherwise compound this doesn't actually matter numerically.

**OQ-10, DECIDED, IMPLEMENTED.** Product confirmed the recommendation below: every
threshold in the codebase is inclusive (`>=`), overriding §18.5's literal "exceeds".
`moderation.service#applyThresholds` already compares `score >= restrictionThreshold`
(and likewise for shadowban/suspension/warning); `trust.service#levelForScore` already
compares `clamped >= bounds[...]` for all three band boundaries; `dateProposal.service`'s
refund cutoff is covered under OQ-1. A full audit of every threshold-shaped comparison in
`src/services/*.ts` (grep for `>=`/`>`/`<` near cutoff/threshold/`_min` identifiers) found
nothing using the exclusive reading, so this decision required no code change, only
confirming and documenting it. Boundary tests already exist and assert the inclusive side
at every named boundary (score 50/80 in `tests/unit/moderation.test.ts`, 24h in
`tests/unit/dateProposal.test.ts`, trust bands 40/70/90 in `tests/unit/trust.test.ts`),
none needed to change. See the decision-layer final report for the full audit trail.

**OQ-10, §18.5 "If report score EXCEEDS threshold" (strict `>`) vs. the natural
"threshold" convention used everywhere else in the spec (inclusive `>=`, e.g. §6.1's
level bands, §14.7's cutoff).** Taken completely literally, a score of exactly 50 (the
default `moderation.auto_restriction_score`) would NOT trigger restriction under "exceeds"
(strict >), but WOULD under the more common "at or above threshold" reading.
*Recommendation:* use inclusive (`>=`) for consistency with every other threshold in the
spec (see OQ-1's same reasoning) and because a config value literally named
`..._score` reads most naturally as "the score at which this kicks in." Test: C-18.5.W1,
using the score=50/80/95 boundary rows.

**OQ-11, De-escalation: can automated recalculation ever REDUCE a user from suspension
back down as their score improves/ages out, without an appeal?** Not stated anywhere.
*Recommendation:* no, automated recalculation only escalates; the ONLY path back down is
the explicit, spec-defined appeal flow (§18.6). This avoids a scenario where a
report-brigading attack that later "ages out" silently un-suspends a genuinely bad actor
with no review step at all, and it matches the spec's framing of appeals as the mechanism
"if appeal passes, restore account" (§18.6), restoration is explicitly an appeal-outcome,
never a side effect of the score simply drifting back down. Test: C-18.5.W2.

**OQ-12, §21.2 "environment scope" for config: no `environment` column appears in the
§23.25/§21.1 `config_entries` schema.** Either this is satisfied structurally by running
separate DB instances per environment (dev/test/prod), or the schema is genuinely missing
a column the spec asks for. *Recommendation:* treat as satisfied by deployment topology
(one DB per environment) rather than an in-table `environment` column, since nothing else
in the spec's schema section (§23) mentions such a column either, flag to product as a
possible spec/schema mismatch, but do not block the test suite on it; C-21.2.4 is marked
`fixture-data`/structural rather than requiring a literal column assertion.

**OQ-13, §12.3 link-rate limit for standard trust (5/hour): what happens on the 6th
link, is the MESSAGE blocked, or only the link's clickability?** §12.5/§19.3 are explicit
that messages are never blocked for containing a link/handle; but §12.3 frames
`chat.max_links_per_hour_standard_trust` as a "limit," which could mean either "6th
link-bearing message is rejected" or "6th link renders non-clickable even for a
standard-trust user, same as if they were low-trust." *Recommendation:* the latter, the
message still sends (never blocked, consistent with §12.5/§19.3's explicit "do not block"
principle), but the 6th-and-later link within the rolling hour is rendered non-clickable
regardless of trust tier, exactly like a Limited-trust user's link. This keeps §12.3 and
§12.5/§19.3 mutually consistent instead of contradicting on whether links can ever block
a send. Reflected in C-12.3.3.

---

# Definition of Done (§34), Coverage Mapping

Each of the spec's 20 DoD items, mapped to the checklist IDs that collectively prove it.
An item counts as "covered" only if its mapped IDs include at least one positive
(happy-path) proof AND, where the item has a natural negative counterpart, at least one
negative test too.

| DoD # | Item | Proven by |
|---|---|---|
| 1 | Register without phone or government ID | C-5.1.*, C-5.2.1, C-5.3.1, C-1.11, C-1.12 |
| 2 | Answer dual 5-point questions | C-8.1.1, C-8.1.2, C-8.2.1 |
| 3 | Hard filters strictly control discovery | C-9.1.1, C-9.1.2, C-9.2.1, CC-1 |
| 4 | Discovery grid sorts by compatibility | C-10.3.1, C-10.3.2, C-16.2.W1 to W3 |
| 5 | Users can send limited interests | C-11.1.*, C-11.2.1, C-11.2.4 |
| 6 | Incoming interests capped and expire | C-11.2.2, C-10.2.5, C-11.4.SM.L3, C-25.1.1 |
| 7 | Mutual interest opens chat | C-11.4.SM.L1, C-12.1.1 |
| 8 | Chat supports free-text after match | C-12.2.1, C-11.3.2 |
| 9 | Text analysis flags risky patterns without blocking normal messages | C-19.3.1 to 5, C-12.5.1, C-12.4.2 |
| 10 | Propose dates with structured venues | C-13.1.1 to 3, C-13.2.1 |
| 11 | Proposer hold authorized on proposal | C-14.2.1 |
| 12 | Acceptor hold authorized on acceptance | C-14.2.2 |
| 13 | Both payments capture only after both holds succeed | C-14.2.3, C-14.3.1, CC-2 |
| 14 | Ticket issued only after successful capture | C-14.2.4, C-14.4.1, CC-3 |
| 15 | Venue redemption marks date completed | C-15.3.2, C-15.3.3, C-15.SM.L1 |
| 16 | Post-date chat becomes established | C-15.3.4, C-12.6.4, C-12.7.* |
| 17 | Automated moderation works without human moderators | C-18.1.1, C-18.1.2, C-4.3.7, CC-7 |
| 18 | Trust score visible with actionable reasons | C-6.3.1, C-6.3.2, C-6.3.3 |
| 19 | Admin can change core variables without code deployment | C-4.3.1, C-21.2.1 to 5, C-21.4.* |
| 20 | All payment events recorded in an immutable ledger | C-14.8.1, C-14.8.2, C-14.8.3, CC-4 |
