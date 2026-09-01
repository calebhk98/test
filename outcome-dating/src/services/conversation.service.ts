import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
import type { Conversation } from '../domain/types.js';

/**
 * conversation.service — conversation lifecycle (not message content —
 * see `message.service.ts`).
 * Spec: §12.1, §12.6, §12.7, §23.13, §24.7, §25.3 (decay job).
 *
 * Owning agent: C.
 *
 * Invariants:
 *  - Exactly one conversation per unordered user pair, enforced by the DB
 *    (`uq_conversations_pair` + `conversations_ordered_pair` requiring
 *    `user_a_id < user_b_id`). `getOrCreateConversation` MUST sort the two
 *    ids before insert/lookup — callers should never do that ordering
 *    themselves.
 *  - `establishConversation` is one-directional: `established` is a
 *    terminal state reached only via a completed date (spec §15.3, §15.4)
 *    and never decays, never re-enters `active`/`cooling`/`archived`
 *    (spec §12.7).
 *  - `runChatDecayJob` MUST NOT touch `established` conversations (spec
 *    §25.3 "Do not archive established conversations") — the query it
 *    issues should filter `status IN ('active', 'cooling')` at the SQL
 *    level (see `idx_conversations_decay_job`), not filter in application
 *    code after the fact.
 */

/** Sorts (userAId, userBId) canonically and inserts if missing, else returns the existing row. Called by `interest.service#acceptInterest` inside its transaction. */
export async function getOrCreateConversation(ctx: Ctx, userAId: string, userBId: string): Promise<Conversation> {
  throw new NotImplementedError('conversation.getOrCreateConversation');
}

export async function listMyConversations(ctx: Ctx, params?: { status?: Conversation['status'] }): Promise<Conversation[]> {
  throw new NotImplementedError('conversation.listMyConversations');
}

export async function getConversation(ctx: Ctx, conversationId: string): Promise<Conversation> {
  throw new NotImplementedError('conversation.getConversation');
}

export async function archiveConversation(ctx: Ctx, conversationId: string): Promise<Conversation> {
  throw new NotImplementedError('conversation.archiveConversation');
}

/** Transitions to 'established' and stamps `first_date_completed_at`. Called by `voucher.service`/`redemption.service`/`dateProposal.service` on date completion (§15.3, §15.4) — never called directly from the HTTP layer. */
export async function establishConversation(ctx: Ctx, conversationId: string): Promise<Conversation> {
  throw new NotImplementedError('conversation.establishConversation');
}

/** §25.3 job: prompt at `chat.date_prompt_hours` since first message with no date proposal, cool at `chat.pre_date_archive_days` minus the prompt window, archive at the full `chat.pre_date_archive_days`. Config keys are 'live' (spec §21.4) — this job always reads current values. */
export async function runChatDecayJob(ctx: Ctx): Promise<{ prompted: number; cooled: number; archived: number }> {
  throw new NotImplementedError('conversation.runChatDecayJob');
}
