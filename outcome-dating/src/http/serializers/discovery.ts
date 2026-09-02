/**
 * src/http/serializers/discovery.ts, the discovery grid card.
 *
 * Explicit allowlist enforcing spec §10.1's negative list at the wire
 * boundary: no `likeCount`, no `popularityScore`, no `boosted`/badge field,
 * no exact coordinates (only the already-fuzzed `approximateDistanceKm`),
 * and at most one `sharedInterestTag` (never an array). `discovery.service`'s
 * `DiscoveryCandidate` type structurally has none of these fields today,
 * this serializer is the last-line-of-defence guarantee that stays true
 * even if that type ever grows one by accident.
 *
 * `trustLevel` is deliberately NOT included, and was never meant to be:
 * the product forbids popularity/status signals on a discovery card (this
 * was never part of the card's own design), a candidate's trust level is
 * a status/ranking signal exactly like a boost badge or a like count, and
 * belongs only to that candidate's OWN trust page
 * (`GET /me/trust`, `trust.service.ts`, unaffected by this), never to
 * someone else's card. `DiscoveryCandidate` (`discovery.service.ts`, not
 * owned here) still carries `trustLevel` for its own internal ranking use
 * (see that file's own doc), this serializer is the allowlist boundary
 * that keeps it from ever reaching the wire.
 *
 * ALT TEXT (wiring fix, accessibility rule 1, "the description must travel
 * with the photo everywhere it appears"): `DiscoveryCandidate.primaryPhotoUrl`
 * is a bare url with no photo id, `discovery.service.ts` (owned by another
 * agent, not editable here) is the only place that could add one to the
 * type itself, out of this build's reach, see the build report. Rather
 * than leave the card without a description, this serializer resolves the
 * SAME `user_photos` row directly, by the one thing it already has that
 * identifies it uniquely enough: `(user_id, image_url)`, in one batched
 * query per page (never per-card), the same "one direct, read-only,
 * batched join query" pattern `serializers/tickets.ts`/`serializers/venue.ts`
 * already use for a cross-domain read outside this file's owning service's
 * "may call" list.
 */
import type { Ctx } from '../../lib/ctx.js';
import type { DiscoveryCandidate, Page } from '../../domain/types.js';

export interface DiscoveryPhotoView {
  id: string;
  imageUrl: string;
  altText: string | null;
}

export interface DiscoveryCardView {
  userId: string;
  displayName: string;
  age: number;
  approximateDistanceKm: number | null;
  /** Wiring fix: was `primaryPhotoUrl: string | null`, see this file's own doc above for why this resolves to the full `{id, imageUrl, altText}` shape via a direct batched lookup rather than a change to `DiscoveryCandidate` itself. */
  primaryPhoto: DiscoveryPhotoView | null;
  sharedInterestTag: string | null;
}

interface PhotoLookupRow {
  user_id: string;
  id: string;
  image_url: string;
  alt_text: string | null;
}

/** One batched lookup for every candidate on the page carrying a `primaryPhotoUrl`, keyed by the `(userId, imageUrl)` pair so it never has to guess which of a user's photos a bare url refers to. */
async function loadPrimaryPhotoViews(ctx: Ctx, candidates: DiscoveryCandidate[]): Promise<Map<string, DiscoveryPhotoView>> {
  const withPhotos = candidates.filter((c): c is DiscoveryCandidate & { primaryPhotoUrl: string } => c.primaryPhotoUrl != null);
  const result = new Map<string, DiscoveryPhotoView>();
  if (withPhotos.length === 0) return result;

  const userIds = withPhotos.map((c) => c.userId);
  const urls = withPhotos.map((c) => c.primaryPhotoUrl);
  const { rows } = await ctx.db.query<PhotoLookupRow>(
    `SELECT user_id, id, image_url, alt_text FROM user_photos WHERE user_id = ANY($1::uuid[]) AND image_url = ANY($2::text[])`,
    [userIds, urls],
  );
  for (const row of rows) {
    result.set(`${row.user_id}|${row.image_url}`, { id: row.id, imageUrl: row.image_url, altText: row.alt_text });
  }
  return result;
}

function serializeDiscoveryCandidate(c: DiscoveryCandidate, photoViews: Map<string, DiscoveryPhotoView>): DiscoveryCardView {
  return {
    userId: c.userId,
    displayName: c.displayName,
    age: c.age,
    approximateDistanceKm: c.approximateDistanceKm,
    primaryPhoto: c.primaryPhotoUrl ? (photoViews.get(`${c.userId}|${c.primaryPhotoUrl}`) ?? null) : null,
    sharedInterestTag: c.sharedInterestTag,
    // Deliberately NOT included: trustLevel (a status/ranking signal, see
    // this file's own doc above), compatibilityScore (internal sort key,
    // spec doesn't require exposing the raw number to the viewer),
    // profileCompleteness (internal ranking signal), likeCount/popularity/
    // boosted (do not exist on the domain type and must never be added
    // here either, spec §10.1, §1 rule 14/15).
  };
}

export async function serializeDiscoveryPage(ctx: Ctx, page: Page<DiscoveryCandidate>): Promise<{ items: DiscoveryCardView[]; nextCursor: string | null }> {
  const photoViews = await loadPrimaryPhotoViews(ctx, page.items);
  return { items: page.items.map((c) => serializeDiscoveryCandidate(c, photoViews)), nextCursor: page.nextCursor };
}
