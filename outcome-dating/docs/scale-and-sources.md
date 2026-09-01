# Scale and sources of truth

Three questions answered against the code, not the spec: can it scale, is demo data actually swappable for real data, is there one source of truth per concept. Originally an analysis of a codebase that had none of the fixes below; most of Part 1 and Part 2's findings are now fixed. See `docs/capacity.md` for the current, measured numbers at 10K to 8B users.

## Part 1: scale, fixed since the original review

The original finding was stark: the discovery grid, the reality dashboard, and the nightly compatibility-score refresh all scanned every active user on the platform with no geographic bound, then walked the result one row at a time over sequential DB round trips. That broke discovery at a few thousand users and made the compatibility refresh job exceed its own 24-hour window between roughly 3,000 and 10,000 users, with storage estimated at 1.75TB at 100,000 users.

All three are now geo-bounded:

- `discovery.service.ts#loadCandidatePool` applies a lat/long bounding box before doing any per-row work, capped at `MAX_CANDIDATE_POOL_SIZE`, proven flat (query count, not just latency) from 1,000 to 50,000 seeded users by `tests/perf/scaleCurve.perf.test.ts` (see `docs/capacity.md` §2).
- `compatibility.service.ts#refreshAllScores` no longer materializes every pair. It only refreshes users active within a configured window, and only their nearest neighbors within a geographic radius, turning the O(density²) blow-up into O(density × K). See the file's own "SCALE FIX" comment block for the full reasoning.
- The rate limiter and job scheduler's in-process state are unchanged and remain a real limit the moment the app tier scales to more than one instance; see `docs/capacity.md` §5 for where that binds relative to everything else.

## Part 2: is demo data actually swappable for real data

Seed data itself is cleanly isolated: `src/seed.ts` is a standalone CLI command never imported by `src/services/**` or `src/http/**`, seeded users share a single greppable email domain, and deleting them cascades correctly through every foreign key. That part was always fine.

The bigger finding, and now fixed, was that nothing stopped a misconfigured production deployment from silently running on fakes:

- **The fake payment processor used to have no loud-failure path.** `PAYMENT_PROCESSOR` defaulted to `'fake'` if unset, and nothing refused to start in production with it selected, meaning escrow holds would "succeed," tickets would issue, and venue payouts would be recorded, with no real money ever moving and a fully green reconciliation job. Fixed: `src/config/adapters.ts#runProductionGuard` now refuses to boot in `NODE_ENV=production` unless `PAYMENT_PROCESSOR=stripe` with real secrets configured. `StripeProcessor` itself remains an unimplemented stub (see the README's known limitations); the guard's job is only to make that fact loud instead of silent.
- **The media moderation stub used to have no config switch at all.** Fixed the same way: the production guard refuses to boot without a real `ImageModerationPort` registered via `registerMediaModerationProvider`. No real adapter exists yet, so production photo moderation still cannot start, which is the correct, honest failure mode until one is written.
- **`AUTH_TOKEN_SECRET` used to have no boot-time check against its insecure default.** Fixed: the production guard also refuses to boot with the shipped dev-default secret or one shorter than the minimum length.
- **The new typed question bank used to have no HTTP route at all**, despite being fully built, seeded, and tested. Fixed: `question.service.ts`'s new-bank functions are now routed (see `src/http/routes/questions.routes.ts`), and the old `questions`/`answers` bank was dropped outright (`db/migrations/022_drop_old_question_bank.sql`), so there is exactly one question system reachable today, closing the "asked about religion three times" risk from Part 3 below at the same time.

## Part 3: is there a single source of truth per concept

The headline finding, two parallel, independently-answered question banks that could ask the same real-world concept twice under different labels, is now fixed by the same change as Part 2 above: the old bank is gone, and `compatibility.service.ts` scores the new one directly.

What's still true and worth knowing:

- **Every status-shaped enum is declared twice** (once as a SQL `CHECK`, once as a TypeScript union), held together only by developer discipline, with one pair (`notification_preferences.category` vs `notification_outbox.category`) already deliberately diverged. See `docs/duplication.md` for the current list and the one drifted pair.
- **Three config values are shadowed by code constants** that exist as fallbacks or test-only defaults (`discovery.service.ts`'s `MIN_PROFILE_COMPLETENESS_FOR_DISCOVERY`, `compatibility.service.ts`'s two pure-function defaults, `trust.service.ts`'s `TRUST_SCORE_BASE`). The first is genuinely dead code and a landmine if anyone starts using it; the other two are lower risk, documented, and used only where a database-free pure function needs a value. Not re-verified in this pass; treat as still open.
- **Two independent haversine formulas** (exact filter enforcement vs. the internal, never-displayed distance-privacy calculation) and **two independent 18-years-old age checks** (application code plus a DB `CHECK`) remain, both currently consistent, both a defensible defense-in-depth pattern rather than an accidental duplicate. See `docs/duplication.md`.
