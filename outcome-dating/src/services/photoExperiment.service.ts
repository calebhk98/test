import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import { KNOWN_FLAGS } from '../config/flags.service.js';
import type { PhotoExperimentStats, PhotoRecommendation } from '../domain/types.js';

/**
 * photoExperiment.service, photo A/B testing.
 * Spec: §7.3, §24.2 (`GET /me/photo-test-results`), §25.5 (nightly stats job).
 *
 * Owning agent: A.
 *
 * Invariants:
 *  - Gated behind the `photo_ab_testing` feature flag
 *    (`ctx.flags.isEnabled(KNOWN_FLAGS.PHOTO_AB_TESTING, ...)`, spec §22),
 *    a user with the flag off never gets a randomized primary photo.
 *  - Only runs when a user has >= 3 photos (spec §7.3 rule 1).
 *  - The success metric is `interestsAccepted`, never raw `impressions` or
 *    profile views (spec §7.3 rule 4), `computeRecommendation` must rank
 *    on accepted-interest rate.
 *  - Reordering is never silent: `applyRecommendation` requires an
 *    explicit user approval unless product has flipped a config value for
 *    automatic reordering (spec §7.3 "user should be able to approve or
 *    reject ... unless product decides automatic reordering is preferred").
 *
 * Significance guard (documented here, the single source of truth for
 * these three numbers): a challenger photo is only ever recommended once
 * it, AND the current primary, individually clear `MIN_IMPRESSIONS_FOR_SIGNIFICANCE`
 * impressions (below that a binomial accept-rate estimate at typical
 * dating-app accept rates is dominated by noise), the challenger has at
 * least `MIN_ACCEPTED_FOR_SIGNIFICANCE` accepted interests of its own (so
 * one lucky accept out of two impressions can't produce a 50% "lift"), and
 * its accept-rate lift over the primary is at least `MIN_LIFT_FRACTION`.
 * This is a threshold guard, not a real significance test (no MVP
 * dependency on a stats library), documented so it can be swapped for a
 * proper two-proportion test later without touching call sites. These are
 * file-local constants rather than `config.service.ts` keys because that
 * registry is shared infra outside this agent's ownership; promoting them
 * to real config keys (e.g. `photo.ab_test_min_impressions`) is a
 * follow-up flagged in the build report if product wants them tunable
 * without a deploy.
 */

const MIN_IMPRESSIONS_FOR_SIGNIFICANCE = 30;
const MIN_ACCEPTED_FOR_SIGNIFICANCE = 3;
/** Minimum relative lift (challenger accept-rate vs primary's), as a fraction, 0.15 = 15%. */
const MIN_LIFT_FRACTION = 0.15;

/** Ad-hoc feature flag (not in `KNOWN_FLAGS`, see `flags.service.ts` doc: "admins may also define ad-hoc flags"). Off by default (no seeded row = `isEnabled` returns false), matching the spec's default of user-approved reordering. */
const AUTO_REORDER_FLAG_KEY = 'photo_ab_auto_reorder';

// =====================================================================
// recordImpression / recordInterestSent / recordInterestAccepted
// =====================================================================

async function assertPhotoBelongsToUser(ctx: Ctx, photoId: string, userId: string): Promise<void> {
  const { rows } = await ctx.db.query<{ user_id: string }>('SELECT user_id FROM user_photos WHERE id = $1', [
    photoId,
  ]);
  const row = rows[0];
  if (!row || row.user_id !== userId) {
    throw new ValidationError('photoId does not belong to candidateUserId.');
  }
}

async function bumpStat(
  ctx: Ctx,
  userId: string,
  photoId: string,
  column: 'impressions' | 'interests_sent' | 'interests_accepted',
): Promise<void> {
  await assertPhotoBelongsToUser(ctx, photoId, userId);
  await ctx.db.query(
    `INSERT INTO photo_experiments (user_id, photo_id, impressions, interests_sent, interests_accepted, created_at, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6, $6)
     ON CONFLICT (user_id, photo_id) DO UPDATE SET
       ${column} = photo_experiments.${column} + 1,
       updated_at = EXCLUDED.updated_at`,
    [
      userId,
      photoId,
      column === 'impressions' ? 1 : 0,
      column === 'interests_sent' ? 1 : 0,
      column === 'interests_accepted' ? 1 : 0,
      ctx.clock.now(),
    ],
  );
}

/** Called once per discovery-grid impression where this photo was shown as the candidate's primary (spec §7.3 rule 3). */
export async function recordImpression(ctx: Ctx, input: { candidateUserId: string; photoId: string }): Promise<void> {
  await bumpStat(ctx, input.candidateUserId, input.photoId, 'impressions');
}

export async function recordInterestSent(ctx: Ctx, input: { candidateUserId: string; photoId: string }): Promise<void> {
  await bumpStat(ctx, input.candidateUserId, input.photoId, 'interests_sent');
}

export async function recordInterestAccepted(ctx: Ctx, input: { candidateUserId: string; photoId: string }): Promise<void> {
  await bumpStat(ctx, input.candidateUserId, input.photoId, 'interests_accepted');
}

