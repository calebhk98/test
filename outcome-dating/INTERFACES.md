# INTERFACES.md — Foundation Layer Contract

This is the contract for the parallel implementation phase. Every file
under `src/services/**/*.service.ts` typechecks today with bodies that
`throw new NotImplementedError(...)`. Each owning agent replaces only the
bodies in their own files — signatures, exported types, and JSDoc are
**frozen** unless a cross-cutting change is coordinated with everyone
whose module calls the one being changed.

Run `npx tsc --noEmit` and `npm test` before and after your changes; both
must stay green.

## How to read this document

- **Ctx** (`src/lib/ctx.ts`) is the first argument to almost every
  function: `{ db, clock, config, flags, logger, actor, payments, media }`.
  Use `ctx.actor` to know who's calling (`user` / `venue_staff` / `admin`
  / `system`), never a bare `userId` parameter, for "the current caller."
  A second, explicit id parameter (e.g. `targetUserId`, `dateProposalId`)
  is always *someone/something else*.
- Domain types (`User`, `Interest`, `DateProposal`, ...) live in
  `src/domain/types.ts`, not in the service files themselves — see that
  file's header for why (avoids import cycles across 24 files owned by 5
  agents).
- "May call" lists the service modules a module is allowed to import
  functions from. An arrow the table doesn't list is not sanctioned —
  if you find you need one, it's a signal the boundary needs discussion,
  not a silent addition.

## Module table

