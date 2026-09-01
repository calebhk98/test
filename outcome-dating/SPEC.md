# Developer Specification Document  
## Outcome-Aligned Dating App  
### Version 1.0

This document is intended for a programmer or development team to build the app. It includes product rules, technical requirements, data models, state machines, APIs, algorithms, moderation rules, payment flow, admin tooling, and the reasoning behind major decisions.

Where this document says **MUST**, it is mandatory.  
Where it says **SHOULD**, it is strongly recommended unless there is a documented technical constraint.  
Where it says **MAY**, it is optional or configurable.

---

# 1. Product Overview

The app is a dating app designed to encourage real-world dating rather than endless swiping.

The core principles are:

1. Users answer structured compatibility questions.
2. Hard filters are strictly enforced.
3. The algorithm sorts candidates only; it does not override filters.
4. Users do not mass-swipe. They browse a discovery grid and send limited match requests.
5. Mutual match unlocks chat.
6. Users can propose structured dates.
7. Date acceptance triggers refundable escrow holds.
8. Date completion is verified through venue redemption or structured post-date feedback.
9. The app does not use generative LLM text to write to users.
10. The app uses static UI copy, structured prompts, regex-based text analysis, and automated moderation.

The app must avoid:

- mandatory government ID verification,
- mandatory phone-number verification,
- social vouching,
- profile boosts,
- pay-to-win visibility,
- unlimited low-effort liking,
- hidden filter behavior,
- human moderation as a core dependency.

---

# 2. Core User Flow

The primary loop is:

```text
Create account
→ Answer compatibility questions
→ Set hard filters
→ Browse discovery grid
→ Send limited match interest
→ Other user accepts interest
→ Chat unlocks
→ Either user proposes structured date
→ Proposer payment hold is authorized
→ Other user accepts
→ Acceptor payment hold is authorized
→ Both funds are captured
→ Date ticket/voucher is issued
→ Date occurs at partner venue
→ Venue scans ticket
→ Post-date feedback collected
→ Chat becomes established
```

---

# 3. Non-Goals for MVP

The MVP should not include:

1. Generative AI text.
2. Video calling.
3. Live streaming.
4. Social feed.
5. Public like counts.
6. Profile boosts.
7. Unlimited likes.
8. Human moderation queues.
9. Mandatory government ID.
10. Mandatory phone verification.
11. In-app payments for subscriptions.
12. Milestone bounty verification unless explicitly added as a later phase.

Reason: These increase legal risk, cost, moderation burden, and product complexity.

---

# 4. User Roles

## 4.1 Regular User

Can:

- create an account,
- answer questions,
- set filters,
- browse profiles,
- send match interests,
- chat after mutual match,
- propose or accept dates,
- report/block users,
- view trust status.

## 4.2 Venue Staff

Can:

- view upcoming vouchers,
- scan or redeem vouchers,
- mark dates completed.

Venue staff cannot:

- see user chats,
- see user emails,
- see payment card details.

## 4.3 Admin

Admin access should be limited and audited.

Admin can:

- edit configuration variables,
- manage questions,
- manage venues,
- view analytics,
- review automated moderation actions,
- override payment disputes only where legally necessary,
- manage feature flags.

Admin should not be required for normal moderation. The system must assume zero human moderation.

Reason: Human moderation is often underfunded, delayed, or abandoned. The app must operate safely through automation and structured user actions.

---

# 5. Account Creation and Verification

## 5.1 Required Information

At signup, the user MUST provide:

1. Email address.
2. Password.
3. Date of birth.
4. Acceptance of terms.
5. Location permission or manually entered city.

The user MUST be at least 18 years old.

The app should calculate age from birthdate and enforce minimum age.

## 5.2 Phone Number

Phone number is NOT required.

Reason: Many younger users avoid phone plans, and phone verification creates friction.

## 5.3 Government ID

Government ID is NOT required.

Reason: Mandatory ID verification creates privacy backlash, legal liability, and onboarding drop-off.

## 5.4 Verification Methods

The app SHOULD use layered trust instead of mandatory identity verification.

Available verification/trust signals:

1. Verified email.
2. Verified payment method.
3. Device reputation.
4. Behavioral consistency.
5. Optional selfie liveness check.
6. Optional connected accounts, such as Spotify or Strava, if user opts in.

No vouching system is allowed.

Reason: Vouching can create exclusionary dynamics, invite abuse, and is hard to trust.

---

# 6. Trust System

## 6.1 Trust Score

Each user has a trust score from 0 to 100.

The trust score is not shown as an exact number unless product decides. Instead, show a level:

| Level | Score Range | Meaning |
|---|---:|---|
| Limited | 0–39 | Restricted features |
| Standard | 40–69 | Normal features |
| Trusted | 70–89 | More visibility/features |
| Elite | 90–100 | Highest trust |

## 6.2 Trust Factors

Positive factors:

- verified email,
- verified payment method,
- completed profile,
- completed dates,
- positive post-date feedback,
- account age,
- low report rate,
- normal message velocity,
- consistent location/device behavior.

Negative factors:

- reports,
- no-shows,
- spam-like message patterns,
- repeated off-platform solicitation patterns,
- fake-looking photos,
- rapid account creation behavior,
- suspicious device/IP signals,
- payment failures or chargebacks.

## 6.3 User Visibility Into Trust

Users MUST be able to see why their trust level is limited.

Do not expose the exact formula.

Show actionable items.

Example:

```text
Your trust level is Standard.

To improve:
- Add a clear face photo
- Verify a payment method
- Complete 3 more profile questions
- Complete a date

Recent negative events:
- 1 missed date
- 1 report for spam-like messaging
```

