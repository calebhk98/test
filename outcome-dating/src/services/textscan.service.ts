import { NotImplementedError } from '../lib/errors.js';
import type { Ctx } from '../lib/ctx.js';
import type { MessageFlagType, TextScanResult } from '../domain/types.js';

/**
 * textscan.service — non-LLM message text analysis.
 * Spec: §12.4, §18.2, §19.3, §19.4.
 *
 * Owning agent: C.
 *
 * HARD INVARIANT (spec §1 rule 9, §12.4, §19.3): regex/keyword/rate-based
 * heuristics ONLY. No LLM call of any kind belongs in this file or
 * anything it calls — this is the one module in the codebase where that
 * constraint is most tempting to break (it "smells like" an NLP task) and
 * most important not to.
 *
 * `scanText` is pure and synchronous (no I/O) so it's trivially unit
 * testable against literal message strings; `message.service.ts` is
 * responsible for the I/O side (persisting `message_flags` rows, checking
 * the caller's trust level against `chat.max_links_per_hour_*`, showing
 * the §12.5 static banner).
 *
 * Detection categories (spec §19.3): crypto, gift cards, wire transfer,
 * cashapp/venmo/zelle, emergency money, investment offers, telegram/
 * whatsapp links, adult-content promotion — plus §23.15's flag_type set
 * (external_contact, money_request, link, crypto, spam_pattern,
 * abuse_pattern). `PATTERN_GROUPS` below is the exported, testable list of
 * regexes backing each flag_type; extend it rather than inlining new
 * regexes elsewhere.
 */

export interface PatternGroup {
  flagType: MessageFlagType;
  /** Severity 1-5 assigned when this group matches (spec §23.15 message_flags.severity). */
  severity: number;
  patterns: RegExp[];
}

/**
 * The regex/keyword rule set. Exported (not private) so tests can assert
 * against it directly and so `moderation.service.ts` can reference flag
 * severities without re-deriving them. Populated with representative
 * patterns per category; extending coverage is expected to happen here,
 * not by adding scan logic elsewhere.
 */
export const PATTERN_GROUPS: PatternGroup[] = [
  {
    flagType: 'link',
    severity: 1,
    patterns: [/https?:\/\/\S+/i, /\b[a-z0-9-]+\.(com|net|org|io|co)\b/i],
  },
  {
    flagType: 'external_contact',
    severity: 2,
    patterns: [
      /\b(instagram|insta|ig)\b[:\s@]*[\w.]+/i,
      /\b(snap(chat)?|telegram|whatsapp|wa\.me)\b/i,
      /\b\+?\d[\d\s().-]{7,}\d\b/, // phone-number-shaped sequences
    ],
  },
  {
    flagType: 'money_request',
    severity: 4,
    patterns: [
      /\b(cash ?app|venmo|zelle|wire transfer|western union|moneygram)\b/i,
      /\b(send|wire|need)\s+(me\s+)?\$?\d+/i,
      /\bemergency\b.{0,20}\bmoney\b/i,
    ],
  },
  {
    flagType: 'crypto',
    severity: 4,
    patterns: [/\b(bitcoin|btc|ethereum|eth|crypto|usdt|binance|metamask)\b/i, /\binvest(ment|ing)?\s+opportunity\b/i],
  },
  {
    flagType: 'spam_pattern',
    severity: 3,
    patterns: [/(.)\1{9,}/, /\b(subscribe|follow me|check out my)\b/i],
  },
  {
    flagType: 'abuse_pattern',
    severity: 5,
    patterns: [], // populated by moderation-config-driven keyword lists at runtime, not hardcoded here
  },
];

/**
 * Scan one message body and return every matching flag plus whether a
 * §12.5 safety banner should render. Per spec §19.3/§12.5, matches never
 * block sending by default — that policy decision belongs to
 * `message.service.ts`, not here.
 */
export function scanText(ctx: Ctx, body: string): TextScanResult {
  throw new NotImplementedError('textscan.scanText');
}
