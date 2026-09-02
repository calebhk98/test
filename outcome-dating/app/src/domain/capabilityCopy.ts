import type { CapabilityReasonCode } from '../api/types';

/** Static, safe reason codes (trust.service.ts's own doc: "carries no weights") turned into a sentence, so a disabled action reads as a reason, never a bare 403. */
export const REASON_MESSAGES: Record<CapabilityReasonCode, string> = {
  payment_method_required: 'Add a payment method to do this. A hold is only ever placed if you propose or accept a date.',
  reduced_quota_low_trust: "Your daily limit for this is temporarily reduced while we build trust with your account.",
  links_disabled_low_trust: "Links aren't allowed in chat yet for your account.",
  links_warning_standard_trust: 'Be careful with links from people you just matched with.',
};

export function messageForReasonCode(code: CapabilityReasonCode | undefined): string | null {
  if (!code) return null;
  return REASON_MESSAGES[code] ?? null;
}