Reason: Users need to understand how to improve, but exposing exact weights invites gaming.

## 6.4 Trust-Based Restrictions

Default restrictions:

| Action | Limited | Standard | Trusted | Elite |
|---|---:|---:|---:|---:|
| Browse grid | yes | yes | yes | yes |
| Send interests | limited | yes | yes | yes |
| Chat | yes | yes | yes | yes |
| Send links | no | warning only | yes | yes |
| Date proposals | requires payment method | yes | yes | yes |

Reason: New or suspicious accounts should be able to use the app but not spam at scale.

---

# 7. Profile System

## 7.1 Profile Fields

Each profile includes:

- display name,
- age,
- city or approximate location,
- photos,
- free-text bio,
- structured prompts,
- interest tags,
- private tags,
- lifestyle attributes,
- relationship intentions,
- trust level,
- profile completeness score.

Exact location MUST NOT be shown. Show approximate distance only.

Reason: Safety and privacy.

## 7.2 Photos

Users can upload multiple photos.

Requirements:

1. At least one photo is required before discovery visibility.
2. First photo must contain a visible face, detected by computer vision.
3. Nudity, weapons, and known illegal imagery must be automatically blocked.
4. Duplicate or known scam images should be flagged using perceptual hash matching.

No human moderation is assumed.

## 7.3 Photo A/B Testing

The app MUST NOT rely only on generic photo advice.

Reason: Most users do not know how to evaluate their own photos, and generic advice fails.

Implementation:

1. When a user has at least 3 photos, the app may run an A/B test.
2. Different viewers see different primary photos.
3. The app records:
   - impressions,
   - profile views,
   - interests sent,
   - interests accepted.
4. The primary success metric is accepted interests, not raw profile views.
5. After enough data, the app recommends or automatically reorders photos.

Example:

```text
Photo 3 produces 42% more accepted matches than Photo 1.
Recommendation: Make Photo 3 your first photo.
```

The user should be able to approve or reject the recommendation unless product decides automatic reordering is preferred.

Reason: The market reveals what works better than subjective advice.

---

# 8. Compatibility Questions

## 8.1 Question Structure

Every compatibility question MUST have two answers:

1. Self answer: what is true for the user.
2. Partner answer: what the user wants in a partner.

All answers use a 5-point scale.

Example:

Question: “Pets”

Self answer:

```text
1 = I do not like pets
2 = I am okay without pets
3 = Neutral
4 = I like pets
5 = I have pets / love pets
```

Partner answer:

```text
1 = I do not want my partner to have pets
2 = Prefer no pets
3 = Neutral
4 = Prefer partner likes pets
5 = Partner must love/have pets
```

## 8.2 Question Metadata

Each question has:

- id,
- slug,
- category,
- question text,
- self left label,
- self right label,
- partner left label,
- partner right label,
- weight,
- polarity,
- sensitivity level,
- private visibility option,
- active flag.

## 8.3 No Assumed Answers

The app MAY observe behavior and suggest questions, but MUST NOT assume answers.

Example:

If a user repeatedly accepts matches who like hiking, the app can ask:

```text
You often match with people who enjoy hiking.
How important is hiking to you in a partner?
```

It must not silently change the user’s preference.

Reason: Behavior can be noisy. Explicit answers should drive sorting.

## 8.4 Social Desirability Bias

Users may hide interests due to stigma.

Example:

A user likes anime but does not want to be judged.

Solution: private tags.

Users can mark an interest tag as:

```text
Public
or
Visible only to people who share this interest
```

If private, the tag does not appear publicly. It only appears when another user also has that tag.

Reason: This encourages honesty without forcing users to expose stigmatized interests to everyone.

## 8.5 Sensitive Questions

Sensitive questions should allow:

- explicit answer,
- prefer not to say,
- private answer.

“Prefer not to say” should be treated as neutral unless it conflicts with a hard filter.

Reason: Forcing answers can create dishonest data.

---

# 9. Filters

## 9.1 Filter Philosophy

Filters MUST be enforced strictly.

The algorithm MUST NOT override a user’s hard filter.

Reason: Users need to trust that filters are real.

## 9.2 Hard Filter Examples

Hard filters include:

- age range,
- maximum distance,
- has children,
- wants children,
- smoking,
- drinking,
- drug use,
- religion,
- relationship intention,
- gender preference,
- other admin-defined filters.

Users MAY set many filters. Do not block filter slots.

Reason: Users should be able to refine their pool. If the pool becomes too small, show the result count instead of preventing filters.

## 9.3 Reality Dashboard

The app SHOULD show:

```text
People who match your filters: X
People whose filters you match: Y
Mutual match pool: Z
```

Reason: This manages expectations and helps users understand why their pool is large or small.

## 9.4 Mutual Filter Requirement

For discovery, a candidate should generally satisfy both:

1. my hard filters,
2. the candidate’s hard filters.

Reason: If I filter out smokers, smokers should not see me and waste an interest.

Exception: If product wants one-sided filtering for browse-only modes, it must be explicit. Default should be mutual filter passing.

---

# 10. Discovery Grid

## 10.1 UI

The discovery screen is a grid, not a swipe deck.

Each card shows:

- primary photo,
- first name or display name,
- age,
- approximate distance,
- maybe one shared interest.

No public like count.

No popularity score.

No boost badge.

Reason: Public popularity metrics create herd behavior and status games.

## 10.2 Profile Visibility Rules

A profile is visible in discovery only if:

