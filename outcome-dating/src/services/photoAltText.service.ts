/**
 * src/services/photoAltText.service.ts, user-authored photo descriptions
 * (task brief accessibility rule 1: "users should be able to describe
 * their photos, and the description must travel with the photo
 * everywhere it appears").
 *
 * Deliberately a SEPARATE file from photo.service.ts (an alternative the
 * task brief explicitly offers) rather than an edit to it: photo.service.ts
 * is Agent A's actively-owned, concurrently-edited file, and this build's
 * file list only authorizes "minimal, additive" changes there. Splitting
 * alt text out entirely (its own service, its own DB column added by an
 * ALTER TABLE in this build's own migration, never touching
 * photo.service.ts's file, and additive to its table) means this build
 * and Agent A's can proceed with zero merge risk against each other.
 *
 * WHAT "TRAVELS WITH THE PHOTO EVERYWHERE IT APPEARS" MEANS HERE, AND WHY
 * IT'S ONLY HALF DONE BY THIS FILE ALONE:
 *
 *   alt_text lives on `user_photos` itself (one column, one row per
 *   photo, db/migrations/021_retention_i18n.sql) precisely so it is
 *   structurally impossible for a photo to be fetched without its alt
 *   text sitting right next to it in the same row. That's the storage
 *   half of the guarantee.
 *
 *   The OTHER half, every serializer that currently emits a photo (today:
 *   `profile.service.ts`'s `fetchProfileRow`, which returns a bare
 *   `photoUrls: string[]` with no photo id at all, let alone alt text,
 *   see that file) needs to actually SELECT and return this column. This
 *   build cannot make that edit itself (profile.service.ts is not in this
 *   build's file list), so `getAltTextForPhotos` below is the ready-made,
 *   tested batch-fetch function any such serializer needs to call, see
 *   docs/accessibility.md for the exact integration point and why
 *   `photoUrls: string[]` is itself a pre-existing structural gap (an
 *   alt-text string can't be paired with a bare URL string once returned
 * the photo's id needs to travel too).
 */
import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import { NotFoundError, ValidationError } from '../lib/errors.js';

export interface PhotoAltText {
  photoId: string;
  /** Null means "not described yet", distinct from an empty string, which a user could otherwise never write (SetAltTextSchema requires non-empty trimmed text) to explicitly mean "deliberately blank" vs. simply never having been asked. A client should treat null the same way it treats a photo it has no alt text for today: fall back to photo.service.ts's own generic "photo" label, never render the literal word "null". */
  altText: string | null;
  updatedAt: Date;
}

const SetAltTextSchema = z.object({
  // Long enough for a genuinely descriptive sentence or two ("A person
  // standing on a beach at sunset, smiling, wearing a blue jacket."),
  // short enough that a client rendering it as a screen-reader label
  // never has to truncate a paragraph. No character-set restriction
  // beyond trimming, descriptive prose is exactly what this field is
  // for, unlike e.g. a display name.
  altText: z.string().trim().min(1).max(500),
});

interface PhotoOwnerRow {
  user_id: string;
}

async function requireOwnedPhoto(ctx: Ctx, photoId: string, userId: string): Promise<void> {
  const { rows } = await ctx.db.query<PhotoOwnerRow>(`SELECT user_id FROM user_photos WHERE id = $1`, [photoId]);
  const row = rows[0];
  if (!row || row.user_id !== userId) {
    throw new NotFoundError('Photo not found.');
  }
}

/** Sets (or replaces) the caller's own photo's description. Ownership-checked the same way every other per-photo mutation in this codebase is (photo.service.ts's own `fetchOwnedPhoto` pattern), a 404, not a 403, for someone else's photo id, so a caller can't distinguish "not yours" from "doesn't exist". */
export async function setPhotoAltText(ctx: Ctx, photoId: string, input: unknown): Promise<PhotoAltText> {
  const { userId } = requireUserActor(ctx);
  const parsed = SetAltTextSchema.parse(input);
  await requireOwnedPhoto(ctx, photoId, userId);

  const now = ctx.clock.now();
  const { rows } = await ctx.db.query<{ id: string; alt_text: string | null; alt_text_updated_at: Date }>(
    `UPDATE user_photos SET alt_text = $2, alt_text_updated_at = $3 WHERE id = $1
     RETURNING id, alt_text, alt_text_updated_at`,
    [photoId, parsed.altText, now],
  );
  const row = rows[0];
  if (!row) throw new ValidationError('Failed to save photo description.');
  return { photoId: row.id, altText: row.alt_text, updatedAt: row.alt_text_updated_at };
}

/** Clears a photo's description back to "not described" (distinct from setting it to an empty string, which validation above never allows), e.g. a user who wants to withdraw a description without deleting the photo itself. */
export async function clearPhotoAltText(ctx: Ctx, photoId: string): Promise<void> {
  const { userId } = requireUserActor(ctx);
  await requireOwnedPhoto(ctx, photoId, userId);
  await ctx.db.query(`UPDATE user_photos SET alt_text = NULL, alt_text_updated_at = $2 WHERE id = $1`, [photoId, ctx.clock.now()]);
}

/** Single-photo read, for a caller that already knows the id (e.g. the owner reviewing their own photo grid). Returns null for an unknown id rather than throwing, callers building a batch view over possibly-mixed ids should prefer `getAltTextForPhotos` below. */
export async function getPhotoAltText(ctx: Ctx, photoId: string): Promise<PhotoAltText | null> {
  const { rows } = await ctx.db.query<{ id: string; alt_text: string | null; alt_text_updated_at: Date }>(
    `SELECT id, alt_text, alt_text_updated_at FROM user_photos WHERE id = $1`,
    [photoId],
  );
  const row = rows[0];
  if (!row) return null;
  return { photoId: row.id, altText: row.alt_text, updatedAt: row.alt_text_updated_at };
}

/**
 * Batch read for exactly the "travels with the photo everywhere it
 * appears" case: a serializer that already has a page of photo ids (a
 * profile view, a discovery card, a match card, ...) calls this ONCE with
 * every id on the page and merges the result in, rather than issuing one
 * query per photo (see profile.ts's own batched-query convention
 * elsewhere in this codebase, e.g. filter.service.ts's `loadProfilesBatch`).
 * A photo id with no row in the map means "photo not found", not "no alt
 * text" (that's `altText: null` on a present entry), a serializer should
 * treat a missing map entry as a data-integrity bug worth logging, not a
 * silent blank.
 */
export async function getAltTextForPhotos(ctx: Ctx, photoIds: string[]): Promise<Map<string, PhotoAltText>> {
  const result = new Map<string, PhotoAltText>();
  if (photoIds.length === 0) return result;

  const { rows } = await ctx.db.query<{ id: string; alt_text: string | null; alt_text_updated_at: Date }>(
    `SELECT id, alt_text, alt_text_updated_at FROM user_photos WHERE id = ANY($1::uuid[])`,
    [photoIds],
  );
  for (const row of rows) {
    result.set(row.id, { photoId: row.id, altText: row.alt_text, updatedAt: row.alt_text_updated_at });
  }
  return result;
}
