/**
 * §25.3 Chat Cooling/Archival job. "Find pre-date conversations: no date
 * proposal after 72 hours -> prompt; after 14 days -> cooling; after 21
 * days -> archive. Do not archive established conversations." — exactly
 * `conversation.service#runChatDecayJob`, whose own SQL only ever selects
 * `status IN ('active','cooling')` rows, so an `established` conversation
 * is never even a candidate (see that function's doc comment) — the "never
 * archive established" rule is structural, not a check this wrapper needs
 * to re-verify.
 */
import type { Ctx } from '../lib/ctx.js';
import { runChatDecayJob } from '../services/conversation.service.js';
import type { JobDefinition } from './types.js';

export async function runChatCoolingArchivalJob(ctx: Ctx): Promise<{ prompted: number; cooled: number; archived: number }> {
  return runChatDecayJob(ctx);
}

export const chatDecayJob: JobDefinition = {
  name: 'chat_decay',
  description: 'Prompt/cool/archive pre-date conversations at the 72h/14d/21d thresholds; established chats are untouched (§25.3).',
  intervalMs: 15 * 60 * 1000,
  run: runChatCoolingArchivalJob,
};