1. account is active,
2. account is not shadowbanned,
3. profile is complete enough,
4. user has at least one approved photo,
5. incoming pending interests < incoming interest cap,
6. active conversations < active conversation cap,
7. I pass their hard filters,
8. they pass my hard filters,
9. neither user has blocked the other.

Reason: This prevents inbox overload and keeps the queue manageable.

## 10.3 Sorting

The grid is sorted by compatibility score descending.

Secondary tie-breakers:

1. trust score,
2. profile completeness,
3. recent activity,
4. response rate.

No compatibility threshold hides users.

Reason: The algorithm sorts only. It does not decide who is allowed to be seen, except through hard filters and capacity rules.

---

# 11. Match Interests

## 11.1 Interest Definition

An interest is a request to start a chat.

It is not a date proposal.

It does not require payment.

## 11.2 Interest Limits

Default configurable limits:

| Variable | Default |
|---|---:|
| outgoing pending interest limit | 5 |
| incoming pending interest limit | 10 |
| interest expiry hours | 48 |
| daily outgoing interest limit | 20 |

Reason: Limits prevent spam and overwhelm.

## 11.3 Interest Content

An interest should not include free-text before match.

Reason: Unsolicited text increases harassment and moderation complexity.

After match, chat is free-text.

## 11.4 Interest States

```text
pending
accepted
declined
expired
canceled
```

### Sender cancels

If sender cancels while pending:

```text
interest = canceled
```

### Recipient accepts

```text
interest = accepted
conversation = active
```

### Recipient declines

```text
interest = declined
```

Sender should see a generic decline message.

Do not show harsh details.

Example:

```text
They passed on this match.
```

Reason: Reduce negativity.

### Interest expires

If recipient does not respond before expiry:

```text
interest = expired
```

Sender’s outgoing slot is freed.

Reason: Prevent dead requests from blocking capacity.

---

# 12. Chat System

## 12.1 Chat Unlock

Chat unlocks only after mutual match.

Reason: Prevents unsolicited messages.

## 12.2 Message Type

Messages support:

- plain text,
- emojis,
- maybe predefined prompt cards.

MVP should not support images, audio, or video.

Reason: Media increases moderation complexity.

## 12.3 Message Limits

Configurable limits:

| Variable | Default |
|---|---:|
| max messages per user per hour | 120 |
| max external links per hour for low trust | 0 |
| max external links per hour for standard trust | 5 |

Reason: Prevent spam while allowing normal conversation.

## 12.4 Text Analysis

The app MAY perform non-LLM textual analysis.

Allowed methods:

- regex,
- keyword lists,
- domain lists,
- rate-based heuristics.

Do not use LLM-generated responses.

Reason: Product constraint.

## 12.5 Off-App Handles and Links

If a message contains an Instagram handle, phone number, Snapchat, Telegram, WhatsApp, or URL, the app should not block it by default.

Instead, show a small notice below the message:

```text
Booking your first date through the app includes venue perks and safety verification.
```

Reason: Moving off-app is common and not inherently bad. The app should incentivize the first date rather than punish normal behavior.

## 12.6 Chat Decay

Chats before a completed date are subject to decay.

Default:

| Event | Action |
|---|---|
| 72 hours after first message with no date proposal | show date prompt |
| 14 days with no date proposal | move chat to cooling |
| 21 days with no date proposal | archive chat |

If a date is completed, chat becomes established and does not decay.

Reason: The app should encourage dates but not force users to date every week just to keep a conversation.

## 12.7 Post-Date Chat

After a completed date, the conversation state becomes:

```text
established
```

Established chats:

- do not expire,
- do not count against pre-date chat slots,
- remain active as long as neither user blocks/archives.

Reason: If users are dating, the app should not interfere.

---

# 13. Date Proposals

## 13.1 Date Proposal Creation

A user can propose a date from an active conversation.

The date proposal includes:

- venue,
- date,
- time slot,
- optional user-written note,
- escrow amount,
- policy version.

The app provides structured venue choices.

Reason: Many users do not know how to plan a good first date.

## 13.2 Venue Categories

Venue categories include:

- coffee,
- dessert,
- drinks,
- walk,
- museum,
- arcade,
- live music,
- comedy,
- class/activity,
- food market.

Each venue has:

- id,
- name,
- address,
- latitude/longitude,
- category,
- active flag,
- available time slots,
- margin percentage,
- redemption method.

## 13.3 Date Proposal States

```text
draft
pending_acceptance
accepted
declined
expired
canceled
payment_failed
charged
ticketed
completed
no_show
refunded
disputed
```

---

# 14. Payment and Escrow Flow

Use a payment processor that supports authorization holds and manual capture, such as Stripe.

Do not store full card numbers.

Use payment tokens.

## 14.1 Escrow Amount

Default escrow amount:

```text
$20 per person
```

Store as minor units:

```text
2000 cents
```

The amount MUST be configurable.

## 14.2 Payment Flow

### Step 1: Proposer sends date proposal

System authorizes proposer payment method.

```text
proposer_payment_hold = authorized
date_proposal = pending_acceptance
```

No charge yet.

Reason: Shows serious intent without charging before acceptance.

### Step 2: Recipient accepts

System authorizes recipient payment method.

```text
recipient_payment_hold = authorized
date_proposal = accepted
```

### Step 3: Capture both holds

Once both holds are authorized, the system captures both payments.

```text
proposer_payment = captured
recipient_payment = captured
date_proposal = charged
```

### Step 4: Ticket issued

After successful capture, the system issues a ticket/voucher.

```text
voucher = issued
date_proposal = ticketed
```

