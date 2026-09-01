# UX walkthrough: a person downloads this app on a Tuesday evening

This is a product read, not a code read. I walked the app the way a real person would experience it — moment by moment — using the spec for intent and the actual backend (`routeTable.ts`, `src/services/`) for what a client could really do today. Where the two disagree, I say so, because that gap is itself a UX finding.

One thing up front, because it changes how to read everything below: **the backend contains two parallel question systems.** The old one is a plain 1–5 self/partner scale, reachable today at `GET /questions` / `PUT /me/answers` — the exact shape user testing already flagged (meaningless midpoints, no "don't care," no deal-breaker, no skip). A second, clearly better system exists in `src/domain/questions/` and `question.service.ts` — typed questions, a "ladder" control for yes/no preferences, deal-breaker/irrelevant/critical importance levels, skip with cooldown, prefer-not-to-say — but it has **no HTTP route.** `routeTable.ts` §24.3 only wires the old endpoints. So today, if a client shipped against this backend as-is, it would ship with exactly the broken question experience the redesign was built to replace, because the redesign is unreachable. I treat this as the single biggest risk in the whole review — see the end.

---

## 1. First launch and signup

**What happens:** email, password, date of birth, terms, city (or location permission). `POST /auth/register`. No phone number, no government ID required — genuinely good, and rare in this category. A person who has been burned by ID-verification dating apps before will feel that immediately, if the app ever tells them so.

**What I'd change:** it currently doesn't tell them so. Nothing in the signup flow says out loud that this app isn't going to ask for their ID or phone number — a real point of relief for a lot of people (especially anyone who's had a bad experience being asked to hand a stranger's app a driver's license photo) is being left on the table. One line on the signup screen:

> "No phone number, no ID required to get started."

**Then what:** to become visible to anyone else, the actual gate (per `computeProfileCompleteness` in `profile.service.ts`) is lower than the spec's ten-item profile list implies. The math: display name (15) + city (10) + age/gender/seeking/relationship-intention (10) + one approved photo (20) = 55, which clears the 50-point `discovery.min_profile_completeness` threshold. Bio and compatibility questions are **not required** to appear in the grid.

That's a real design tension, and it cuts two ways:
- **Good:** an impatient person can be looking at real human faces after roughly four fields and one photo. That's a short wall, shorter than the spec's ordering ("questions, filters, and photos before discovery is useful") suggests.
- **Bad:** because compatibility scoring needs at least 3 mutually-answered questions to produce anything other than a flat 0 (`DEFAULT_MIN_SHARED_QUESTIONS = 3`, `DEFAULT_NO_DATA_SCORE = 0`), a person who rushes past the questions to get to the grid gets a grid that is sorted by nothing meaningful. The product's headline promise — "sorted by compatibility, not popularity" — quietly degrades to "sorted arbitrarily" for exactly the impatient users most likely to bounce off a survey. They experience the cost of skipping (a worse grid) without ever being told that's why.

**What I'd change:** don't gate discovery on 5 answered questions (too much friction, and the current build doesn't anyway) — but do tell a person, once, the trade they're making. After the third skip in a row, one line, no button required to dismiss it:

> "Skipping ahead — you'll see more people, but matches won't be sorted by compatibility yet. Answer a few when you're ready and we'll re-sort."

That converts an invisible quality cliff into an informed choice, which is the difference between "this app's matching feels random" (a trust-destroying impression) and "I chose to skip ahead" (a shrug).

---

## 2. The question flow

**What's reachable today** is the old system: `GET /questions` returns the *entire* active bank in one call, ordered by category then question text — there is no "next questions to show" endpoint, no pacing, no selector logic at all for the live routes. A client would have to invent its own pacing on top of a flat list of (per the spec's "hundreds of questions" design) 600+ rows. That is a bad foundation for "doesn't feel like a survey" — the server isn't helping.

