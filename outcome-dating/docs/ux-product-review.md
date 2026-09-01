# UX walkthrough: a person downloads this app on a Tuesday evening

A product read, not a code read: walking the app the way a real person would experience it, using the spec for intent and the backend for what a client could actually do. This is a copy and product-flow review, not a bug list; findings are recommendations for whoever writes client-facing copy, not code defects.

**The original headline finding is resolved.** The review originally warned that the better of two parallel question systems (typed, ladder control, deal-breaker importance, real skip) had no HTTP route, so a client shipped today would ship with the older, worse system (no skip, no "don't care," meaningless midpoints) that user testing had already flagged. Both routes are now wired and the old system is gone entirely (see `docs/ux-api-review.md`). The rest of this document's observations about pacing, copy, and moments of friction are still worth reading for a client build.

## Moments most likely to cause abandonment, in order

1. **The payment-hold moment, if "hold" reads as "charge."** The proposer's card gets an authorization hold the instant a date proposal is sent, released automatically on decline/expiry/cancel. Nothing in a normal person's vocabulary distinguishes "hold" from "charge," and if the eventual client copy collapses that distinction, this is a trust rupture at the single most sensitive screen in the product. Say plainly, before the card is collected: *"Sending this date invite places a $20 hold on your card, like a hotel deposit. Nothing is charged unless [Name] accepts."* Never let a backend status leak in verbatim (`payment_failed`, `disputed`, `canceled` are internal enum values, not sentences).
2. **An unexplained empty or thin discovery grid**, especially outside a major city. The reality dashboard (matching-filter counts, whose-filters-you-match counts, mutual pool size) is the right tool for this and already exists, but it's opt-in to view. Surface it proactively the first time a grid comes back thin, rather than waiting for someone to go looking for it.
3. **Photo rejection with no explanation.** With no human reviewers, the copy has to do all the work of making a rejection feel fixable rather than accusatory. A missing-face rejection and a nudity-flag rejection currently read identically from outside; they need different, specific sentences (see the copy audit below).
4. **A wrongly-restricted new account with no real appeal lever for 30 days.** The `existing_signals` appeal path (the one that doesn't need a camera or a card) is gated behind 30 days of account age, which is exactly backwards from who's most likely to be a false positive. Rare, but severe when it happens.

## Copy audit: two places that need the most work before a client ships

1. **Anything payment-related.** "Hold" vs "charge," a generic "payment failed" vs a human explanation of what happens next, "disputed" vs "we're waiting on them to confirm." Backend enum values will otherwise leak directly into user-facing text.
2. **Rejection and restriction moments** (photo rejection, trust restriction, appeal denial). These are exactly the moments a person is most likely to feel judged, and the code currently exposes them as terse reason codes (`nudity_detected`, `primary_photo_missing_face`) rather than sentences. Example replacements:
   - Missing face: *"We couldn't find a clear face in this photo. Your first photo needs to show your face so matches know who they're talking to."*
   - Flagged content: *"This photo can't be used, it looks like it may contain [nudity / a weapon / content we don't allow]. Try a different photo."* Never accuse of intent, describe what was detected.
   - A merely-flagged (not rejected) non-primary photo should say so gently: *"This photo is a little blurry, it's on your profile, but we won't use it as your first photo."*

**Protect the vague/generic copy that's already there on purpose.** The generic decline template ("They passed on this match.") and the generic mutual-eligibility refusal are both deliberately vague, to protect the other party's privacy and dignity. Don't let a future "more transparency" push add detail back into either.

## Other moments worth writing copy for carefully

- **The 48-hour interest/proposal clock**, described as a countdown, reads as pressure; described as a fact ("This request is open until [date]") does not.
- **The 72-hour chat-decay prompt** needs to read as an invitation with a free, unrecorded "not yet" dismissal, never as the app judging the pace of two people's relationship.
- **A single-sided attendance confirmation** (`disputed` state) should never say "disputed" to the user; from the honest confirmer's side it looks exactly like being stood up. *"We're waiting on your date to also confirm you both showed up."*
- **A failed payment authorization on either side** should be blame-neutral and give both people the same explanation, not a generic "payment failed" with no next step.

## What's genuinely good and should be protected from "helpful" changes

No like counts, no boosts, no popularity signal anywhere in the wire format (one field-addition away from being undone by a future growth experiment); the generic decline and generic refusal copy; the escrow structure's careful failure handling (a failed second capture refunds the first rather than leaving one person charged); the four-outcome post-date check-in instead of a single star rating; venue staff's narrow view (names and times only); and the reality dashboard's honesty about a thin market instead of papering over it with fake profiles.

## Accessibility and inclusion notes

The payment-hold model structurally excludes anyone without a card that can sustain a hold; there's no fallback tier. The 48-hour/72-hour clocks assume someone checks the app every day or two, which disadvantages irregular schedules (shift work, caregiving, travel) with no way to signal "I'm slow to respond right now." The face-photo requirement is a reasonable catfishing deterrent but deserves a sympathetic exception path in copy for anyone whose face genuinely can't be the lead photo.