The ticket appears in both users’ wallets.

## 14.3 When Is the Actual Charge?

The actual charge happens after:

1. proposer’s hold is authorized,
2. recipient accepts,
3. recipient’s hold is authorized,
4. system successfully captures both holds.

Reason: Neither user should be charged unless both have committed.

## 14.4 When Do Users Get the Ticket?

Users get the ticket only after both payments are captured successfully.

Reason: The ticket represents purchased value. It should not exist before funds are secured.

## 14.5 Payment Failure Cases

### Proposer authorization fails

```text
date_proposal = payment_failed
```

Notify proposer to update payment method.

### Recipient authorization fails

```text
date_proposal = payment_failed
release proposer hold
```

Notify both users.

Reason: The proposer should not be stuck with a hold if the recipient cannot accept.

### Capture fails after authorization

```text
date_proposal = payment_failed
release all holds
```

Reason: Do not charge one person without completing the pair.

## 14.6 Expiry of Pending Date Proposal

If recipient does not accept within configurable time, default 48 hours:

```text
date_proposal = expired
release proposer hold
```

Reason: Holds should not remain indefinitely.

## 14.7 Cancellation and Refunds

Configurable policy:

| Variable | Default |
|---|---:|
| full refund cutoff hours before date | 24 |
| late cancel refund percent | 0 |
| no-show refund percent | 0 |

### Before acceptance

Proposer cancels:

```text
release proposer hold
date_proposal = canceled
```

### After acceptance, more than 24 hours before date

Either user cancels:

```text
refund both users
voucher = canceled
date_proposal = refunded
```

### After acceptance, less than 24 hours before date

Either user cancels:

```text
no refund by default
voucher = canceled or retained according to policy
date_proposal = canceled
```

Reason: Prevent flaking.

This policy MUST be configurable.

## 14.8 Ledger

All payment events must be recorded in an immutable ledger.

Ledger entry fields:

- id,
- user_id,
- date_proposal_id,
- type,
- amount_cents,
- currency,
- processor_reference,
- created_at,
- metadata.

Types:

- authorization,
- capture,
- release,
- refund,
- dispute,
- chargeback.

Reason: Financial correctness and auditability.

---

# 15. Ticket/Voucher System

## 15.1 Ticket Contents

Ticket includes:

- voucher id,
- date proposal id,
- venue id,
- user names,
- scheduled time,
- amount/value,
- QR payload,
- expiration date.

## 15.2 QR Payload

Use signed JWT or similar signed token.

Example payload:

```json
{
  "voucher_id": "abc123",
  "venue_id": "venue_42",
  "date_proposal_id": "date_900",
  "expires_at": "2026-09-05T23:59:59Z",
  "signature": "signed_value"
}
```

Do not include full payment card data.

Reason: Venue staff need validation, not sensitive user data.

## 15.3 Redemption

Venue staff scans or enters code.

Redemption records:

- voucher id,
- venue staff id,
- timestamp,
- method.

Once redeemed:

```text
voucher = redeemed
date_proposal = completed
conversation = established
```

Reason: Completion should be tied to real-world action.

## 15.4 No-Scan Fallback

If venue does not scan, users may both confirm attendance after the scheduled date.

If both confirm within 72 hours:

```text
date_proposal = completed_unverified
conversation = established
```

This does not automatically settle venue payment.

Reason: Prevent users from being blocked due to venue error, while preserving financial integrity.

If only one user confirms:

```text
date_proposal = disputed
```

Automated handling applies according to policy.

---

# 16. Compatibility Algorithm

## 16.1 Algorithm Role

The algorithm sorts candidates.

It does not hide candidates who pass hard filters, except for:

- capacity limits,
- moderation restrictions,
- blocking,
- incomplete profile,
- geographic limits.

Reason: Filters are the boundary. Sorting is preference.

## 16.2 Compatibility Score Formula

For each answered question, compare:

- User A’s partner preference with User B’s self answer.
- User B’s partner preference with User A’s self answer.

For question `i`:

```text
satisfaction_A_with_B = 1 - abs(A.partner_answer[i] - B.self_answer[i]) / 4
satisfaction_B_with_A = 1 - abs(B.partner_answer[i] - A.self_answer[i]) / 4
pair_satisfaction = (satisfaction_A_with_B + satisfaction_B_with_A) / 2
```

If question polarity is reversed, transform values first.

Example reversed polarity:

```text
transformed_value = 6 - original_value
```

Weight each question:

```text
question_weight = base_weight * importance_multiplier
```

Importance multiplier can be based on extremity of partner preference:

```text
importance_multiplier = 1 + abs(partner_answer - 3) * 0.25
```

Final score:

```text
compatibility_score =
  sum(pair_satisfaction[i] * question_weight[i])
  /
  sum(question_weight[i])
```

If there are too few shared answered questions, score defaults to 0 or neutral.

Reason: This is simple, explainable, and configurable.

## 16.3 Score Storage

For MVP, compute score on demand for candidates.

For scale, precompute candidate scores nightly or incrementally.

Possible storage:

```text
compatibility_scores
  user_id
  candidate_id
  score
  computed_at
```

Reason: Full real-time pairwise scoring does not scale.

---

# 17. Behavioral Question Trigger

The app should detect patterns in accepted and declined matches.

Example:

If a user accepts several profiles with a specific tag, the app can ask a clarifying question.

Rules:

1. Do not assume the answer.
2. Do not silently change sorting.
3. Ask the user explicitly.
4. Let the user skip.

Example:

```text
You often match with people who list pets.
How do you feel about pets in a partner?
```