// =====================================================================
// listStatsForUser
// =====================================================================

interface StatsRow {
  id: string;
  user_id: string;
  photo_id: string;
  impressions: string;
  interests_sent: string;
  interests_accepted: string;
  created_at: Date;
  updated_at: Date;
}

function mapStats(row: StatsRow): PhotoExperimentStats {
  return {
    id: row.id,
    userId: row.user_id,
    photoId: row.photo_id,
    impressions: Number(row.impressions),
    interestsSent: Number(row.interests_sent),
    interestsAccepted: Number(row.interests_accepted),
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

export async function listStatsForUser(ctx: Ctx, userId: string): Promise<PhotoExperimentStats[]> {
  if (ctx.actor.type === 'user' && ctx.actor.userId !== userId) {
    throw new ForbiddenError('Cannot view another user’s photo experiment stats.');
  }
  if (ctx.actor.type === 'venue_staff') {
    throw new ForbiddenError('Venue staff cannot view photo experiment stats.');
  }

  const { rows } = await ctx.db.query<StatsRow>(
    `SELECT id, user_id, photo_id, impressions::text, interests_sent::text, interests_accepted::text, created_at, updated_at
     FROM photo_experiments WHERE user_id = $1 ORDER BY created_at ASC`,
    [userId],
  );
  return rows.map(mapStats);
}

// =====================================================================
// Recommendation computation (pure) + significance guard
// =====================================================================

export interface PhotoRankingInput {
  photoId: string;
  position: number;
  impressions: number;
  interestsAccepted: number;
}

/**
 * Pure ranking/significance function, no I/O, easy to unit-test directly.
 * Returns the single best-supported recommendation (challenger vs current
 * primary, i.e. `position === 0`), or `null` if fewer than 3 photos, no
 * primary, or nothing clears the significance guard documented above.
 */
export function computeRecommendation(photos: PhotoRankingInput[]): PhotoRecommendation | null {
  if (photos.length < 3) return null;
  const primary = photos.find((p) => p.position === 0);
  if (!primary) return null;
  if (primary.impressions < MIN_IMPRESSIONS_FOR_SIGNIFICANCE) return null;

  const primaryRate = primary.impressions > 0 ? primary.interestsAccepted / primary.impressions : 0;

  let best: { photo: PhotoRankingInput; lift: number } | null = null;
  for (const p of photos) {
    if (p.photoId === primary.photoId) continue;
    if (p.impressions < MIN_IMPRESSIONS_FOR_SIGNIFICANCE) continue;
    if (p.interestsAccepted < MIN_ACCEPTED_FOR_SIGNIFICANCE) continue;

    const rate = p.interestsAccepted / p.impressions;
    let lift: number;
    if (primaryRate <= 0) {
      if (rate <= 0) continue;
      lift = 1; // primary has never converted; report as a 100% floor rather than an undefined/infinite lift.
    } else {
      lift = (rate - primaryRate) / primaryRate;
    }
    if (lift < MIN_LIFT_FRACTION) continue;
    if (!best || lift > best.lift) best = { photo: p, lift };
  }

  if (!best) return null;
  return {
    photoId: best.photo.photoId,
    currentPosition: best.photo.position,
    recommendedPosition: 0,
    acceptedInterestLiftPercent: Math.round(best.lift * 100),
  };
}

async function fetchRankingInputs(ctx: Ctx, userId: string): Promise<PhotoRankingInput[]> {
  const { rows } = await ctx.db.query<{ photo_id: string; position: number; impressions: string; interests_accepted: string }>(
    `SELECT up.id AS photo_id, up.position,
            COALESCE(pe.impressions, 0)::text AS impressions,
            COALESCE(pe.interests_accepted, 0)::text AS interests_accepted
     FROM user_photos up
     LEFT JOIN photo_experiments pe ON pe.photo_id = up.id AND pe.user_id = up.user_id
     WHERE up.user_id = $1 AND up.moderation_status = 'approved'
     ORDER BY up.position ASC`,
    [userId],
  );
  return rows.map((r) => ({
    photoId: r.photo_id,
    position: r.position,
    impressions: Number(r.impressions),
    interestsAccepted: Number(r.interests_accepted),
  }));
}

async function applyPhotoReorder(ctx: Ctx, userId: string, photoId: string): Promise<void> {
  const { rows } = await ctx.db.query<{ id: string }>(
    'SELECT id FROM user_photos WHERE user_id = $1 ORDER BY position ASC',
    [userId],
  );
  const ids = rows.map((r) => r.id);
  if (!ids.includes(photoId)) return;

  const reordered = [photoId, ...ids.filter((id) => id !== photoId)];
  for (let i = 0; i < reordered.length; i++) {
    await ctx.db.query('UPDATE user_photos SET position = $2 WHERE id = $1', [reordered[i], i]);
  }
  await ctx.db.query('UPDATE user_photos SET is_primary = false WHERE user_id = $1 AND is_primary = true', [userId]);
  await ctx.db.query('UPDATE user_photos SET is_primary = true WHERE id = $1', [photoId]);
}

// =====================================================================
// getMyPhotoTestResults
// =====================================================================

interface RecommendationRow {
  photo_id: string;
  current_position: number;
  recommended_position: number;
  lift_percent: number;
}

/** `GET /me/photo-test-results`, current recommendation(s), if the experiment has enough data. Reads persisted `photo_recommendations` rows (populated by `refreshAllRecommendations`), not a fresh recompute per call. */
export async function getMyPhotoTestResults(ctx: Ctx): Promise<PhotoRecommendation[]> {
  const { userId } = requireUserActor(ctx);

  const { rows } = await ctx.db.query<RecommendationRow>(
    `SELECT photo_id, current_position, recommended_position, lift_percent
     FROM photo_recommendations WHERE user_id = $1 AND status = 'pending'
     ORDER BY lift_percent DESC`,
    [userId],
  );

  return rows.map((r) => ({
    photoId: r.photo_id,
    currentPosition: r.current_position,
    recommendedPosition: r.recommended_position,
    acceptedInterestLiftPercent: r.lift_percent,
  }));
}

// =====================================================================
// refreshAllRecommendations (§25.5 nightly job)
// =====================================================================

/** §25.5 nightly job: aggregate impressions/accepted-interests across all users with an active experiment and refresh recommendations. */
export async function refreshAllRecommendations(ctx: Ctx): Promise<{ usersUpdated: number }> {
  const { rows: eligibleUsers } = await ctx.db.query<{ user_id: string }>(
    `SELECT user_id FROM user_photos WHERE moderation_status = 'approved' GROUP BY user_id HAVING count(*) >= 3`,
  );

  const autoReorder = await ctx.flags.isEnabled(AUTO_REORDER_FLAG_KEY);
  let usersUpdated = 0;

  for (const { user_id: userId } of eligibleUsers) {
    const abTestingEnabled = await ctx.flags.isEnabled(KNOWN_FLAGS.PHOTO_AB_TESTING, { userId });
    if (!abTestingEnabled) continue;

    const rankingInputs = await fetchRankingInputs(ctx, userId);
    const recommendation = computeRecommendation(rankingInputs);
    if (!recommendation) continue;

    const now = ctx.clock.now();
    await ctx.db.query(
      `INSERT INTO photo_recommendations (user_id, photo_id, current_position, recommended_position, lift_percent, status, created_at, updated_at)
       VALUES ($1, $2, $3, $4, $5, 'pending', $6, $6)
       ON CONFLICT (user_id, photo_id) DO UPDATE SET
         current_position = EXCLUDED.current_position,
         recommended_position = EXCLUDED.recommended_position,
         lift_percent = EXCLUDED.lift_percent,
         updated_at = EXCLUDED.updated_at
       WHERE photo_recommendations.status = 'pending'`,
      [userId, recommendation.photoId, recommendation.currentPosition, recommendation.recommendedPosition, recommendation.acceptedInterestLiftPercent, now],
    );
    usersUpdated++;

    if (autoReorder) {
      await applyPhotoReorder(ctx, userId, recommendation.photoId);
      await ctx.db.query(
        `UPDATE photo_recommendations SET status = 'approved', updated_at = $3 WHERE user_id = $1 AND photo_id = $2`,
        [userId, recommendation.photoId, now],
      );
    }
  }

  return { usersUpdated };
}

// =====================================================================
// approveRecommendation / rejectRecommendation
// =====================================================================

async function fetchPendingRecommendation(ctx: Ctx, userId: string, photoId: string): Promise<RecommendationRow> {
  const { rows } = await ctx.db.query<RecommendationRow>(
    `SELECT photo_id, current_position, recommended_position, lift_percent
     FROM photo_recommendations WHERE user_id = $1 AND photo_id = $2 AND status = 'pending'`,
    [userId, photoId],
  );
  const row = rows[0];
  if (!row) {
    throw new NotFoundError('No pending photo recommendation for this photo.');
  }
  return row;
}

/** User approves a recommendation, reorders photos, setting `recommendedPosition`'s photo as primary if position 0. */
export async function approveRecommendation(ctx: Ctx, photoId: string): Promise<void> {
  const { userId } = requireUserActor(ctx);
  await fetchPendingRecommendation(ctx, userId, photoId);

  await applyPhotoReorder(ctx, userId, photoId);
  await ctx.db.query(
    `UPDATE photo_recommendations SET status = 'approved', updated_at = $3 WHERE user_id = $1 AND photo_id = $2`,
    [userId, photoId, ctx.clock.now()],
  );
}

export async function rejectRecommendation(ctx: Ctx, photoId: string): Promise<void> {
  const { userId } = requireUserActor(ctx);
  await fetchPendingRecommendation(ctx, userId, photoId);

  await ctx.db.query(
    `UPDATE photo_recommendations SET status = 'rejected', updated_at = $3 WHERE user_id = $1 AND photo_id = $2`,
    [userId, photoId, ctx.clock.now()],
  );
}
