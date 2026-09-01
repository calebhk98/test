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
 */
import type { DiscoveryCandidate, Page } from '../../domain/types.js';

export interface DiscoveryCardView {
  userId: string;
  displayName: string;
  age: number;
  approximateDistanceKm: number | null;
  primaryPhotoUrl: string | null;
  sharedInterestTag: string | null;
  trustLevel: DiscoveryCandidate['trustLevel'];
}

export function serializeDiscoveryCandidate(c: DiscoveryCandidate): DiscoveryCardView {
  return {
    userId: c.userId,
    displayName: c.displayName,
    age: c.age,
    approximateDistanceKm: c.approximateDistanceKm,
    primaryPhotoUrl: c.primaryPhotoUrl,
    sharedInterestTag: c.sharedInterestTag,
    trustLevel: c.trustLevel,
    // Deliberately NOT included: compatibilityScore (internal sort key,
    // spec doesn't require exposing the raw number to the viewer),
    // profileCompleteness (internal ranking signal), likeCount/popularity/
    // boosted (do not exist on the domain type and must never be added
    // here either, spec §10.1, §1 rule 14/15).
  };
}

export function serializeDiscoveryPage(page: Page<DiscoveryCandidate>): { items: DiscoveryCardView[]; nextCursor: string | null } {
  return { items: page.items.map(serializeDiscoveryCandidate), nextCursor: page.nextCursor };
}