Reason: Behavior can reveal useful areas to ask about, but explicit answers should drive the algorithm.

---

# 18. Moderation and Safety

## 18.1 Zero Human Moderation Assumption

The system MUST assume no human moderators.

All moderation must be:

- automated,
- rule-based,
- threshold-based,
- community-report-driven,
- appealable through automated verification where possible.

Reason: Human moderation is often unavailable.

## 18.2 Automated Moderation Signals

Signals include:

- user reports,
- block count,
- message velocity,
- repeated identical messages,
- regex-detected scam patterns,
- nudity/violence image detection,
- duplicate photo hashes,
- device reputation,
- payment fraud signals,
- no-shows,
- negative post-date feedback.

## 18.3 Report Categories

Reports must be structured.

Categories:

- fake profile,
- scam/money request,
- harassment,
- unsafe behavior,
- misleading photos,
- minor suspected,
- spam,
- no-show,
- inappropriate content,
- other.

Do not rely only on free-text reports.

Reason: Structured reports are easier to automate.

## 18.4 Automated Actions

Actions include:

```text
none
warning
restriction
shadowban
suspension
```

### Restriction

Restriction may:

- reduce discovery visibility,
- limit outgoing interests,
- disable links,
- require additional verification.

### Shadowban

Shadowbanned user can still use the app but is not shown to others.

Reason: This reduces ban evasion and gives space for automated appeal.

### Suspension

Suspension blocks access.

Use only for severe or repeated automated violations.

## 18.5 Report Scoring

Each report contributes a score.

Score depends on:

- report category,
- reporter trust,
- reporter/report relationship,
- number of previous reports,
- recency.

Example:

```text
scam report from trusted user = high weight
duplicate report from same social cluster = reduced weight
no-show report after completed date = medium weight
```

If report score exceeds threshold:

```text
restriction
```

If higher:

```text
shadowban
```

If severe:

```text
suspension
```

All thresholds must be configurable.

Reason: Prevent brigading and false positives.

## 18.6 Appeals

Appeals should be automated where possible.

Possible appeal steps:

1. complete liveness check,
2. verify payment method,
3. wait cooldown period,
4. confirm identity through existing account signals.

If appeal passes, restore account.

If appeal fails, maintain restriction.

Reason: No human moderation means appeals must be automated.

---

# 19. Scam Prevention

## 19.1 Economic Friction

Date escrow is a major scam deterrent.

Reason: Scammers generally do not want to lock real money.

## 19.2 Device and Network Checks

Use:

- device fingerprinting,
- IP reputation,
- emulator detection,
- VPN/proxy detection,
- rate limiting.

Reason: Many scams are automated.

## 19.3 Message Pattern Rules

Use regex/keyword rules for:

- crypto,
- gift cards,
- wire transfer,
- cashapp/venmo/zelle,
- emergency money,
- investment offers,
- telegram/whatsapp links,
- adult-content promotion.

Do not block the message automatically by default.

Instead:

- flag internally,
- show safety banner if appropriate,
- increase fraud score if repeated.

Reason: Some normal users share links or social handles. Blocking creates bad UX.

## 19.4 Link Handling

Links should be displayed as plain text by default.

For low-trust users:

```text
links are not clickable
```

For standard/trusted users:

```text
links may be clickable but show warning if domain is unknown
```

Reason: Reduce phishing while allowing normal use.

---

# 20. Notification System

All notification text must be static or template-based.

No generated natural language.

## 20.1 Notification Events

- interest received,
- interest accepted,
- interest declined,
- interest expiring soon,
- chat opened,
- date proposal received,
- date accepted,
- payment hold authorized,
- payment failed,
- ticket issued,
- date reminder,
- venue redeemed,
- post-date feedback request,
- chat cooling,
- trust level changed,
- safety notice.

## 20.2 Channels

Use:

- push notification,
- email,
- in-app notification center.

Do not use SMS by default.

Reason: Cost and phone-number dependency.

---

# 21. Configuration System

All important business variables MUST be configurable without code deployment where possible.

## 21.1 Config Table

```text
config_entries
  key
  value_json
  description
  version
  updated_by
  updated_at
```

## 21.2 Config Loading

The app should load config through a config service.

The service should:

- cache values,
- invalidate on change,
- support versioning,
- support environment scope,
- log changes.

## 21.3 Policy Snapshots

When a user sends an interest or date proposal, store a policy snapshot.

Example:

```json
{
  "interest_expiry_hours": 48,
  "escrow_amount_cents": 2000,
  "full_refund_cutoff_hours": 24,
  "incoming_interest_limit": 10
}
```

Reason: Existing objects should not unexpectedly change rules.

## 21.4 Config Variables

| Key | Default | Existing Object Behavior | Reason |
|---|---:|---|---|
| `interest.outgoing_pending_limit` | 5 | live | prevent spam |
| `interest.incoming_pending_limit` | 10 | live | prevent overload |
| `interest.expiry_hours` | 48 | existing keep original | predictable expiry |
| `chat.active_limit` | 15 | live | manage attention |
| `chat.date_prompt_hours` | 72 | live | encourage dates |
| `chat.pre_date_archive_days` | 21 | live | prevent pen-pal drift |
| `date.escrow_amount_cents` | 2000 | existing proposals keep original | payment fairness |
| `date.accept_expiry_hours` | 48 | existing keep original | payment fairness |
| `date.full_refund_cutoff_hours` | 24 | existing keep original | cancellation fairness |
| `date.late_cancel_refund_percent` | 0 | existing keep original | policy consistency |
| `moderation.auto_restriction_score` | 50 | live | safety |
| `moderation.auto_shadowban_score` | 80 | live | safety |
| `trust.link_min_level` | standard | live | reduce spam |

