import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { UserPhoto } from '../domain/types.js';

/**
 * photo.service — photo upload, ordering, and moderation.
 * Spec: §7.2 (requirements), §24.2 (routes).
 *
 * Owning agent: A.
 *
 * Invariants:
 *  - Every upload is analyzed via `ctx.media` (`ImageModerationPort`,
 *    `src/services/media/*`) before the row is marked 'approved' — never
 *    trust client-supplied moderation status.
 *  - A photo in the primary slot MUST have `faceDetected: true` from that
 *    analysis, or it's rejected (spec §7.2 rule 2) — this module is the
 *    enforcement point; `discovery.service.ts`'s visibility rule ("has at
 *    least one approved photo", §10.2 rule 4) just reads the resulting
 *    `moderation_status`.
 *  - Duplicate/scam detection (§7.2 rule 4, §18.2) compares the new
 *    photo's `perceptualHash` against other users' `user_photos` rows —
 *    this module owns that query; `ctx.media` only produces the hash for
 *    one image.
 *  - `uq_user_photos_one_primary` (partial unique index) enforces "at most
 *    one primary photo" at the DB layer; `setPrimaryPhoto` must
 *    unset-then-set within one transaction to satisfy it.
 */

export interface UploadPhotoInput {
  imageUrl: string;
}

export async function uploadPhoto(ctx: Ctx, input: UploadPhotoInput): Promise<UserPhoto> {
  throw new NotImplementedError('photo.uploadPhoto');
}

export async function deletePhoto(ctx: Ctx, photoId: string): Promise<void> {
  throw new NotImplementedError('photo.deletePhoto');
}

export async function listMyPhotos(ctx: Ctx): Promise<UserPhoto[]> {
  throw new NotImplementedError('photo.listMyPhotos');
}

/** Re-runs moderation analysis and promotes `photoId` to primary. Throws ValidationError if the photo isn't 'approved' or lacks a detected face. */
export async function setPrimaryPhoto(ctx: Ctx, photoId: string): Promise<UserPhoto> {
  throw new NotImplementedError('photo.setPrimaryPhoto');
}

/** Persist a new photo order (position 0..n-1). Does not change which photo is primary — see `setPrimaryPhoto`. */
export async function reorderPhotos(ctx: Ctx, orderedPhotoIds: string[]): Promise<UserPhoto[]> {
  throw new NotImplementedError('photo.reorderPhotos');
}

/** Cross-user duplicate/scam-image check by perceptual hash (§7.2 rule 4, §18.2). Returns the user ids of any other approved photo sharing this hash. */
export async function findDuplicateOwners(ctx: Ctx, perceptualHash: string, excludeUserId: string): Promise<string[]> {
  throw new NotImplementedError('photo.findDuplicateOwners');
}