| Module | Agent | Exported functions | Spec sections | May call |
|---|---|---|---|---|
| `auth.service` | A | `register`, `login`, `logout`, `refresh`, `forgotPassword`, `resetPassword`, `verifyAccessToken` | §5, §24.1, §28.1-2 | — (leaf; HTTP layer calls it) |
| `profile.service` | A | `getMyProfile`, `updateMyProfile`, `getPublicProfile`, `computeProfileCompleteness` | §7.1, §9.4, §24.2, §28.5 | `discovery` (block check in `getPublicProfile`) |
| `photo.service` | A | `uploadPhoto`, `deletePhoto`, `listMyPhotos`, `setPrimaryPhoto`, `reorderPhotos`, `findDuplicateOwners` | §7.2, §18.2, §24.2 | `ctx.media` (port) |
| `photoExperiment.service` | A | `recordImpression`, `recordInterestSent`, `recordInterestAccepted`, `listStatsForUser`, `getMyPhotoTestResults`, `refreshAllRecommendations`, `approveRecommendation`, `rejectRecommendation` | §7.3, §24.2, §25.5 | `photo` (photo ids), `ctx.flags` |
| `question.service` | B | `listActiveQuestions`, `getMyAnswers`, `putMyAnswers`, `adminListQuestions`, `adminCreateQuestion`, `adminUpdateQuestion` | §8, §24.3, §27 | `compatibility` (`refreshScoresForUser` after answer change) |
| `filter.service` | B | `getMyFilters`, `updateMyFilters`, `evaluateFilter` (pure), `passesMutualFilters`, `countUsersMatchingMyFilters`, `countUsersWhoseFiltersIMatch` | §9, §24.4 | — (leaf) |
| `compatibility.service` | B | `computePairScore` (pure), `getScore`, `getScoresForCandidates`, `refreshScoresForUser`, `refreshAllScores` | §16, §25.4 | — (leaf; reads `answers`/`questions` directly) |
| `discovery.service` | B | `getDiscoveryGrid`, `getRealityDashboard`, `recordDiscoveryImpression`, `isProfileVisibleTo`, `blockUser`, `unblockUser`, `listBlockedUsers`, `isEitherBlocked` | §9.3, §10, §16.1, §16.3, §24.5 | `filter`, `compatibility`, `trust`, `moderation`, `photoExperiment` |
| `behavioralPrompt.service` | B | `detectPatternsForUser`, `listPendingSuggestions`, `respondToSuggestion` | §17, §22 | `question` (`putMyAnswers`, never `answers` directly), `ctx.flags` |
| `interest.service` | C | `sendInterest`, `listOutgoing`, `listIncoming`, `acceptInterest`, `declineInterest`, `cancelInterest`, `expireDuePendingInterests` | §11, §21.3, §24.6, §25.1 | `conversation` (`getOrCreateConversation`), `notification`, `photoExperiment`, `discovery` (capacity check), `ctx.config` |
| `conversation.service` | C | `getOrCreateConversation`, `listMyConversations`, `getConversation`, `archiveConversation`, `establishConversation`, `runChatDecayJob` | §12.1, §12.6-7, §23.13, §24.7, §25.3 | `notification` |
| `message.service` | C | `sendMessage`, `listMessages`, `markRead`, `countMessagesInLastHour`, `countLinksInLastHour` | §12.2-5, §24.7 | `textscan`, `trust` (`canSendClickableLinks`), `conversation` (status check), `notification` (`notify` for the existing `safety_notice` banner; `notifications/index#enqueueNotification` for `message_received`, added by the wiring build — see docs/ux-api-review.md §13's finding that new-message notifications never fired because this edge was not yet permitted) |
| `textscan.service` | C | `scanText` (pure), `PATTERN_GROUPS` (const) | §12.4, §18.2, §19.3-4 | — (leaf, no I/O) |
| `notification.service` | C | `notify`, `listMyNotifications`, `markNotificationRead`, `deliverPending`, `NOTIFICATION_TEMPLATES` (const) | §20 | — (leaf; every module calls *into* this one) |
| `venue.service` | D | `listActiveVenues`, `getVenue`, `listAvailableTimeSlots`, `adminListVenues`, `adminCreateVenue`, `adminUpdateVenue` | §13.2, §24.8, §27, §30.6 | — (leaf) |
| `dateProposal.service` | D | `proposeDate`, `acceptDateProposal`, `declineDateProposal`, `cancelDateProposal`, `confirmAttendance`, `submitPostDateFeedback`, `getDateProposal`, `expireDuePendingProposals`, `markNoShow`, `markCompletedByRedemption` | §13, §14, §15.4, §21.3, §24.8, §25.2 | `venue`, `payment`, `voucher`, `conversation`, `notification`, `trust` |
| `payment.service` | D | `addPaymentMethod`, `listPaymentMethods`, `deletePaymentMethod`, `getDefaultPaymentMethod`, `authorizeHold`, `captureHold`, `releaseHold`, `refundHold`, `handleProcessorWebhook` | §14, §24.10, §28.4 | `ledger`, `ctx.payments` (port) |
| `ledger.service` | D | `recordEntry`, `listEntriesForDateProposal`, `listEntriesForUser`, `reconcileWithProcessor` | §14.8, §25.9, §27 | `ctx.payments` (port, reconciliation only) |
| `voucher.service` | D | `issueVoucher`, `getVoucher`, `listMyVouchers`, `verifyQrPayload` (pure), `expireDueVouchers`, `cancelVoucher`, `markRedeemed` | §15.1-2, §23.20, §24.9, §25.8 | `src/lib/signing.ts`, `src/lib/ids.ts` |
| `redemption.service` | D | `redeemByStaff`, `redeemBySelf`, `getRedemptionHistory` | §4.2, §15.3, §24.9 | `voucher`, `dateProposal`, `conversation`, `trust` |
| `trust.service` | E | `getMyTrustSummary`, `listMyTrustEvents`, `recordTrustEvent`, `recalculateTrustScore`, `levelForScore`, `canSendClickableLinks` | §6, §24.11, §25.6 | `notification` (level-change event) |
| `moderation.service` | E | `recordAutomatedFlag`, `computeModerationScore`, `applyThresholds`, `listModerationActions`, `isVisibleInDiscovery`, `runModerationRecalculation` | §18 (ex. §18.6), §24.13, §25.7 | `report` (`scoreReport`), `trust`, `notification` |
| `report.service` | E | `submitReport`, `listReportsAgainst`, `countRecentReportsAgainst`, `scoreReport` | §18.3, §18.5, §24.12, §30.9 | `moderation` (`recordAutomatedFlag`, after submit) |
| `appeal.service` | E | `submitAppeal`, `resolveAppeal`, `getMyLatestAppeal`, `checkCooldownElapsed` | §18.6, §24.11 | `moderation` (read the appealed action), `trust` |
| `payments/processor.port` + `fake.processor` + `stripe.processor` | *(shared infra — implemented, not stubbed)* | `PaymentProcessor.{authorize,capture,cancel,refund}` | §14, §28.4 | — |
| `media/moderation.port` + `stub.adapter` | *(shared infra — implemented, not stubbed)* | `ImageModerationPort.analyzePhoto` | §7.2, §18.2 | — |

Reading the "may call" column as a graph, the only edges are:

```
discovery ─▶ filter, compatibility, trust, moderation, photoExperiment
interest ─▶ conversation, notification, photoExperiment, discovery
message ─▶ textscan, trust, conversation, notification
dateProposal ─▶ venue, payment, voucher, conversation, notification, trust
redemption ─▶ voucher, dateProposal, conversation, trust
moderation ─▶ report, trust, notification
appeal ─▶ moderation, trust
payment ─▶ ledger
question ─▶ compatibility
behavioralPrompt ─▶ question
photoExperiment ─▶ photo
profile ─▶ discovery
report ─▶ moderation
```

No cycles. `notification`, `textscan`, `ledger`, `filter`, `compatibility`,
`conversation`, `venue`, `trust` (mostly), and `voucher` are leaves or
near-leaves — safe for anyone to depend on.

## Signature decisions parallel agents must know

1. **`Ctx` is the DI container, not just db+clock+config+flags+logger+actor.**
   It also carries `payments: PaymentProcessor` and `media:
   ImageModerationPort` (`src/lib/ctx.ts`) — the two external-integration
   ports the spec names explicitly (§14, §7.2). `photo.service.ts` calls
   `ctx.media.analyzePhoto`; `payment.service.ts` calls
   `ctx.payments.{authorize,capture,cancel,refund}`. Nobody should import a
   concrete adapter (`FakeProcessor`, `StripeProcessor`,
   `StubMediaModerationAdapter`) directly — always go through `ctx`, so
   tests can substitute freely per-call.

2. **Transactions compose via `withDb(ctx, db)`.** `src/db/tx.ts`'s
   `withTransaction(fn)` hands `fn` a `DbClient` bound to one Postgres
   transaction; wrap it in `withDb(ctx, db)` and pass that `Ctx` into every
   service call that must share the transaction. Concretely:
   `interest.acceptInterest` doing "flip interest to accepted + create a
   conversation" is `withTransaction(db => { const txCtx = withDb(ctx,
   db); await ...; return conversation.getOrCreateConversation(txCtx, ...);
   })`. The multi-service flows below (voucher redemption, date proposal
   capture) all follow this pattern — a single `withTransaction` at the
   top of the outermost function, all nested service calls sharing that
   `db` via `withDb`.

3. **IDs are plain `string` (uuid), not branded types.** Chosen for lower
   friction across ~180 stub function signatures; the cost is that
   `passesMutualFilters(ctx, userId, candidateId)` won't catch a
   swapped-argument bug at compile time. Be deliberate about parameter
   *names* (always `userId`/`candidateId`/`dateProposalId`, never a bare
   `id`) since that's the only guard rail.

4. **Money is `number` in TypeScript, `bigint` in Postgres, always
   `*Cents`.** Never introduce a float or a `numeric` column for money.
   `escrowAmountCents`, `amountCents`, `capturedAmountCents` etc. are all
   integers; multiply/divide by 100 only at a display boundary that is
   explicitly not this codebase's concern yet.

5. **Config policy snapshots are captured once, at creation, never
   re-read.** `interest.sendInterest` and `dateProposal.proposeDate` each
   call `ctx.config.snapshotPolicy(INTEREST_POLICY_KEYS |
   DATE_PROPOSAL_POLICY_KEYS)` (from `src/config/config.service.ts`) and
   store the *result* in the row's `policy_snapshot` jsonb column. Every
   later expiry/refund calculation on that row reads
   `row.policySnapshot[...]`, never `ctx.config.get(...)` again. This is
   what makes spec §21.4's "existing keep original" rows behave correctly
   with zero extra bookkeeping.

6. **`conversations` canonical ordering.** `user_a_id < user_b_id` is a DB
   CHECK constraint. `conversation.getOrCreateConversation(ctx, userAId,
   userBId)` must sort its two arguments before querying/inserting — order
   of the *arguments* is not meaningful, only the stored row's order is.

7. **Blocking/reporting live under `discovery`/`report`, not a standalone
   `block.service.ts`.** The spec's own API layout (§24.5) puts `POST
   /profiles/{userId}/block` next to discovery routes; there was no
   6th agent-B or extra agent-E module requested, so blocking got folded
   into `discovery.service.ts` (visibility is already discovery's concern)
   and reporting stayed its own file per the task's module list.

8. **`redemption.service.ts` — not `voucher.service.ts` — is the
   transaction owner for "scan ticket → complete date".** `voucher.markRedeemed`
   and `dateProposal.markCompletedByRedemption` are narrow,
   single-purpose functions that `redemption.redeemByStaff`/`redeemBySelf`
   call in sequence inside one `withTransaction`, alongside
   `conversation.establishConversation` and two
   `trust.recordTrustEvent` calls (one per participant). Neither
   `voucher.service.ts` nor `dateProposal.service.ts` calls the other
   directly — this keeps that dependency graph acyclic (see the graph
   above).

9. **Actor-scoped functions trust `ctx.actor`, not a parameter.**
   `redemption.redeemByStaff` reads `ctx.actor.venueId` (requires
   `ctx.actor.type === 'venue_staff'`); it does not take a `venueId`
   parameter for "which venue is redeeming" — that would let a caller
   pass a venue they don't work for. Use `requireUserActor(ctx)` from
   `src/lib/ctx.ts` as the standard guard at the top of user-only
   functions.

## Invariants (violating any of these is a bug, not a design choice)

- **Hard filters are never overridden by scoring.** `filter.passesMutualFilters`
  is a hard gate `discovery.getDiscoveryGrid` calls before compatibility
  scoring ever runs; compatibility only sorts the already-filtered set
  (spec §9.1, §16.1).
- **No compatibility threshold hides users.** `discovery.getDiscoveryGrid`
  must never drop a candidate for having a low score — only filters,
  blocks, moderation visibility, and capacity limits remove a candidate
  (spec §10.3).
- **No user is charged unless both holds authorize.**
  `dateProposal.acceptDateProposal` calls `payment.captureHold` for either
  side only after confirming both `payment_holds` rows reached
  `authorized` (spec §14.3). `payment.service.ts` itself exposes no
  "capture both" convenience that could be misused to skip that check.
- **A ticket exists only after capture.** `voucher.issueVoucher` is called
  by `dateProposal.acceptDateProposal` only after both
  `payment.captureHold` calls return `captured`, in the same transaction
  as `status = 'ticketed'` (spec §14.4).
- **No LLM text anywhere.** `notification.service.ts`'s
  `NOTIFICATION_TEMPLATES` and `textscan.service.ts`'s regex-only
  `PATTERN_GROUPS` are the two places most tempting to reach for a model;
  don't (spec §1 rule 9, §12.4, §20).
- **Venue staff cannot see chats, emails, or card details.**
  `redemption.redeemByStaff` never touches `messages`, `users.email`, or
  `payment_methods`/`payment_holds` — its result type (`RedeemResult`) is
  deliberately narrow (spec §4.2).
- **The reporter's identity is never exposed to the reported user.**
  No function in `report.service.ts` or `moderation.service.ts` returns a
  reporter id to anyone but an admin actor (spec §30.9).
- **The payment ledger is insert-only.** `ledger.service.ts` exposes no
  update/delete function; a correction is a new offsetting row (spec §14.8).
- **Zero human moderation.** Every `moderation.service.ts` /
  `appeal.service.ts` function resolves to an automated outcome; there is
  no "queue for human review" state anywhere in either module's contract
  (spec §18.1, Definition of Done #17).
- **Policy snapshots are immutable once captured** (see decision #5 above)
  — a `config.set` call must never change the behavior of an
  already-created `interests`/`date_proposals` row.

## What's real vs. stubbed

**Fully implemented (not stubs):** `src/config/*`, `src/lib/*`, `src/db/*`,
`src/services/payments/*`, `src/services/media/*`, `src/seed.ts`,
`db/migrations/001_init.sql`.

**Stubbed (throw `NotImplementedError`), signatures frozen:** every file
listed in the Module table above.