Reason: The team must be able to tune the product without digging through code.

---

# 22. Feature Flags

Use feature flags for risky features.

Examples:

- photo A/B testing,
- behavioral question prompts,
- new venue categories,
- new report categories,
- chat decay,
- post-date feedback,
- milestone bounties.

Feature flag fields:

```text
key
enabled
rollout_percent
target_user_segments
created_at
updated_at
```

Reason: Safe rollout and rollback.

---

# 23. Database Schema

Below is a recommended relational schema. Use Postgres or equivalent.

## 23.1 users

```text
id
email
password_hash
birthdate
status
trust_score
trust_level
shadowbanned
suspended
created_at
last_active_at
```

## 23.2 user_auth_events

```text
id
user_id
device_fingerprint
ip_address
login_at
success
```

## 23.3 profiles

```text
user_id
display_name
bio
city
latitude
longitude
location_fuzzed
age
gender
seeking
relationship_intention
profile_completeness
updated_at
```

## 23.4 user_photos

```text
id
user_id
image_url
position
is_primary
moderation_status
face_detected
blur_score
brightness_score
group_photo_detected
created_at
```

## 23.5 photo_experiments

```text
id
user_id
photo_id
impressions
interests_sent
interests_accepted
created_at
updated_at
```

## 23.6 questions

```text
id
slug
category
question_text
self_left_label
self_right_label
partner_left_label
partner_right_label
weight
polarity
sensitive
active
created_at
updated_at
```

## 23.7 answers

```text
user_id
question_id
self_value
partner_value
updated_at
```

Primary key: `(user_id, question_id)`.

## 23.8 interest_tags

```text
id
name
category
public_description
created_at
```

## 23.9 user_tags

```text
user_id
tag_id
visibility
created_at
```

Visibility:

```text
public
private_reciprocal
hidden
```

## 23.10 hard_filters

```text
user_id
filter_key
operator
value
enabled
updated_at
```

Examples:

```text
age_min >= 21
age_max <= 35
distance_km <= 25
smoking <= 2
wants_children >= 4
```

## 23.11 discovery_events

```text
id
viewer_user_id
candidate_user_id
primary_photo_id
source
created_at
```

## 23.12 interests

```text
id
sender_id
recipient_id
status
policy_snapshot
created_at
expires_at
accepted_at
declined_at
canceled_at
expired_at
```

## 23.13 conversations

```text
id
user_a_id
user_b_id
status
created_at
last_message_at
first_date_completed_at
archived_at
```

Status:

```text
active
cooling
archived
established
```

## 23.14 messages

```text
id
conversation_id
sender_id
body
created_at
read_at
analysis_flags
```

## 23.15 message_flags

```text
id
message_id
flag_type
severity
created_at
```

Flag types:

```text
external_contact
money_request
link
crypto
spam_pattern
abuse_pattern
```

## 23.16 venues

```text
id
name
address
latitude
longitude
category
active
margin_percent
time_slot_config
created_at
```

## 23.17 date_proposals

```text
id
conversation_id
proposer_id
recipient_id
venue_id
scheduled_start
scheduled_end
optional_note
status
policy_snapshot
escrow_amount_cents
created_at
accepted_at
declined_at
expired_at
canceled_at
charged_at
ticketed_at
completed_at
```

## 23.18 payment_holds

```text
id
date_proposal_id
user_id
processor
processor_intent_id
amount_cents
currency
status
authorized_at
captured_at
released_at
refunded_at
failure_reason
```

Status:

```text
pending
authorized
capture_pending
captured
released
failed
refunded
```

## 23.19 payment_ledger

```text
id
user_id
date_proposal_id
payment_hold_id
type
amount_cents
currency
processor_reference
metadata
created_at
```

## 23.20 vouchers

```text
id
date_proposal_id
venue_id
code
qr_payload
status
issued_at
expires_at
redeemed_at
```

Status:

```text
issued
redeemed
expired
canceled
```

## 23.21 venue_redemptions

```text
id
voucher_id
venue_id
venue_staff_id
method
created_at
```

## 23.22 reports

```text
id
reporter_id
reported_id
conversation_id
message_id
category
severity
details
created_at
```

## 23.23 moderation_actions

```text
id
user_id
action
reason
score
metadata
created_at
```

## 23.24 trust_events

```text
id
user_id
event_type
delta
metadata
created_at
```

## 23.25 config_entries

```text
key
value_json
description
version
updated_by
updated_at
```

## 23.26 feature_flags

```text
key
enabled
rollout_percent
segments
updated_at
```

---

# 24. API Specification

Use REST or GraphQL. REST is shown below.

All authenticated endpoints use short-lived access tokens and refresh tokens.

## 24.1 Auth

```text
POST /auth/register
POST /auth/login
POST /auth/logout
POST /auth/refresh
POST /auth/forgot-password
POST /auth/reset-password
```

## 24.2 Profile

```text
GET /me
PATCH /me
GET /me/profile
PATCH /me/profile
POST /me/photos
DELETE /me/photos/{photoId}
GET /me/photo-test-results
```

## 24.3 Questions

```text
GET /questions
GET /me/answers
PUT /me/answers
```

## 24.4 Filters

```text
GET /me/filters
PATCH /me/filters
```

## 24.5 Discovery

```text
GET /discovery
GET /profiles/{userId}
POST /profiles/{userId}/block
POST /profiles/{userId}/report
```

