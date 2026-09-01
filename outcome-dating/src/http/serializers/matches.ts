/**
 * src/http/serializers/matches.ts, the `/matches` list/detail wire view.
 *
 * Explicit allowlist over `matches.service#MatchListItem` (same discipline
 * `serializers/discovery.ts`/`serializers/profile.ts` already use), even
 * though that type has no unsafe field today, this is the one place a
 * future field added to it would have to also be added HERE before it
 * could reach the wire, rather than leaking by an accidental spread.
 */
import type { Page } from '../../domain/types.js';
import type { MatchListItem } from '../../services/matches.service.js';

export interface MatchListItemView {
  conversationId: string;
  matchedUserId: string;
  displayName: string;
  primaryPhotoUrl: string | null;
  approximateDistanceKm: number | null;
  matchedAt: string;
  conversationStatus: MatchListItem['conversationStatus'];
  lastMessagePreview: string | null;
  lastMessageAt: string | null;
  unreadCount: number;
  lastActivityAt: string;
}

export function serializeMatch(m: MatchListItem): MatchListItemView {
  return {
    conversationId: m.conversationId,
    matchedUserId: m.matchedUserId,
    displayName: m.displayName,
    primaryPhotoUrl: m.primaryPhotoUrl,
    approximateDistanceKm: m.approximateDistanceKm,
    matchedAt: m.matchedAt,
    conversationStatus: m.conversationStatus,
    lastMessagePreview: m.lastMessagePreview,
    lastMessageAt: m.lastMessageAt,
    unreadCount: m.unreadCount,
    lastActivityAt: m.lastActivityAt,
  };
}

export function serializeMatchPage(page: Page<MatchListItem>): { items: MatchListItemView[]; nextCursor: string | null } {
  return { items: page.items.map(serializeMatch), nextCursor: page.nextCursor };
}