**What exists but isn't wired** is much better: `selectNextQuestionsForMe` in `question.service.ts` prioritizes by answer-rate (ask easy/likely-to-answer questions first), information value, and category balance, so early questions are the ones people actually finish and the categories stay mixed rather than exhausting "religion" before ever touching "hobbies." It supports real skip (with a 14-day cooldown before a skipped question resurfaces) and "prefer not to say" as a first-class answer, not a workaround. This is the fix for the exact user-testing complaint ("no way to skip a question") — it just isn't reachable by any route yet.

On the **old, reachable** system specifically:
- There is no skip endpoint. A user either answers a question (`PUT /me/answers`) or the client just doesn't ask about it — nothing server-side remembers "I chose not to answer this," so a naive client would either re-show it forever or silently drop it with no signal to the algorithm.
- "Prefer not to say" (null/null) is only legal on questions flagged `sensitive`. On a non-sensitive question — which is most of the bank — the API rejects a null with a validation error. A person facing "How important is a clean apartment to you?" who genuinely has no strong feeling has no way to say so; they have to either fabricate a 3 (mid-scale, itself flagged elsewhere as a meaningless dodge) or leave it blank and hope.
- Both self and partner value are required together. There's no "I'll tell you about me but I'm not ready to say what I want in a partner" — a real hesitation for younger or newly-out users on sensitive topics.