## 24.6 Interests

```text
POST /interests
GET /interests/outgoing
GET /interests/incoming
POST /interests/{interestId}/accept
POST /interests/{interestId}/decline
POST /interests/{interestId}/cancel
```

## 24.7 Conversations

```text
GET /conversations
GET /conversations/{conversationId}
GET /conversations/{conversationId}/messages
POST /conversations/{conversationId}/messages
POST /conversations/{conversationId}/archive
```

## 24.8 Dates

```text
GET /venues
POST /conversations/{conversationId}/date-proposals
GET /date-proposals/{dateProposalId}
POST /date-proposals/{dateProposalId}/accept
POST /date-proposals/{dateProposalId}/decline
POST /date-proposals/{dateProposalId}/cancel
POST /date-proposals/{dateProposalId}/confirm-attendance
```

## 24.9 Tickets

```text
GET /tickets
GET /tickets/{ticketId}
POST /tickets/{ticketId}/redeem
```

Venue staff endpoint:

```text
POST /venue/redeem
```

## 24.10 Payments

```text
POST /payment-methods
GET /payment-methods
DELETE /payment-methods/{paymentMethodId}
POST /webhooks/payments
```

## 24.11 Trust

```text
GET /me/trust
GET /me/trust/events
POST /me/trust/appeal
```

## 24.12 Reports

```text
POST /reports
```

## 24.13 Admin

```text
GET /admin/config
PATCH /admin/config
GET /admin/questions
POST /admin/questions
PATCH /admin/questions/{id}
GET /admin/venues
POST /admin/venues
GET /admin/users
GET /admin/moderation/actions
POST /admin/feature-flags
GET /admin/analytics/overview
```

---

# 25. Background Jobs

## 25.1 Interest Expiry

Run every few minutes.

Find pending interests past expiry.

Set to expired.

Release outgoing slot.

## 25.2 Date Proposal Expiry

Find pending date proposals past acceptance expiry.

Set to expired.

Release proposer hold.

## 25.3 Chat Cooling/Archival

Find pre-date conversations:

- no date proposal after 72 hours: send prompt.
- no date proposal after 14 days: cooling.
- no date proposal after 21 days: archive.

Do not archive established conversations.

## 25.4 Compatibility Score Refresh

Run nightly or on major answer changes.

Update materialized compatibility scores.

## 25.5 Photo A/B Stats

Aggregate impressions and accepted interests.

Update photo ranking.

## 25.6 Trust Score Recalculation

Recalculate trust scores when major events occur:

- report,
- date completed,
- payment failure,
- profile change,
- verification change.

## 25.7 Moderation Score Recalculation

Aggregate reports and automated flags.

Apply restrictions/shadowbans when thresholds crossed.

## 25.8 Voucher Expiry

Expire vouchers after configurable period.

## 25.9 Payment Reconciliation

Compare processor webhooks with local ledger.

Flag mismatches.

---

# 26. Analytics and Metrics

Track product metrics without exposing them publicly.

## 26.1 Core Metrics

- registrations,
- verified emails,
- profiles completed,
- discovery impressions,
- interests sent,
- interests accepted,
- conversations opened,
- date proposals sent,
- date proposals accepted,
- dates completed,
- voucher redemptions,
- refunds,
- no-shows,
- reports,
- blocks,
- shadowbans,
- uninstalls,
- retention by cohort.

## 26.2 Quality Metrics

- accepted interest rate,
- date completion rate,
- post-date positive feedback rate,
- report rate per 1,000 messages,
- no-show rate,
- refund rate,
- chat-to-date conversion rate,
- repeat date rate.

Reason: The app should optimize for real dates, not raw matches.

---

# 27. Admin Panel Requirements

Admin panel should include:

1. Config editor.
2. Feature flag manager.
3. Question manager.
4. Venue manager.
5. User lookup.
6. Trust event viewer.
7. Moderation action viewer.
8. Payment ledger viewer.
9. Report trend dashboard.
10. Date completion dashboard.
11. Photo A/B results.
12. Funnel analytics.

Admin actions must be logged.

Reason: Developers and product owners need operational control without requiring direct database edits.

---

# 28. Security Requirements

## 28.1 Passwords

Use Argon2id or bcrypt.

Do not store plaintext passwords.

## 28.2 Tokens

Use short-lived access tokens and rotated refresh tokens.

## 28.3 Encryption

Encrypt sensitive data at rest.

Use TLS in transit.

## 28.4 Payment Compliance

Do not store card numbers.

Use PCI-compliant payment processor.

## 28.5 Location Privacy

Store approximate location only.

Do not expose exact coordinates to other users.

## 28.6 Audit Logs

Log admin actions.

Log moderation actions.

Log config changes.

Reason: Security and abuse investigation.

---

# 29. Privacy Requirements

The app should support:

1. account deletion,
2. data export,
3. consent management,
4. marketing opt-out,
5. cookie/tracking disclosure,
6. privacy policy acceptance.

Users should be able to delete account.

Account deletion should:

- remove profile from discovery,
- block new messages,
- retain financial records as legally required,
- anonymize analytics where possible.

Reason: Legal compliance.

---

# 30. Edge Cases

## 30.1 User has no candidates

Show:

```text
No candidates currently match your filters.
Try widening distance or age range.
```

Show reality dashboard counts.

Do not show fake profiles.

Reason: Trust.

## 30.2 User reaches outgoing interest limit

Disable send button and show:

```text
You have reached your pending interest limit.
Wait for responses or expiration.
```

Reason: Prevent spam.

