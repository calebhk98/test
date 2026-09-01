/**
 * src/http/serializers/interests.ts, `GET /interests/incoming`/`outgoing`,
 * enriched (docs/ux-api-review.md §6). Wraps
 * `interest.service#EnrichedInterestItem` (already the counterpart's
 * `displayName`/`primaryPhotoUrl`/`age`/`approximateDistanceKm`, with the
 * internal-only `policySnapshot` already dropped at the service layer),
 * this file only turns `Date` into an ISO-8601 string, same convention as
 * every other list serializer in this codebase.
 */
import type { EnrichedInterestItem } from '../../services/interest.service.js';
import type { Page } from '../../domain/types.js';

export interface InterestListItemView {
  id: string;
  counterpartUserId: string;
  status: EnrichedInterestItem['status'];
  displayName: string;
  primaryPhotoUrl: string | null;
  age: number;
  approximateDistanceKm: number | null;
  createdAt: string;
  expiresAt: string;
  acceptedAt: string | null;
  declinedAt: string | null;
  canceledAt: string | null;
  expiredAt: string | null;
}

function serializeItem(item: EnrichedInterestItem): InterestListItemView {
  return {
    id: item.id,
    counterpartUserId: item.counterpartUserId,
    status: item.status,
    displayName: item.displayName,
    primaryPhotoUrl: item.primaryPhotoUrl,
    age: item.age,
    approximateDistanceKm: item.approximateDistanceKm,
    createdAt: item.createdAt.toISOString(),
    expiresAt: item.expiresAt.toISOString(),
    acceptedAt: item.acceptedAt ? item.acceptedAt.toISOString() : null,
    declinedAt: item.declinedAt ? item.declinedAt.toISOString() : null,
    canceledAt: item.canceledAt ? item.canceledAt.toISOString() : null,
    expiredAt: item.expiredAt ? item.expiredAt.toISOString() : null,
  };
}

export interface InterestListPageView {
  items: InterestListItemView[];
  nextCursor: string | null;
}

export function serializeInterestListPage(page: Page<EnrichedInterestItem>): InterestListPageView {
  return { items: page.items.map(serializeItem), nextCursor: page.nextCursor };
}