**What I'd change, in order of impact:**
1. Wire the new question-bank routes before shipping a client — everything about the pacing, skip, and deal-breaker experience depends on it, and it already exists.
2. On the new system, cap a single sitting at a small, told number — 8–10 questions, not "however many the client decides." Show progress honestly: "Question 4 of 8 for now — more later." A visible, small, finishable number is what keeps this from feeling like a survey; an open-ended flat list of 600 (the old system's shape) guarantees it will.
3. After that first batch, stop and let them into the grid, with a light, recurring invitation later ("2 quick ones based on who you've been matching with") rather than a wall.
4. Every question needs a visible, always-present "Skip" and, where sensitive, "Prefer not to say" — never buried in a menu. The new ladder control already gives a "Don't care" mid-position for yes/no questions, which is exactly right; make sure the client surfaces it as a real position on the control, not a tiny link below it.

**Copy** — the new system has no midpoint problem for binary preferences (the ladder's center position is `Don't care`, not an unlabeled 3), but for the remaining `scale` type questions the spec requires a labeled midpoint too (`ScaleDefinition.midLabel` is mandatory in the type). A client must never render a bare number line — every position needs words. For a still-live example, "Pets" per spec section text:

> 1 = I do not like pets · 2 = I am okay without pets · 3 = Neutral · 4 = I like pets · 5 = I have pets / love pets

That's fine because 3 = Neutral is an actual, meaningful answer for this particular question — the earlier failure mode ("a scale from 'no kids' to 'has kids' where the midpoint meant nothing") happens when a *categorical* fact gets forced onto this shape. The type system now prevents that structurally (categorical facts are `single_choice`, which never gets an unlabeled numeric midpoint) — that's the real fix, and it's worth protecting: don't let a future "quick win" question get authored as a `scale` because it's less admin work, if it's actually describing a category.

---

## 3. Photos

**The moment:** first photo upload gates visibility (`user_photos`, needs at least one `approved` photo). The primary photo specifically must have a detected face — `analyzePhoto` runs synchronously on upload.

**What rejection feels like today:** the service returns a `rejectionReasons` array (`nudity_detected`, `weapons_detected`, `illegal_content_detected`, `primary_photo_missing_face`) and a `ValidationError` when someone tries to set a faceless photo as primary. That's useful *data*, but nothing server-side softens it into something a rejected person can act on without feeling accused. A photo of someone at a concert, backlit, half-turned — genuinely their own photo — can get "no face detected" and land the same as if it had been flagged for nudity, unless the client is careful to separate these.

**This matters more than it looks like**, because there are no human reviewers (spec §18.1, structurally enforced — `PhotoModerationStatus` has no "pending human review" state at all). A false rejection has no appeal path except "try a different photo." For someone whose only photos are group shots, side profiles, or low light — which is disproportionately likely for older users, users with disabilities that affect a face-forward photo, or users who just don't have a phone with a great camera — this can be a hard wall with no acknowledgment that it might be the system's mistake, not theirs.

**What I'd change:**
- Never say "rejected." Say what happened and what to try, specific to the actual reason:
  - Missing face on primary: **"We couldn't find a clear face in this photo. Your first photo needs to show your face so matches know who they're talking to — try a photo facing the camera, without sunglasses or a hat, and with decent light."**
  - Flagged content (nudity/weapons/illegal): **"This photo can't be used — it looks like it may contain [nudity / a weapon / content we don't allow]. Try a different photo."** (Never accuse of intent; describe what was detected, plainly.)
  - Flagged as duplicate: **"This photo appears to be used on another profile. If this is genuinely you, try a different photo, or contact support if you believe this is a mistake."** — this one deserves an actual human-reachable path (email, not a form into a void) because a false duplicate match (e.g. two people who share a professional headshot, or a reused old photo the user themselves posted elsewhere first) is exactly the case automation gets wrong and the person has no way to prove otherwise from inside the product.
- Non-primary photos that are merely `flagged` (blurry, group photo) should say so gently and explain the photo is visible but not first: **"This photo is a little blurry — it's on your profile, but we won't use it as your first photo."** Right now `flagged` and `rejected` both read as failure states from outside; only one of them is.
- Give people a second and third try without punishment. Nothing in the code rate-limits or penalizes repeated uploads, which is right — just make sure the client doesn't invent a cooldown that isn't there.

**What's genuinely good and worth protecting:** the reorder/primary-photo endpoints and the A/B testing groundwork (`photoExperiment.service.ts`, impressions vs. accepted interests) are the correct way to solve "most users don't know their best photo" — data over generic advice, exactly as the spec argues. Just make sure the eventual recommendation copy stays a recommendation, not an automatic silent swap, per spec §7.3's own carve-out ("user should be able to approve or reject").

---

## 4. First look at discovery

**The moment:** a grid, sorted by compatibility, no like counts, no boosts. This is one of the product's best decisions and it shows in the code — `serializeDiscoveryCandidate` is an explicit allowlist that structurally cannot leak a popularity number, with a comment making the intent explicit. Protect this hard; it is very easy for a future "engagement" push to sneak a like-count or a "🔥 popular" badge back in, and the whole differentiation from swipe apps rides on not doing that.

**One thing that quietly works against that intent:** the discovery card includes `trustLevel` (Limited / Standard / Trusted / Elite) on every candidate — visible to anyone browsing, not just self. That's not in the spec's card field list (photo, name, age, distance, one shared interest), and even though it's not literally a popularity number, a visible tier badge on strangers functions as one — it invites exactly the "herd behavior and status games" the spec's own reasoning for banning like-counts and boosts warns about. A new, honest, Standard-trust user sitting next to Trusted and Elite badges reads as "less legitimate" even though the difference might just be account age. I'd either drop it from the card entirely (trust already gates who's visible and what they can do — it doesn't need to also be a rank on display) or fold it into something purely functional and non-comparative, like a small "recently active" indicator that doesn't imply a ladder.

**Thin or empty grid, day one, small city:** the reality dashboard (`GET /discovery/reality`) is a genuinely good, honest feature — showing "people who match your filters," "people whose filters match you," and the mutual pool size, rather than pretending the pool is bigger than it is. But it's opt-in to look at; the default empty-grid moment is where most people will actually be sitting, and the spec's own placeholder text is flat:

> "No candidates currently match your filters. Try widening distance or age range."

That's honest but not warm, and it doesn't distinguish "you have zero filters and there's genuinely nobody near you yet" (a cold-start problem, not the user's fault) from "your filters are unusually narrow" (an easy fix). I'd write it as two different states:

- **No filters set, pool still empty (genuine cold start):** "Nobody's nearby yet — you're early here. Widen your distance, or check back soon; new people join every day." (Never fabricate profiles to fill the gap — the spec is explicit about this, correctly.)
- **Filters are the likely cause:** "Your filters are excluding everyone nearby right now. [See what's filtering them out →]" linking to the reality dashboard, with the X/Y/Z counts front and center instead of buried behind a second screen most people won't think to visit.

A small-city user is going to hit this constantly, not just on day one — and repeatedly seeing "no candidates" with no path forward is one of the clearest reasons to uninstall in the whole product. Surface the reality dashboard *proactively* the first time the grid comes back thin (say, under 5 people), rather than waiting for someone to go looking for it.

---

## 5. Sending interest

**The moment:** an interest is a request to talk, capped at 5 outgoing pending (2 for Limited-trust accounts), no message attached, 48-hour expiry, 20/day. `sendInterest`'s function signature structurally has no field for a message — a nice guarantee that "no free text before match" can't be bypassed even by accident.

**How it lands:** for someone coming from swipe apps, "no message with the like" will read as a real behavior change, and probably a relief for anyone who's been on the receiving end of an unsolicited opener. But it removes the one thing that usually makes a like feel *considered* rather than automatic — there's nothing to distinguish "I read your profile and this is deliberate" from "I tapped through a stack." The grid-not-a-deck framing and shared-interest tag help (seeing one thing you have in common with someone before you decide), but I'd make sure the profile view itself, not just the card, is the thing people are shown before they send — sending interest should feel like it followed reading, not browsing.

**Hitting the cap:** `You have reached your pending interest limit.\nWait for responses or expiration.` — flat and a little bureaucratic, but functional. I'd warm it slightly and make it feel like a design choice, not a wall:

> "You've got 5 requests out right now — that's the most at once. Once someone responds (or 48 hours passes), you'll have room to send another."

**One sharp edge worth flagging:** when a send is refused because the recipient's filters would exclude the sender (a real, common case — Layer 2 eligibility check), the copy is deliberately identical to "this person's inbox is full" — *This person cannot receive new interests right now.* That's a deliberate and good anti-probing decision (so nobody can fish out someone's filter preferences by testing sends), but it means a person who gets this message repeatedly across different profiles has no way to learn "oh, it's my own filters that are the problem" versus "everyone I like happens to be busy" — which is exactly the kind of silent, confusing pattern the spec's whole "hidden filter behavior" ban is trying to prevent from the *sender's own* filter-setting side. I'd solve it without touching the anti-probing copy: if a person hits this message 3+ times in a session, show a *separate*, self-directed nudge, not about the recipient — "Not connecting? Double check your own filters aren't narrower than you meant" — linking to their filter settings. That's about the sender's own state, so it can't leak anything about anyone else.

---

## 6. Receiving interest

**The moment:** up to 10 pending at once, 48-hour clock per interest. This protects a popular profile from being buried, and gives a normal person a bounded, checkable-in-one-sitting inbox rather than an infinite scroll — genuinely good, and the trust-tiered outgoing cap (2 for Limited accounts) means new/unverified accounts can't flood it.

**The pressure question:** a 48-hour clock on every incoming interest is a real design tension. It protects the *sender* from a request that sits forever, but it puts a soft deadline on the *recipient* too — "decide about this stranger within two days or it vanishes." For someone who wants to think about it, or who's simply busy that week, the app is quietly making the decision for them by omission. I'd make expiry visible and unalarming rather than a countdown — "Expires in 2 days" reads as pressure; "This request is open until [date]" reads as a fact. Small wording difference, real effect on how it feels to open the inbox.

**Decline, from both sides:** the sender sees a single, deliberately generic template — *"They passed on this match."* — never a reason, never who. That's the right call; it protects the decliner from having to justify themselves and protects the sender from a harsher, specific rejection. I'd keep it exactly as-is; this is one of the places genericness is a feature, not a corner cut. On the recipient's side, declining should be zero-friction and require no reason from them either — nothing in the code forces one, which is correct.

---

## 7. The chat

**Unlock:** only after mutual accept — no unsolicited messages, ever. Good, simple, and matches how people actually expect a dating app's DMs to work versus generic social messaging.

**Decay:** 72 hours with no date proposal → a prompt; 14 days → "cooling"; 21 days → archived. Established (post-date) chats never decay. This is a real and reasonable design bet — "the app should encourage dates but not force weekly dating just to keep a conversation" — but the 72-hour prompt is the one moment most likely to feel like being nagged, especially for two people who are genuinely just enjoying talking and aren't ready to commit money and a calendar slot to each other yet. Whatever that prompt says needs to read as an invitation, never a deadline:

> "You two have been chatting a few days — want to suggest a coffee, a walk, or something low-key?" with a clear, equally-visible "Not yet" dismissal that doesn't cost anything (no counter, no visible "declined to plan a date" signal to the other person).

The failure mode to avoid: if the prompt (or the eventual cooling/archive notice) reads as the app judging the pace of two people's actual relationship, that's the moment it stops feeling like a tool and starts feeling like a landlord. Cooling and archive notices should be equally soft — "this conversation's gone quiet, want to pick it back up or let it go?" — never "your match has expired," which implies the *people* expired, not the chat window.

**Off-platform nudges:** when a message contains a handle, phone number, or link, the message still sends (never blocked — correct), with a banner. Spec's own copy for this is genuinely good and worth keeping verbatim:

> "Booking your first date through the app includes venue perks and safety verification."

That's a positive-framed nudge toward the app's actual value (real perks, real safety) rather than a scold about leaving. Good tone; protect it as the template if link-handling copy ever gets rewritten.

---

## 8. The money moment

This is the moment that will make or break trust in the whole product, and it deserves the most careful walk.

**What actually happens, per `dateProposal.service.ts`:** the **proposer's card is placed on hold the instant they send the date proposal** — before the other person has said anything. It's an authorization hold, not a charge (no money moves), and it's released automatically if the recipient declines, if the proposal expires unanswered (48h default), or if the proposer cancels first. But a normal person reading "add a payment method to propose a date" for the first time does not know the difference between "hold" and "charge" — those words mean the same thing to almost everyone outside of banking. If the UI says anything close to "your card will be charged," or even just shows a hold as a pending transaction on their bank app (which it will), the natural reaction is *"wait, they haven't even said yes and my card already shows a pending $20 charge?"* That's a trust rupture at the single most sensitive moment in the product, and it's avoidable with clear language:

> **"Sending this date invite places a $20 hold on your card — like a hotel deposit. Nothing is charged unless [Name] accepts. If they don't respond within 48 hours, the hold is automatically released."**

That sentence needs to appear *before* the payment method is collected, not after, and it needs to say what happens if the answer is no, out loud, before it happens — that's the single biggest thing that will make this feel safe instead of alarming: **telling someone what happens on decline, before they commit their card.**

**What the recipient sees:** they only need to add a card at the moment they choose to accept an actual invitation with a real time, place, and person attached — not up front at signup (correctly enforced: spec §6.4 requires a payment method only for date proposals, not for browsing or chatting). That sequencing is right. But the same hold-vs-charge clarity applies in reverse, with an extra wrinkle: if the recipient accepts and their own authorization fails (declined card, insufficient funds), the proposer's hold is released and **both** get notified — good, no one is left wondering why nothing happened. Make that notification explicit and blame-neutral for both sides:

> To the recipient: **"Your card couldn't be authorized for this date. No one's been charged. Try a different card, or let them know you can't make it."**
> To the proposer: **"[Name]'s payment couldn't go through, so this date didn't happen. Nothing was charged to you."**

Never say "payment failed" alone with no next step — that's the coldest, most clinical version of this moment and it's exactly the default a backend error message will produce if nobody writes copy for it.

**What people will be afraid of, specifically, and what actually protects them:**
- *"What if I get scammed and never get my money back?"* — the escrow model (hold → capture only after both sides commit → refund on cancellation per policy) is genuinely the right structural answer to this fear, and the code enforces "never charge one side alone" carefully (a failed second capture triggers a refund of the first, not a silent write-off). This deserves to be said plainly in the product, once, somewhere a nervous first-time user will see it before they ever hit "add card" — a one-line reassurance, not a wall of terms:

  > "We hold funds, we don't take them — you're only charged once you're both confirmed for a real date, and refund rules are shown before you commit."

- *"What if I show up and they don't, or it's unsafe?"* — the no-show and dispute handling exists (§14.7 refund policy, §15.4 no-scan fallback with mutual confirmation), but none of that is visible to a person *before* they pay. Show the cancellation/no-show policy — plainly, in real numbers, not a link to a legal document — right on the proposal screen: **"Full refund if canceled more than 24 hours before your date. Inside 24 hours, no refund by default."** People will forgive a strict policy they can see coming far more than a surprise one.

**Biggest single risk in this whole moment:** the word "hold" doing silent, heavy lifting. If the client-side copy (which doesn't exist yet, since there's no client) ever collapses "authorize a hold" into "charge your card" for simplicity, this becomes the single most damaging piece of copy in the product — it will read as the app taking money from two strangers who've never met, with no visible reason why, at the exact moment they're being asked to trust it most.

---

## 9. The date itself and after

**The ticket:** issued only after both captures succeed — never before, which is right (a voucher represents secured money, not just an accepted invite). Venue staff get a genuinely well-scoped view — name, time, participant *names* (not emails, not payment info, not the chat) — the `venue.ts` serializer is an explicit allowlist built specifically to keep staff blind to anything sensitive. That's a good, quiet piece of design worth protecting as-is.

**The scan:** straightforward, low-friction by design — staff scan or enter a code, the date completes. If the venue's scanner is down or staff forget (a completely ordinary real-world failure, not a user's fault), the fallback is both people independently confirming attendance within 72 hours. That's the right way to avoid punishing two people for a venue's operational hiccup — but the moment where only one of them confirms and it becomes `disputed` needs very careful copy, because from the honest confirmer's side this can look exactly like being stood up, even when the truth is just "the other person forgot to tap a button." Don't say "disputed" to the user — that word implies conflict where there might just be forgetfulness:

> "We're waiting on your date to also confirm you both showed up. If they don't confirm soon, we'll follow up before anything's decided."

**Post-date check-in:** the four-outcome model (`did_not_happen` / `happened_bad` / `happened_fine` / `happened_good`) rather than a single star rating is a real improvement over generic post-transaction ratings — it separates "the logistics worked" from "I had a good time," and routes safety concerns through the report pipeline privately rather than mixing them into a visible rating. This is good design and worth protecting; don't let a future redesign collapse it back into a single 1-5 star average, which would recreate the exact "meaningless midpoint" failure mode this whole review keeps finding elsewhere.

---

## 10. Trust and moderation from the receiving end

**Being restricted, from the inside:** the trust summary is a real strength — it names specific, actionable items ("Verify your email address," "Add a clear face photo," "Verify a payment method," "Complete more of your profile questions," "Complete a date") rather than a bare score, exactly per spec, and it does not expose the underlying formula. That's the right balance between transparency and gaming-resistance. Protect this list's specificity — a lazy future rewrite that collapses it to "improve your profile to raise your trust level" would quietly break the one thing that makes a restriction feel fixable instead of arbitrary.

**When it's wrong — the actual hard case:** appeal has exactly four automated paths (`liveness_check`, `payment_verification`, `cooldown`, `existing_signals`), and `existing_signals` — the "just trust that my account looks normal" path — is gated behind 30 days of account age *and* a verified email. That means a brand-new, wrongly-flagged account (the single most likely person to be a false positive, since new accounts trigger more automated suspicion by design) has effectively **one real option: wait out the cooldown (24 hours by default) and try again**, or add a verified payment method, or pass a liveness check. For someone who did nothing wrong, on day two of a new account, being told "your account is limited" with "wait 24 hours" as the only real lever is going to read as punitive, even though the system is behaving exactly as designed (zero human moderation, per spec). The one thing that would make this feel survivable rather than Kafkaesque is honesty about *which* path is actually available to them right now, instead of listing methods they can't yet use:

> "Your account is limited. Here's what will lift it fastest: verify a payment method (works right away), or complete a quick liveness check. Account history alone can restore access automatically once your account is 30 days old."

Never show a rejected appeal as a dead end. Right now a failed appeal just leaves the restriction in place with no forward path shown in the copy anywhere — at minimum, tell them when they can try again:

> "This appeal didn't pass. You can try again in [cooldown] — in the meantime, verifying a payment method is usually the fastest way to restore full access."

**Shadowban specifically:** per spec, a shadowbanned account can keep using the app but nobody sees them — deliberately invisible so it can't be gamed by evasion. That means the honest, safety-motivated version of this feature *requires* the affected person to feel confused for a while before the trust summary explains why (they'll notice zero new matches and won't necessarily connect it to "restricted," since nothing tells them outright they're shadowbanned — only that their level is limited). That's a real, unavoidable tension in the design, not a bug — but it means the trust summary page needs to be genuinely easy to find (not buried three taps deep) the moment someone might start wondering why the app went quiet, because that page is the only honest signal they're going to get.

---

## Tone and copy audit

Across everything actually specified as literal copy in code and spec, the voice is mostly good — plain, unaccusatory, specific. The two places it needs the most active work before a client ships:

1. **Anything payment-related** — "hold" vs "charge," "payment_failed" vs a human explanation, "disputed" vs "we're waiting on them to confirm" — because backend states will otherwise leak directly into user-facing text verbatim (`payment_failed`, `disputed`, `canceled` are internal status enum values, not sentences), and that is the single fastest way to make a warm product feel like a broken one.
2. **Rejection and restriction moments** (photo rejection, trust restriction, appeal denial) — these are exactly the moments where a person is most likely to feel judged, and they're exactly the moments the current code exposes as terse internal reason-codes (`nudity_detected`, `primary_photo_missing_face`) rather than sentences. Every one of those needs a human sentence before it ever reaches a screen.

One genuinely good, protectable pattern already established: **the generic decline** ("They passed on this match.") and the **generic mutual-eligibility refusal** are both deliberately vague to protect the other party's privacy and dignity, and both are consistent with each other. Don't let a future "more transparency" push add detail back into either — the vagueness is the safety feature here, not a gap.

---

## Cognitive load — what to defer or cut

- **Defer to after the first grid view, not before it:** full profile bio, interest tags (public/private), lifestyle attributes beyond the four gating fields. None of these are required to reach 50% completeness; don't ask for them before someone has seen a single other human being.
- **Never require in one sitting:** the compatibility question bank. Batch it small (see §2) and let people return to it between sessions — a bank designed for hundreds of entries is structurally an ongoing relationship with the app, not an onboarding step, and pacing it as a wall works against that design.
- **Cut entirely from the first-run path:** payment method collection. It's already correctly deferred to the point of the first date proposal in the code — protect that; there's no reason to ask earlier, and asking earlier would put a card number in front of someone before they've even seen if there's anyone worth dating nearby.

---

## Accessibility and inclusion

- **No stable address / no bank card:** the payment-hold model structurally excludes anyone without a card that can sustain a hold (unbanked users, some students, people rebuilding credit). The spec doesn't address this, and there's no visible fallback (e.g. a debit-only path, a lower-friction verification-only proposal tier). This is a real exclusion, not just a UX rough edge, and it's worth naming plainly to product: the "real money as scam deterrent" design choice has a real cost in who can use the dating half of the product at all, even though browsing and chatting stay free.
- **Irregular schedules:** the 48-hour interest/proposal-acceptance windows and 72-hour chat-decay prompt assume someone checks the app every day or two. Shift workers, people with irregular caregiving schedules, and touring/travelling workers will disproportionately let interests expire and get nudged toward dates on a clock that doesn't fit their week. There's no way in the current design to say "I'm slow to respond right now" — worth considering as a lightweight, opt-in status rather than a fix.
- **Small or rural areas:** covered above in the discovery-grid section — the reality dashboard is the right tool, it just needs to surface itself proactively instead of waiting to be found, or rural users will experience "no candidates" as the whole product rather than as a fixable, explained state.
- **Face-photo requirement:** reasonable as a catfishing deterrent, but worth an explicit, sympathetic exception path in copy (not necessarily in enforcement) for anyone whose face genuinely can't be the lead photo for a real reason — the rejection copy in §3 above at least avoids making this feel like an accusation, which is the minimum bar.

---

## What's genuinely good and should be protected from "helpful" changes

1. **No like counts, no boosts, no popularity signal in the wire format** — enforced by an explicit allowlist serializer with a comment explaining why. This is the product's core differentiation from swipe apps; it is one field-addition away from being quietly undone by a future growth experiment.
2. **The generic decline / generic refusal copy** — vagueness as a deliberate privacy and dignity feature, not a gap to "improve."
3. **The escrow structure** (hold → both-sides-authorize → capture together → ticket) and its careful failure handling (a failed second capture refunds the first rather than leaving one person charged). This is the single most trust-critical mechanism in the app and it's built correctly.
4. **The redesigned question bank** (ladder control, deal-breaker/irrelevant importance levels, labeled midpoints, skip with cooldown) — exactly the right fix for the user-testing failures this review was asked to watch for. It needs routes, not a rewrite.
5. **The post-date four-outcome check-in**, keeping safety, logistics-truth, and future-matching signal as three separate concerns that can't corrupt each other.
6. **Venue staff's narrow view** — names and times only, nothing sensitive — a good, quiet piece of least-privilege design.
7. **The reality dashboard's honesty** — showing real, sometimes disappointing pool numbers rather than papering over a thin market with fake profiles (the spec explicitly forbids this, and the code follows through).

---

## Moments most likely to cause abandonment, ranked

1. **The money moment, if "hold" reads as "charge."** This is the highest-stakes single screen in the product — two strangers, a real card, before a date has even been agreed to. A miscommunication here doesn't just lose one session, it's the kind of thing people screenshot and warn others about.
2. **The question flow, if the old (unrouted-fix) system ships.** No skip, no "don't care," required paired answers, a flat unpaced list of hundreds of questions — this is precisely the shape that already failed in user testing, and it's the literal first thing between signup and a real match for anyone who doesn't rush past it.
3. **The empty/thin discovery grid, especially in a small city, with no proactive explanation.** "No candidates" with no visible next step reads as "this app has nothing for me" — a first-session-ending impression that the reality dashboard already exists to prevent, if it's surfaced automatically instead of hidden behind a second screen.
4. **Photo rejection with no explanation and no visible way to ask about a mistake.** No human reviewers means the copy has to do all the work of making a rejection feel like a fixable, understood event rather than an unappealable accusation — right now the reason codes are internal strings, not sentences.
5. **A wrongly-restricted new account with no real appeal lever available for 30 days.** Rare, but severe when it happens — this is the moment someone concludes the app is broken or hostile, not just strict.

---

## Summary for the team

**Moments most likely to lose a user:** (1) the payment-hold moment if it isn't explained as "hold, not charge" before the card is added; (2) the question flow, if it ships on the old, unrouted system rather than the better one already built; (3) an unexplained empty discovery grid, especially outside a major city.

**Single biggest experience risk:** the good question-bank redesign — the actual fix for the exact problems this review was asked to hunt for — has no HTTP route. Every other finding in this document assumes a client gets built against what's *reachable* today, and today that means the old 5-point, no-skip, no-deal-breaker system is what a user would actually experience, even though a materially better one is sitting finished in the codebase one routing layer away.

**What I'd change first:** wire `question.service.ts`'s new question-bank functions (`selectNextQuestionsForMe`, `putMyQuestionAnswer`, the deal-breaker and tag-intensity endpoints) into real routes before anything else in this list — it's the highest-leverage fix here because the design work is already done; it just needs a door to reach the person.