## 30.3 Recipient inbox full

Do not show profile in discovery.

Reason: Prevent overload.

## 30.4 Interest accepted while sender is shadowbanned

Existing accepted conversation may remain, but new discovery visibility should be restricted.

Reason: Avoid breaking existing conversations unless safety requires.

## 30.5 Date proposal accepted but payment fails

Cancel proposal and release other hold.

Reason: Do not charge one side alone.

## 30.6 Venue closes after date accepted

Allow admin to mark venue inactive.

If date not redeemed, allow refund or reschedule.

Reason: Operational failure should not punish users.

## 30.7 User changes hard filters after matching

Existing conversations remain.

Future discovery uses new filters.

Reason: Changing filters should not erase existing human interaction.

## 30.8 User accidentally changes important answer

Show confirmation before saving critical fields.

Example:

```text
This answer may significantly change your matches.
```

Reason: Reduce accidental data corruption.

## 30.9 User reports someone they matched with

Preserve conversation for automated investigation.

Do not notify reported user of reporter identity.

Reason: Safety.

---

# 31. Implementation Phases

## Phase 1: Core Account and Profile

Build:

- auth,
- user model,
- profile model,
- photo upload,
- basic moderation checks,
- settings.

Exit criteria:

- user can register,
- user can create profile,
- photos are stored safely.

## Phase 2: Questions and Filters

Build:

- question schema,
- answer schema,
- filter schema,
- profile completeness,
- reality dashboard counts.

Exit criteria:

- user can answer questions,
- filters are enforced,
- profile completeness updates.

## Phase 3: Discovery and Interests

Build:

- discovery grid,
- compatibility sorting,
- interest limits,
- interest expiry,
- block/report.

Exit criteria:

- users can send limited interests,
- interests expire,
- capacity limits work.

## Phase 4: Chat

Build:

- conversations,
- messages,
- message flags,
- chat decay,
- established chats.

Exit criteria:

- mutual match opens chat,
- chat decays only before completed date,
- text analysis flags patterns.

## Phase 5: Dates and Payments

Build:

- venues,
- date proposals,
- payment holds,
- capture,
- refunds,
- vouchers,
- venue redemption.

Exit criteria:

- full date payment flow works,
- ticket is issued after capture,
- venue redemption completes date.

## Phase 6: Trust and Safety

Build:

- trust score,
- automated restrictions,
- report scoring,
- shadowban,
- appeals.

Exit criteria:

- automated moderation works without human queue.

## Phase 7: Admin and Analytics

Build:

- admin config,
- feature flags,
- analytics,
- moderation logs,
- payment ledger.

Exit criteria:

- product team can change variables safely.

---

# 32. Recommended Stack

The exact stack may be chosen by the development team, but it must support:

- relational database,
- background jobs,
- webhook handling,
- file storage,
- push notifications,
- payment authorization/capture,
- admin panel,
- config management,
- audit logging.

Example stack:

- Backend: Node.js/TypeScript or Python.
- Database: PostgreSQL.
- Cache/queue: Redis.
- File storage: S3-compatible storage.
- Payments: Stripe or equivalent.
- Push: FCM/APNs.
- Admin: internal React dashboard.
- Mobile: React Native or Flutter.

Reason: These are mature, widely supported technologies.

---

# 33. Major Product Decisions and Reasons

| Decision | Reason |
|---|---|
| No swipe deck | Reduces mindless mass swiping |
| Discovery grid | Encourages browsing with more context |
| Limited interests | Prevents spam and overwhelm |
| Incoming inbox cap | Prevents one side being flooded |
| Mutual match before chat | Prevents unsolicited messages |
| Chat after match | Allows users to talk before date |
| Structured date proposal | Reduces planning friction |
| Payment hold on proposal | Shows intent without immediate charge |
| Capture after both accept | Ensures both sides committed |
| Ticket after capture | Prevents issuing value before payment |
| Established chat after date | Does not force endless new dates |
| Hard filters strictly enforced | Builds trust |
| Algorithm sorts only | Prevents hidden manipulation |
| No threshold hiding | Users see eligible pool sorted, not censored |
| No LLM text | Product constraint and simpler compliance |
| Regex text analysis | Allows safety without generative AI |
| No mandatory ID | Reduces friction and privacy risk |
| No phone requirement | Supports users without phone plans |
| No vouching | Avoids exclusion and abuse |
| No human moderation dependency | Assumes real operating constraints |
| No profile boosts | Prevents pay-to-win visibility |
| Photo A/B testing | Uses data instead of subjective advice |
| Private tags | Reduces social desirability bias |
| Config-driven variables | Avoids digging through code for changes |

---

# 34. Definition of Done

The app is considered MVP-complete when:

1. A user can register without phone or government ID.
2. A user can answer dual 5-point questions.
3. Hard filters strictly control discovery.
4. Discovery grid sorts by compatibility.
5. Users can send limited interests.
6. Incoming interests are capped and expire.
7. Mutual interest opens chat.
8. Chat supports free-text messages after match.
9. Text analysis flags risky patterns without blocking normal messages.
10. Users can propose dates with structured venues.
11. Proposer payment hold is authorized on proposal.
12. Acceptor payment hold is authorized on acceptance.
13. Both payments capture only after both holds succeed.
14. Ticket is issued only after successful capture.
15. Venue redemption marks date completed.
16. Post-date chat becomes established.
17. Automated moderation works without human moderators.
18. Trust score is visible with actionable reasons.
19. Admin can change core variables without code deployment.
20. All payment events are recorded in an immutable ledger.

