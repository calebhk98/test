/**
 * src/http/serializers/timeline.ts, the merged conversation timeline wire
 * view.
 *
 * Explicit allowlist over `timeline.service#TimelineEvent` (same
 * discipline `serializers/discovery.ts`/`serializers/profile.ts` already
 * use). Doubles as the enforcement point for `timeline.service.ts`'s own
 * documented omissions, no payment card data, no exact venue
 * coordinates, no raw voucher payload, by construction: this file names
 * every field it forwards, so a field never listed here can never reach
 * the wire even if the service type grew one by accident.
 */
import type { Page } from '../../domain/types.js';
import type { TimelineDateProposalEvent, TimelineEvent, TimelineMessageEvent } from '../../services/timeline.service.js';

export interface TimelineMessageEventView {
  kind: 'message';
  id: string;
  occurredAt: string;
  conversationId: string;
  senderId: string;
  body: string;
  readAt: string | null;
}

export interface TimelineDateProposalEventView {
  kind: TimelineDateProposalEvent['kind'];
  id: string;
  occurredAt: string;
  conversationId: string;
  dateProposalId: string;
  proposerId: string;
  recipientId: string;
  venueName: string;
  scheduledStart: string;
  scheduledEnd: string;
  status: TimelineDateProposalEvent['status'];
  hasTicket: boolean;
}

export type TimelineEventView = TimelineMessageEventView | TimelineDateProposalEventView;

function serializeMessageEvent(e: TimelineMessageEvent): TimelineMessageEventView {
  return {
    kind: 'message',
    id: e.id,
    occurredAt: e.occurredAt,
    conversationId: e.conversationId,
    senderId: e.senderId,
    body: e.body,
    readAt: e.readAt,
  };
}

function serializeDateProposalEvent(e: TimelineDateProposalEvent): TimelineDateProposalEventView {
  return {
    kind: e.kind,
    id: e.id,
    occurredAt: e.occurredAt,
    conversationId: e.conversationId,
    dateProposalId: e.dateProposalId,
    proposerId: e.proposerId,
    recipientId: e.recipientId,
    venueName: e.venueName,
    scheduledStart: e.scheduledStart,
    scheduledEnd: e.scheduledEnd,
    status: e.status,
    hasTicket: e.hasTicket,
  };
}

export function serializeTimelineEvent(e: TimelineEvent): TimelineEventView {
  return e.kind === 'message' ? serializeMessageEvent(e) : serializeDateProposalEvent(e);
}

export function serializeTimelinePage(page: Page<TimelineEvent>): { items: TimelineEventView[]; nextCursor: string | null } {
  return { items: page.items.map(serializeTimelineEvent), nextCursor: page.nextCursor };
}
