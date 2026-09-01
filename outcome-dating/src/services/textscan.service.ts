import type { Ctx } from '../lib/ctx.js';
import type { MessageFlagType, TextScanResult } from '../domain/types.js';

/**
 * textscan.service, non-LLM message text analysis.
 * Spec: §12.4, §18.2, §19.3, §19.4.
 *
 * Owning agent: C.
 *
 * HARD INVARIANT (spec §1 rule 9, §12.4, §19.3): regex/keyword/rate-based
 * heuristics ONLY. No LLM call of any kind belongs in this file or
 * anything it calls, this is the one module in the codebase where that
 * constraint is most tempting to break (it "smells like" an NLP task) and
 * most important not to.
 *
 * `scanText` is pure and synchronous (no I/O) so it's trivially unit
 * testable against literal message strings; `message.service.ts` is
 * responsible for the I/O side (persisting `message_flags` rows, checking
 * the caller's trust level against `chat.max_links_per_hour_*`, showing
 * the §12.5 static banner). `ctx` is accepted (and currently unused) only
 * to keep the signature stable if a future revision wants config-driven
 * pattern lists, do not read `ctx.db`/network from here; that would
 * violate "no I/O".
 *
 * Detection categories (spec §19.3): crypto, gift cards, wire transfer,
 * cashapp/venmo/zelle, emergency money, investment offers, telegram/
 * whatsapp links, adult-content promotion, plus §23.15's flag_type set
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
 *
 * False-positive notes (see tests/unit/textscan.test.ts):
 *  - The phone-number patterns require a classic 3-3-4 digit grouping (or
 *    a leading "+" international run) rather than "any long run of
 *    digits/separators", a loose version of that regex matches dotted
 *    dates like "3.15.2026" (a 1-2-4 grouping), which is exactly the kind
 *    of false positive spec §19.3 warns against ("Some normal users share
 *    links or social handles... Blocking creates bad UX", the same logic
 *    applies to over-flagging).
 *  - "cash app"/"venmo"/etc. still match as a plain substring regardless
 *    of surrounding context (e.g. a "my cash app of tea"-style pun on "my
 *    cup of tea"), regexes cannot understand puns, so this is expected
 *    to flag. That's fine per spec §19.3: matches never block sending by
 *    default, they only flag internally, so an ambiguous/near-miss match
 *    costs nothing but a low-severity flag row.
 */
