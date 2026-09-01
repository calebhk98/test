import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { NotFoundError, ValidationError } from '../lib/errors.js';
import type { PhotoModerationStatus, UserPhoto } from '../domain/types.js';

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
 *  - Zero human moderation (§18.1): nudity/weapons/illegal content always
 *    resolves to 'rejected' immediately from `ctx.media`'s verdict — there
 *    is no "pending human review" state written anywhere in this file.
 */

export interface UploadPhotoInput {
  imageUrl: string;
}

const UploadPhotoSchema = z.object({
  imageUrl: z.string().trim().url().max(2000),
});

interface PhotoRow {
  id: string;
  user_id: string;
  image_url: string;
  position: number;
  is_primary: boolean;
  moderation_status: PhotoModerationStatus;
  face_detected: boolean | null;
  blur_score: number | null;
  brightness_score: number | null;
  group_photo_detected: boolean | null;
  perceptual_hash: string | null;
  created_at: Date;
}

function mapPhoto(row: PhotoRow): UserPhoto {
  return {
    id: row.id,
    userId: row.user_id,
    imageUrl: row.image_url,
    position: row.position,
    isPrimary: row.is_primary,
    moderationStatus: row.moderation_status,
    faceDetected: row.face_detected,
    blurScore: row.blur_score,
    brightnessScore: row.brightness_score,
    groupPhotoDetected: row.group_photo_detected,
    perceptualHash: row.perceptual_hash,
    createdAt: row.created_at,
  };
}

const PHOTO_COLUMNS =
  'id, user_id, image_url, position, is_primary, moderation_status, face_detected, blur_score, brightness_score, group_photo_detected, perceptual_hash, created_at';

async function fetchOwnedPhoto(ctx: Ctx, photoId: string, userId: string): Promise<PhotoRow> {
  const { rows } = await ctx.db.query<PhotoRow>(`SELECT ${PHOTO_COLUMNS} FROM user_photos WHERE id = $1`, [photoId]);
  const row = rows[0];
  if (!row || row.user_id !== userId) {
    throw new NotFoundError('Photo not found.');
  }
  return row;
}

export async function uploadPhoto(ctx: Ctx, input: UploadPhotoInput): Promise<UserPhoto> {
  const { userId } = requireUserActor(ctx);
  const { imageUrl } = UploadPhotoSchema.parse(input);

  const { rows: existingRows } = await ctx.db.query<{ count: string; max_position: number | null }>(
    `SELECT count(*)::text AS count, max(position) AS max_position FROM user_photos WHERE user_id = $1`,
    [userId],
  );
  const existingCount = Number(existingRows[0]?.count ?? 0);
  const nextPosition = (existingRows[0]?.max_position ?? -1) + 1;
  // The first photo a user ever uploads is the primary-candidate — it's
  // the one the "first photo must contain a visible face" gate (§7.2 rule
  // 2) applies to. Later uploads are never auto-primary; promotion happens
  // explicitly via `setPrimaryPhoto`, which re-runs this same gate.
  const isCandidatePrimary = existingCount === 0;

  const analysis = await ctx.media.analyzePhoto({ imageUrl, isCandidatePrimary });

  // §7.2 rule 4 / §18.2: cross-user duplicate/scam-image flag. A
  // `nudity`/`weapons`/`illegal` rejection from the port always wins; an
  // otherwise-clean image sharing a hash with another user's *approved*
  // photo is downgraded to 'flagged' regardless of the port's own verdict.
  let moderationStatus = analysis.moderationStatus;
  const duplicateOwners = await findDuplicateOwners(ctx, analysis.perceptualHash, userId);
  if (moderationStatus === 'approved' && duplicateOwners.length > 0) {
    moderationStatus = 'flagged';
  }

  const isPrimary = isCandidatePrimary && moderationStatus === 'approved';

  const { rows } = await ctx.db.query<PhotoRow>(
    `INSERT INTO user_photos
       (user_id, image_url, position, is_primary, moderation_status, face_detected, blur_score, brightness_score, group_photo_detected, perceptual_hash, created_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
     RETURNING ${PHOTO_COLUMNS}`,
    [
      userId,
      imageUrl,
      nextPosition,
      isPrimary,
      moderationStatus,
      analysis.faceDetected,
      analysis.blurScore,
      analysis.brightnessScore,
      analysis.groupPhotoDetected,
      analysis.perceptualHash,
      ctx.clock.now(),
    ],
  );

  return mapPhoto(rows[0]!);
}

