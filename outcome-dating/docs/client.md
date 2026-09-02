# Client (app/)

The first client for this backend: Expo + TypeScript, in `app/`. Its own
dependencies live entirely in `app/package.json`, separate from the
backend's.

## Running it

```
cd app
npm install
npm run typecheck   # tsc --noEmit
npm test            # jest, 81 tests
npm start           # expo start, opens the Expo Go / simulator picker
```

Set `expo.extra.apiBaseUrl` in `app/app.json` to point at a running
backend (defaults to `http://localhost:3000`).

## Built properly (loading, empty, error states; real API calls)

1. Onboarding and sign up: email, password, birthdate, terms, optional
   city and location toggle. No phone number, no identity document.
   Age 18 enforced client-side (`domain/age.ts`) as an early check; the
   server is still the real authority.
2. Question flow: renders the control the server's `presentation`
   field names, exactly, never inferred from type or option count
   (`components/question/*`, driven by `domain/questionDraft.ts`).
   Scale, single choice, multi choice, frequency, and the collapsed
   ladder control are all covered. Skip and prefer-not-to-say are
   always visible, never gated on a complete draft.
3. Discovery grid: a real grid (`numColumns={2}`), never a swipe deck.
   An empty grid fetches `/discovery/reality` and tells cold start
   apart from over-narrow filters (`domain/discoveryReality.ts`), and
   shows the three pool numbers rather than hiding them.
4. Profile view: photos, bio, tags, trust badge, and the interest
   action. Shows interests sent today and any capability-gated reason
   before the person spends one (see Known gaps).
5. Matches and chat: `/matches` list, then `/conversations/:id/timeline`
   rendered as one merged feed, a date proposal renders as a card in
   place with venue, time, and status.
6. Date proposal and the money moment: every sentence is in
   `domain/moneyMomentCopy.ts` and rendered by `components/money/MoneySummary.tsx`,
   both covered by tests. States plainly that a hold is not a charge,
   what triggers the charge, what a decline does, and what the refund
   cutoff means, using the policy numbers the server actually returns,
   never a hardcoded figure.

## Scaffolded (real API calls, no editing/actions, not tested)

Wallet and ticket detail, the stats/pool screen, trust, settings
(units are fully wired; filter editing is read-only), and the post-date
check-in. Each has a visible "SCAFFOLDED, NOT FINISHED" banner naming
exactly what is missing.

## Known gaps found while building (not this client's bug)

- `PublicProfileResponse` has no prompts field despite a backend doc
  comment claiming one; the profile screen shows what the wire shape
  actually has (bio, photos, tags).
- No route lets a client preview the hold amount before sending a date
  proposal (`date.escrow_amount_cents` is only visible in the response
  after the hold is placed). The propose screen explains the hold
  generically, then shows the real amount immediately after, on the
  same screen the invite lands on.
- No endpoint exposes a user's remaining daily interest quota, only a
  429 after it's spent. The profile screen shows interests sent today
  instead of interests remaining.

## Verified vs. not

Verified: `tsc --noEmit` passes clean; all 81 Jest tests pass
(`domain/*`, `units/*`, `api/errors`, and component tests for every
question control and the money summary). Not verified: this has never
been opened in Expo Go, a simulator, or a device, and never run against
a live backend. Navigation wiring, keyboard behaviour, and real network
error/offline states are unverified until someone runs it for real.