export const PATTERN_GROUPS: PatternGroup[] = [
  {
    flagType: 'link',
    severity: 1,
    patterns: [/https?:\/\/\S+/i, /\bwww\.[a-z0-9-]+\.[a-z]{2,}\b/i, /\b[a-z0-9-]{2,}\.(com|net|org|io|co)\b/i],
  },
  {
    flagType: 'external_contact',
    severity: 2,
    patterns: [
      /\b(instagram|insta|ig)\b[:\s@]*[\w.]+/i,
      /\b(snap(chat)?|telegram|whatsapp|wa\.me|t\.me)\b/i,
      // Classic 3-3-4 grouping: 555-123-4567 / (555) 123-4567 / 555.123.4567.
      // Deliberately NOT a loose "any long digit run", that false-positives
      // on dotted dates like "3.15.2026" (a 1-2-4 grouping, not 3-3-4).
      /(?<!\d)(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)/,
      // Bare international run, e.g. +14155552671.
      /(?<!\d)\+\d{7,14}(?!\d)/,
    ],
  },
  {
    flagType: 'money_request',
    severity: 4,
    patterns: [
      /\b(cash ?app|venmo|zelle|wire transfer|western union|moneygram)\b/i,
      /\b(gift ?cards?|itunes card|google play card|steam card)\b/i,
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
    patterns: [
      /(.)\1{9,}/,
      /\b(subscribe|follow me|check out my)\b/i,
      /\b(onlyfans|only ?fans|cam ?girl|sell(ing)? (nudes|content))\b/i, // adult-content promotion (§19.3)
    ],
  },
  {
    flagType: 'abuse_pattern',
    severity: 5,
    patterns: [], // populated by moderation-config-driven keyword lists at runtime, not hardcoded here
  },
];

/**
 * Reason codes for the §12.5/§19.3 safety banner. `message.service.ts`
 * maps this into the single static `safety_notice` notification template's
 * `payload.reason`, it is NOT itself a notification template key, so the
 * "exactly one static template per event" invariant
 * (`notification.service.ts#NOTIFICATION_TEMPLATES`) stays intact even
 * though there are two distinct banner situations.
 */
export const OFF_APP_BANNER_REASON = 'off_app_handle' as const;
export const SCAM_RISK_BANNER_REASON = 'scam_risk' as const;

/**
 * Scan one message body and return every matching flag plus whether a
 * §12.5 safety banner should render. Per spec §19.3/§12.5, matches never
 * block sending by default, that policy decision belongs to
 * `message.service.ts`, not here.
 */
export function scanText(ctx: Ctx, body: string): TextScanResult {
  void ctx; // see file header: accepted for signature stability, unused today.

  const flags: TextScanResult['flags'] = [];
  for (const group of PATTERN_GROUPS) {
    for (const pattern of group.patterns) {
      const match = pattern.exec(body);
      if (match) {
        // One flag per group per message is enough, multiple patterns in
        // the same group matching the same message shouldn't produce
        // duplicate flag rows of the same type.
        flags.push({ type: group.flagType, severity: group.severity, matchedPattern: pattern.source });
        break;
      }
    }
  }

  // §12.5: URL or off-app handle -> venue-perks/safety-verification notice.
  const hasOffAppSignal = flags.some((f) => f.type === 'external_contact' || f.type === 'link');
  // §19.3: money/crypto solicitation -> a more urgent scam-risk notice.
  const hasScamSignal = flags.some((f) => f.type === 'money_request' || f.type === 'crypto');

  let showSafetyBanner = false;
  let safetyBannerTemplateKey: string | null = null;
  if (hasScamSignal) {
    showSafetyBanner = true;
    safetyBannerTemplateKey = SCAM_RISK_BANNER_REASON;
  } else if (hasOffAppSignal) {
    showSafetyBanner = true;
    safetyBannerTemplateKey = OFF_APP_BANNER_REASON;
  }

  return { flags, showSafetyBanner, safetyBannerTemplateKey };
}

/** First link-shaped substring in `body`, or null. Used by `message.service.ts` to feed `decideLinkPresentation` without re-implementing the `link` pattern group's matching. */
export function extractFirstLink(body: string): string | null {
  const linkGroup = PATTERN_GROUPS.find((g) => g.flagType === 'link');
  if (!linkGroup) return null;
  for (const pattern of linkGroup.patterns) {
    const match = pattern.exec(body);
    if (match) return match[0];
  }
  return null;
}

/**
 * Curated allowlist for the §19.4 "known domain" check, not exhaustive,
 * just enough to distinguish common legitimate destinations from anything
 * else. A domain LIST heuristic (spec §12.4), never inferred by a model.
 */
export const KNOWN_SAFE_DOMAINS: ReadonlySet<string> = new Set([
  'instagram.com',
  'facebook.com',
  'twitter.com',
  'x.com',
  'linkedin.com',
  'spotify.com',
  'strava.com',
  'youtube.com',
  'google.com',
  'maps.google.com',
  'yelp.com',
  'opentable.com',
  'eventbrite.com',
]);

/** Extracts a lowercased, `www.`-stripped hostname from a URL or bare domain-like token. Best-effort/pure, never throws, returns null on anything unparseable. */
export function extractDomain(text: string): string | null {
  const withScheme = /^https?:\/\//i.test(text) ? text : `https://${text}`;
  try {
    const host = new URL(withScheme).hostname.toLowerCase();
    return host.startsWith('www.') ? host.slice(4) : host;
  } catch {
    return null;
  }
}

export interface LinkPresentationInput {
  url: string;
  /**
   * Resolved by the caller via `trust.service#canSendClickableLinks`,
   * this function never re-derives that decision from a raw trust level
   * (spec direction: "call it, do not reimplement scoring").
   */
  canSendClickableLinks: boolean;
  linksSentInLastHour: number;
  linkLimitPerHour: number;
}

export interface LinkPresentationDecision {
  clickable: boolean;
  /** Only meaningful when `clickable` is true (spec §19.4 "show warning if domain is unknown"). */
  unknownDomainWarning: boolean;
}

/**
 * Pure §19.4 presentation decision for one detected link: not clickable
 * for low-trust senders (or once the sender's hourly link quota is spent);
 * clickable-with-a-warning for an unrecognized domain otherwise. Never
 * modifies the message body, the caller renders the raw text as-is and
 * uses this decision only for how to *present* it.
 */
export function decideLinkPresentation(input: LinkPresentationInput): LinkPresentationDecision {
  const withinHourlyQuota = input.linksSentInLastHour < input.linkLimitPerHour;
  const clickable = input.canSendClickableLinks && withinHourlyQuota;
  if (!clickable) return { clickable: false, unknownDomainWarning: false };
  const domain = extractDomain(input.url);
  const unknownDomainWarning = domain === null || !KNOWN_SAFE_DOMAINS.has(domain);
  return { clickable: true, unknownDomainWarning };
}
