import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { PhotoExperimentStats, PhotoRecommendation } from '../domain/types.js';

/**
 * photoExperiment.service — photo A/B testing.
 * Spec: §7.3, §24.2 (`GET /me/photo-test-results`), §25.5 (nightly stats job).
 *
 * Owning agent: A.
 *
 * Invariants:
 *  - Gated behind the `photo_ab_testing` feature flag
 *    (`ctx.flags.isEnabled(KNOWN_FLAGS.PHOTO_AB_TESTING, ...)`, spec §22) —
 *    a user with the flag off never gets a randomized primary photo.
 *  - Only runs when a user has >= 3 photos (spec §7.3 rule 1).
 *  - The success metric is `interestsAccepted`, never raw `impressions` or
 *    profile views (spec §7.3 rule 4) — `computeRecommendation` must rank
 *    on accepted-interest rate.
 *  - Reordering is never silent: `applyRecommendation` requires an
 *    explicit user approval unless product has flipped a config value for
 *    automatic reordering (spec §7.3 "user should be able to approve or
 *    reject ... unless product decides automatic reordering is preferred").
 */

/** Called once per discovery-grid impression where this photo was shown as the candidate's primary (spec §7.3 rule 3). */
export async function recordImpression(ctx: Ctx, input: { candidateUserId: string; photoId: string }): Promise<void> {
  throw new NotImplementedError('photoExperiment.recordImpression');
}

export async function recordInterestSent(ctx: Ctx, input: { candidateUserId: string; photoId: string }): Promise<void> {
  throw new NotImplementedError('photoExperiment.recordInterestSent');
}

export async function recordInterestAccepted(ctx: Ctx, input: { candidateUserId: string; photoId: string }): Promise<void> {
  throw new NotImplementedError('photoExperiment.recordInterestAccepted');
}

export async function listStatsForUser(ctx: Ctx, userId: string): Promise<PhotoExperimentStats[]> {
  throw new NotImplementedError('photoExperiment.listStatsForUser');
}

/** `GET /me/photo-test-results` — current recommendation(s), if the experiment has enough data. */
export async function getMyPhotoTestResults(ctx: Ctx): Promise<PhotoRecommendation[]> {
  throw new NotImplementedError('photoExperiment.getMyPhotoTestResults');
}

/** §25.5 nightly job: aggregate impressions/accepted-interests across all users with an active experiment and refresh recommendations. */
export async function refreshAllRecommendations(ctx: Ctx): Promise<{ usersUpdated: number }> {
  throw new NotImplementedError('photoExperiment.refreshAllRecommendations');
}

/** User approves a recommendation — reorders photos, setting `recommendedPosition`'s photo as primary if position 0. */
export async function approveRecommendation(ctx: Ctx, photoId: string): Promise<void> {
  throw new NotImplementedError('photoExperiment.approveRecommendation');
}

export async function rejectRecommendation(ctx: Ctx, photoId: string): Promise<void> {
  throw new NotImplementedError('photoExperiment.rejectRecommendation');
}
