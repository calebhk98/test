import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Conversation, Interest, Page } from '../domain/types.js';

/**
 * interest.service — match interests.
 * Spec: §11, §24.6, §25.1 (expiry job).
 *
 * Owning agent: C.
 *
 * Invariants:
 *  - `sendInterest` snapshots policy via
 *    `ctx.config.snapshotPolicy(INTEREST_POLICY_KEYS)` (spec §21.3) into
 *    `interests.policy_snapshot` at creation time — the interest's own
 *    expiry MUST use the snapshotted `interest.expiry_hours`, never a
 *    later-updated config value (spec §21.4 "existing keep original").
 *  - Enforces, at send time: outgoing pending limit, daily outgoing limit,
 *    and (on the recipient's side) that the recipient's incoming pending
 *    count is below their limit — mirrors the discovery visibility rule
 *    (§10.2 rule 5) so an interest can never be sent to someone whose
 *    inbox is already full.
 *  - INVARIANT: `acceptInterest` MUST create (or reuse) exactly one
 *    `conversations` row in the same transaction as the status flip to
 *    'accepted' — see `conversation.service#getOrCreateConversation`. A
 *    caller must never observe `interest.status === 'accepted'` without a
 *    conversation existing.
 *  - `declineInterest` never surfaces the decliner's reasoning to the
 *    sender beyond the generic "They passed on this match." template
 *    (spec §11.4) — that copy lives in `notification.service.ts`'s
 *    template registry, not here.
 */

export async function sendInterest(ctx: Ctx, recipientId: string): Promise<Interest> {
  throw new NotImplementedError('interest.sendInterest');
}

export async function listOutgoing(ctx: Ctx, params?: { cursor?: string; limit?: number }): Promise<Page<Interest>> {
  throw new NotImplementedError('interest.listOutgoing');
}

export async function listIncoming(ctx: Ctx, params?: { cursor?: string; limit?: number }): Promise<Page<Interest>> {
  throw new NotImplementedError('interest.listIncoming');
}

/** Accepts a pending incoming interest. Returns the now-active conversation alongside the updated interest (see invariant above). */
export async function acceptInterest(ctx: Ctx, interestId: string): Promise<{ interest: Interest; conversation: Conversation }> {
  throw new NotImplementedError('interest.acceptInterest');
}

export async function declineInterest(ctx: Ctx, interestId: string): Promise<Interest> {
  throw new NotImplementedError('interest.declineInterest');
}

/** Sender cancels their own pending outgoing interest, freeing their outgoing slot immediately (spec §11.4). */
export async function cancelInterest(ctx: Ctx, interestId: string): Promise<Interest> {
  throw new NotImplementedError('interest.cancelInterest');
}

/** §25.1 job: find pending interests past `expires_at`, mark expired, free the sender's outgoing slot. Runs as `ctx.actor = { type: 'system', job: 'interest_expiry' }`. */
export async function expireDuePendingInterests(ctx: Ctx): Promise<{ expired: number }> {
  throw new NotImplementedError('interest.expireDuePendingInterests');
}