export async function deletePhoto(ctx: Ctx, photoId: string): Promise<void> {
  const { userId } = requireUserActor(ctx);
  const photo = await fetchOwnedPhoto(ctx, photoId, userId);

  await ctx.db.query('DELETE FROM user_photos WHERE id = $1', [photoId]);

  if (photo.is_primary) {
    // Promote the next best candidate: lowest position, already-approved,
    // and (per §7.2 rule 2) already known to have a detected face from its
    // own analysis. If none qualifies, the user has no primary until they
    // pick one via `setPrimaryPhoto` — never auto-promote a faceless photo.
    const { rows: candidateRows } = await ctx.db.query<{ id: string }>(
      `SELECT id FROM user_photos WHERE user_id = $1 AND moderation_status = 'approved' AND face_detected = true ORDER BY position ASC LIMIT 1`,
      [userId],
    );
    const candidate = candidateRows[0];
    if (candidate) {
      await ctx.db.query('UPDATE user_photos SET is_primary = true WHERE id = $1', [candidate.id]);
    }
  }
}

export async function listMyPhotos(ctx: Ctx): Promise<UserPhoto[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<PhotoRow>(
    `SELECT ${PHOTO_COLUMNS} FROM user_photos WHERE user_id = $1 ORDER BY position ASC`,
    [userId],
  );
  return rows.map(mapPhoto);
}

/** Re-runs moderation analysis and promotes `photoId` to primary. Throws ValidationError if the photo isn't 'approved' or lacks a detected face. */
export async function setPrimaryPhoto(ctx: Ctx, photoId: string): Promise<UserPhoto> {
  const { userId } = requireUserActor(ctx);
  const photo = await fetchOwnedPhoto(ctx, photoId, userId);

  // Re-analyze specifically *as* a primary-candidate: a photo approved as a
  // secondary photo may never have been checked for a face (§7.2 rule 2
  // only gates primary-candidate photos), so the stored `face_detected`
  // from its original upload analysis isn't sufficient here.
  const analysis = await ctx.media.analyzePhoto({ imageUrl: photo.image_url, isCandidatePrimary: true });

  if (analysis.moderationStatus !== 'approved' || !analysis.faceDetected) {
    throw new ValidationError('This photo cannot be set as primary.', {
      reasons: analysis.rejectionReasons.length > 0 ? analysis.rejectionReasons : ['primary_photo_missing_face'],
    });
  }

  await ctx.db.query('UPDATE user_photos SET is_primary = false WHERE user_id = $1 AND is_primary = true', [userId]);
  const { rows } = await ctx.db.query<PhotoRow>(
    `UPDATE user_photos SET
       is_primary = true,
       moderation_status = $2,
       face_detected = $3,
       blur_score = $4,
       brightness_score = $5,
       group_photo_detected = $6,
       perceptual_hash = $7
     WHERE id = $1
     RETURNING ${PHOTO_COLUMNS}`,
    [
      photoId,
      analysis.moderationStatus,
      analysis.faceDetected,
      analysis.blurScore,
      analysis.brightnessScore,
      analysis.groupPhotoDetected,
      analysis.perceptualHash,
    ],
  );

  return mapPhoto(rows[0]!);
}

/** Persist a new photo order (position 0..n-1). Does not change which photo is primary — see `setPrimaryPhoto`. */
export async function reorderPhotos(ctx: Ctx, orderedPhotoIds: string[]): Promise<UserPhoto[]> {
  const { userId } = requireUserActor(ctx);

  const { rows: existing } = await ctx.db.query<{ id: string }>('SELECT id FROM user_photos WHERE user_id = $1', [
    userId,
  ]);
  const existingIds = new Set(existing.map((r) => r.id));
  const requestedIds = new Set(orderedPhotoIds);

  if (existingIds.size !== requestedIds.size || [...existingIds].some((id) => !requestedIds.has(id))) {
    throw new ValidationError('That list of photos doesn’t match your current photos — refresh and try again.');
  }

  for (let i = 0; i < orderedPhotoIds.length; i++) {
    await ctx.db.query('UPDATE user_photos SET position = $2 WHERE id = $1', [orderedPhotoIds[i], i]);
  }

  return listMyPhotos(ctx);
}

/** Cross-user duplicate/scam-image check by perceptual hash (§7.2 rule 4, §18.2). Returns the user ids of any other approved photo sharing this hash. */
export async function findDuplicateOwners(ctx: Ctx, perceptualHash: string, excludeUserId: string): Promise<string[]> {
  if (!perceptualHash) return [];
  const { rows } = await ctx.db.query<{ user_id: string }>(
    `SELECT DISTINCT user_id FROM user_photos WHERE perceptual_hash = $1 AND user_id <> $2 AND moderation_status = 'approved'`,
    [perceptualHash, excludeUserId],
  );
  return rows.map((r) => r.user_id);
}
