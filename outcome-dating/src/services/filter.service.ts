import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import type { FilterOperator, HardFilter } from '../domain/types.js';
import { BODY_TYPES } from '../domain/units/bodyType.js';
import { ValidationError } from '../lib/errors.js';

/**
 * filter.service, hard filters.
 * Spec: §9, §24.4 (routes).
 *
 * Owning agent: B.
 *
 * INVARIANT (spec §9.1, restated in INTERFACES.md): hard filters are
 * NEVER overridden by the compatibility algorithm. `passesMutualFilters`
 * is the sole gate `discovery.service.ts` calls before a candidate is even
 * scored, a candidate that fails it must not appear regardless of
 * compatibility score. Do not add a "soft override" path here for any
 * reason; if product wants one-sided filtering later it must be a new,
 * explicit function, not a fallback inside this one (spec §9.4 exception
 * clause: "it must be explicit").
 *
 * CANDIDATE ATTRIBUTE SOURCING (a design decision the spec leaves
 * implicit, documented here because it drives most of this file): a
 * `hard_filters` row only stores the *filter* (key/operator/value), it
 * says nothing about where a candidate's actual value for that key comes
 * from. `db/migrations/001_init.sql` (frozen, not owned by this agent)
 * gives `profiles` exactly: display_name, bio, city, latitude, longitude,
 * age, gender, seeking, relationship_intention, no smoking/drinking/
 * drugs/children/religion columns. Meanwhile spec §9.2's own examples
 * (`smoking <= 2`, `wants_children >= 4`) are numeric comparisons on a 1-5
 * scale, which is exactly the scale `answers.self_value` uses (§8.1), and
 * the seed data (`src/seed.ts`) ships a `smoking`/`wants_children`/
 * `religion`/... question in the bank with that same slug convention. So:
 *   - `age_min` / `age_max` resolve against `profiles.age`.
 *   - `distance_km` resolves against the haversine distance between the
 *     two users' `profiles.latitude/longitude` (never the fuzzed/exposed
 *     value, see `discovery.service.ts` for the rounded value shown on a
 *     card, §7.1/§28.5).
 *   - `gender_preference` resolves against `profiles.gender`.
 *   - `relationship_intention` resolves against `profiles.relationship_intention`.
 *   - `height_cm` / `weight_g` resolve against `profiles.height_cm` /
 *     `profiles.weight_g` (this build, `db/migrations/009_units_attributes.sql`)
 * always the CANONICAL stored value, never a display unit (see
 *     `src/domain/units/`). `weight_g` additionally resolves as
 *     UNRESOLVED whenever `profiles.weight_visible` is false: a hidden
 *     weight is invisible to filter matching exactly as it is invisible
 *     on the public profile view, not merely hidden from display while
 *     still usable to gate matches (see `profile.service.ts`'s
 *     `PublicProfileView` doc for the same discipline applied there).
 *   - `body_type` resolves against `profiles.body_type`, a categorical
 *     value, so a body-type PREFERENCE is expressed as a SET of
 *     acceptable values via the existing `in` operator, never a numeric
 *     midpoint comparison.
 *   - a `qb:`-prefixed key (e.g. `qb:children_intention`) resolves against
 *     the candidate's `user_question_answers.self_value` for the ONE typed
 *     question bank (db/migrations/008_questions.sql) row whose
 *     `question_slug` equals `filterKey.slice(3)`, UNRESOLVED unless that
 *     row's `status = 'answered'` (an unanswered/skipped/
 *     `prefer_not_to_say` self value can't be compared, this is
 *     deliberate: it's what lets `prefer_not_to_say` still fail a
 *     deal-breaker filter, since `evaluateFilter` treats `undefined` as
 *     failing whenever `excludeIfUnset` is true). The `qb:` namespace is
 *     populated by `question.service#getMyDealBreakerFilterRows`
 *     (deal-breaker-derived rows) but is not reserved to it alone: any
 *     caller of `updateMyFilters` may target `qb:<slug>` directly for a
 *     non-deal-breaker filter against a new-bank question too.
 *   - any OTHER key (has_children, wants_children, smoking, drinking,
 *     drug_use, religion, and any admin-defined key not spelled `qb:...`)
 *     is always UNRESOLVED. See QUESTION-SYSTEM CUTOVER below, this used
 *     to be a read-compatibility shim against the OLD `answers`/
 *     `questions` tables; those tables are gone, and so is the shim.
 *
 * QUESTION-SYSTEM CUTOVER, COMPLETE. The redesigned typed question bank
 * (`question_bank`/`user_question_answers`, `qb:`-prefixed keys above) is
 * the ONE bank every user-reachable route, `compatibility.service.ts`, and
 * every `hard_filters` row uses, see
 * `src/services/question.service.ts`'s file-level CUTOVER doc. This
 * file's bare-slug (non-`qb:`) resolution against the OLD `answers`/
 * `questions` tables has been REMOVED (`db/migrations/022_drop_old_question_bank.sql`
 * drops both tables). A first attempt at removing this resolution path,
 * before the tables themselves could be dropped, broke several test
 * suites that planted an old-bank answer via a bare filter key as their
 * normal way of exercising filter-gated behavior
 * (`tests/unit/eligibility.test.ts`/`testCtxEligibility.ts`,
 * `tests/unit/autoDecline.test.ts`, `tests/unit/profileAttributes.test.ts`)
 * those suites have been updated to use the `qb:`-prefixed form against
 * the typed bank instead (see each file's own history), so removing the
 * shim now breaks nothing. Any `hard_filters` row that was still keyed on
 * a bare old-bank slug at the time of the drop is handled by
 * `db/migrations/022_drop_old_question_bank.sql` itself (see that file's
 * header for the cleanup and why it's a deletion, not a migration to
 * `qb:`).
 *
 * MISSING/UNRESOLVED VALUES, the `excludeIfUnset` toggle (product
 * decision, no § reference; supersedes this file's original unconditional
 * "always fails closed" behavior). Every hard-filter row now carries an
 * `excludeIfUnset: boolean` (`hard_filters.exclude_if_unset`,
 * `009_units_attributes.sql`): when a candidate's value for a filter's
 * key cannot be resolved (`resolveAttributeValue` returns `undefined`),
 * `evaluateFilter` EXCLUDES that candidate if `excludeIfUnset` is true,
 * and INCLUDES them (does not fail the filter) if it is false. This is a
 * per-row, per-user, explicit choice, not a hardcoded rule:
 *   - Default when the caller omits it: FALSE, for EVERY filter key, no
 *     exceptions, including keys derived from a DEAL-BREAKER preference
 *     (built by another agent in `src/domain/questions/`, not this
 *     file). This went through two narrower designs before landing here
 *     (first "true for everything", then "true except three physical-
 *     attribute keys"), both were rejected by the product owner for the
 *     same underlying reason: a brand-new account has not filled
 *     everything in yet, and must not be punished for that. Someone who
 *     just signed up and has not entered a height (or answered the
 *     question a deal-breaker filter is derived from) should still be
 *     discoverable while they finish their profile, silently
 *     disappearing from every OTHER user's results because a field is
 *     blank is exactly the failure this toggle exists to prevent, and an
 *     opt-out-by-default policy re-creates that failure for anyone who
 *     forgets to opt in. So: nothing is ever excluded by an unresolved
 *     value unless a user (or a deal-breaker derivation acting on that
 *     user's explicit request) deliberately sets `excludeIfUnset: true`
 *     for that specific filter, see `defaultExcludeIfUnset`, which
 *     still takes a `filterKey` argument (for interface stability and
 *     so a future per-key exception, if product ever asks for one again,
 *     has a single place to live) but currently ignores it.
 *   - `updateMyFilters` always honors an EXPLICIT `excludeIfUnset` over
 *     this default, a deal-breaker derivation, or a user's own toggle,
 *     passing `true` is respected exactly. No change is needed in this
 *     file for the deal-breaker-derivation agent's code to work; the
 *     field's existence and this default are flagged in this build's
 *     report so that agent knows to set it explicitly when (and only
 *     when) the user has asked for that deal-breaker to be strict about
 *     unknowns.
 *   - The `hard_filters.exclude_if_unset` COLUMN default (used only by
 *     inserts that bypass this service, e.g. raw SQL fixtures) is
 *     `false`, matching the application-level default above exactly,
 *     there is no longer any filter category with a different default.
 *   - The toggle only ever changes how a filter treats an UNRESOLVED
 *     value; it never reads, writes, or otherwise touches any stored
 *     profile attribute.
 */

export interface UpdateFilterInput {
  filterKey: string;
  operator: FilterOperator;
  value: unknown;
  enabled: boolean;
  /**
   * Whether a candidate whose value for `filterKey` cannot be resolved is
   * EXCLUDED (`true`) or still allowed through (`false`). Optional: when
   * omitted, `updateMyFilters` applies `defaultExcludeIfUnset(filterKey)`
   * see the file-level "MISSING/UNRESOLVED VALUES" note. Passing this
   * explicitly always wins over that default, and over whatever value was
   * previously stored for this filter.
   */
  excludeIfUnset?: boolean;
}

/**
 * `HardFilter` (`domain/types.ts`, not owned by this agent) predates the
 * `excludeIfUnset` toggle. Rather than edit a file outside this build's
 * ownership boundary, every row this service returns is `HardFilter`
 * PLUS that one field, a strict superset, so every existing consumer
 * that only knows about `HardFilter`'s original fields keeps compiling
 * unchanged (structural typing: extra properties on a returned object
 * are never a type error, only excess properties on an object LITERAL
 * checked directly against a narrower annotated type would be).
 */
export interface HardFilterWithUnsetPolicy extends HardFilter {
  excludeIfUnset: boolean;
}

interface HardFilterRow {
  user_id: string;
  filter_key: string;
  operator: FilterOperator;
  value: unknown;
  enabled: boolean;
  exclude_if_unset: boolean;
  updated_at: Date;
}

function filterFromRow(row: HardFilterRow): HardFilterWithUnsetPolicy {
  return {
    userId: row.user_id,
    filterKey: row.filter_key,
    operator: row.operator,
    value: row.value,
    enabled: row.enabled,
    excludeIfUnset: row.exclude_if_unset,
    updatedAt: row.updated_at,
  };
}

export async function getMyFilters(ctx: Ctx): Promise<HardFilterWithUnsetPolicy[]> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<HardFilterRow>(
    'SELECT * FROM hard_filters WHERE user_id = $1 ORDER BY filter_key',
    [userId],
  );
  return rows.map(filterFromRow);
}

const filterOperatorSchema = z.enum(['eq', 'neq', 'gte', 'lte', 'gt', 'lt', 'in']);

const updateFilterInputSchema = z.object({
  filterKey: z.string().min(1).max(100),
  operator: filterOperatorSchema,
  value: z.unknown(),
  enabled: z.boolean(),
  excludeIfUnset: z.boolean().optional(),
});

/**
 * Default for an omitted `excludeIfUnset`, for any filter key, see the
 * file-level "MISSING/UNRESOLVED VALUES" note. Always `false` (unset
 * values are INCLUDED, never excluded, unless a caller opts in
 * explicitly), with no per-key exception. Still takes `filterKey` and is
 * exported as a named function, rather than inlining `false`, so callers
 * never hardcode the policy themselves and a future per-key exception
 * (if product ever asks for one again) has exactly one place to live.
 */
export function defaultExcludeIfUnset(_filterKey: string): boolean {
  return false;
}

/**
 * Upserts the caller's filters. Does not cap the number of filter slots
 * (spec §9.2 "do not block filter slots").
 *
 * DELIBERATELY HAS NO SIDE EFFECT on any existing interest, match, or
 * conversation (product-owner correction, an earlier build had this
 * retroactively auto-decline the caller's now-ineligible PENDING
 * incoming interests; that has been removed, and must not be re-added
 * here). Saving a filter change is not a judgment on relationships that
 * already exist, people narrow and widen their filters for ordinary
 * reasons, and doing so must never destroy a pending like or a
 * conversation. A user who genuinely wants to tidy their inbox after
 * narrowing their filters can do that explicitly and separately via
 * `interest.service.ts#previewFilterCleanup` / `runFilterCleanup` (see
 * that file's "CORRECTION" note for the full reasoning), this function
 * must never call either, or anything like them, itself.
 */
export async function updateMyFilters(ctx: Ctx, filters: UpdateFilterInput[]): Promise<HardFilterWithUnsetPolicy[]> {
  const { userId } = requireUserActor(ctx);
  const parsed = z.array(updateFilterInputSchema).parse(filters);

  for (const f of parsed) {
    if (f.filterKey === 'body_type') {
      const candidates = f.operator === 'in' ? f.value : [f.value];
      if (!Array.isArray(candidates) || !candidates.every((v) => (BODY_TYPES as readonly unknown[]).includes(v))) {
        throw new ValidationError(`body_type filter value must be one of: ${BODY_TYPES.join(', ')}`, {
          filterKey: f.filterKey,
          value: f.value,
        });
      }
    }
    const excludeIfUnset = f.excludeIfUnset ?? defaultExcludeIfUnset(f.filterKey);
    await ctx.db.query(
      `INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled, exclude_if_unset, updated_at)
       VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7)
       ON CONFLICT (user_id, filter_key) DO UPDATE SET
         operator = EXCLUDED.operator,
         value = EXCLUDED.value,
         enabled = EXCLUDED.enabled,
         exclude_if_unset = EXCLUDED.exclude_if_unset,
         updated_at = EXCLUDED.updated_at`,
      [userId, f.filterKey, f.operator, JSON.stringify(f.value), f.enabled, excludeIfUnset, ctx.clock.now()],
    );
  }

  const { rows } = await ctx.db.query<HardFilterRow>(
    'SELECT * FROM hard_filters WHERE user_id = $1 ORDER BY filter_key',
    [userId],
  );
  return rows.map(filterFromRow);
}

/**
 * Pure evaluation of one filter against one candidate attribute value,
 * no I/O. Exported so both `passesMutualFilters` and unit tests can use
 * the exact same operator semantics.
 *
 * `candidateValue === undefined` means "could not be resolved". What
 * happens then is `excludeIfUnset` (see the file-level "MISSING/
 * UNRESOLVED VALUES" note): `true` fails the filter (excludes the
 * candidate); `false`, the default parameter value, matching
 * `defaultExcludeIfUnset`'s current universal default, passes it despite
 * the unresolved value. `null` is a resolved-but-empty value and is
 * compared normally (so `neq: null` etc. behave as expected), only
 * `undefined` triggers this branch at all.
 */
export function evaluateFilter(
  filter: Pick<HardFilter, 'operator' | 'value'>,
  candidateValue: unknown,
  excludeIfUnset = false,
): boolean {
  if (candidateValue === undefined) return !excludeIfUnset;

  const { operator, value } = filter;

  switch (operator) {
    case 'eq':
      return deepEqual(candidateValue, value);
    case 'neq':
      return !deepEqual(candidateValue, value);
    case 'in': {
      if (!Array.isArray(value)) return false;
      if (Array.isArray(candidateValue)) {
        // Overlap semantics: true iff `candidateValue` shares at least one
        // element with `value`. This is what a `multi_choice` deal-breaker
        // preference means ("must include at least one of: Spanish,
        // French"), see src/domain/questions/dealBreakers.ts's
        // (now-resolved) KNOWN LIMITATION note. A scalar-membership check
        // (`value.some(v => deepEqual(v, candidateValue))`) can never match
        // a whole array against one scalar entry, so this branch only ever
        // activates for an array `candidateValue`, every pre-existing
        // scalar usage (age/gender/body_type/single_choice) is untouched
        // by the `else` branch below.
        return value.some((v) => candidateValue.some((c) => deepEqual(v, c)));
      }
      return value.some((v) => deepEqual(v, candidateValue));
    }
    case 'gte':
    case 'lte':
    case 'gt':
    case 'lt': {
      const a = toComparableNumber(candidateValue);
      const b = toComparableNumber(value);
      if (a === undefined || b === undefined) return false;
      if (operator === 'gte') return a >= b;
      if (operator === 'lte') return a <= b;
      if (operator === 'gt') return a > b;
      return a < b;
    }
    default:
      return false;
  }
}

function toComparableNumber(v: unknown): number | undefined {
  if (typeof v === 'number') return Number.isFinite(v) ? v : undefined;
  if (typeof v === 'string' && v.trim() !== '' && Number.isFinite(Number(v))) return Number(v);
  return undefined;
}

function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (typeof a !== typeof b) return false;
  if (a === null || b === null) return false;
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
    return a.every((v, i) => deepEqual(v, b[i]));
  }
  if (typeof a === 'object' && typeof b === 'object') {
    return JSON.stringify(a) === JSON.stringify(b);
  }
  return false;
}

// =====================================================================
// Candidate attribute resolution (see file-level "CANDIDATE ATTRIBUTE
// SOURCING" note).
// =====================================================================

interface ProfileLocationAge {
  age: number | null;
  gender: string | null;
  relationshipIntention: string | null;
  latitude: number | null;
  longitude: number | null;
  /** Canonical centimetres, or `null` if the user never set it, see `src/domain/units/height.ts`. */
  heightCm: number | null;
  /** Canonical grams, or `null` if the user never set it, see `src/domain/units/weight.ts`. */
  weightG: number | null;
  weightVisible: boolean;
  bodyType: string | null;
}

async function loadProfile(ctx: Ctx, userId: string): Promise<ProfileLocationAge | undefined> {
  const { rows } = await ctx.db.query<{
    age: number;
    gender: string;
    relationship_intention: string;
    latitude: number | null;
    longitude: number | null;
    height_cm: number | null;
    weight_g: number | null;
    weight_visible: boolean;
    body_type: string | null;
  }>(
    `SELECT age, gender, relationship_intention, latitude, longitude, height_cm, weight_g, weight_visible, body_type
     FROM profiles WHERE user_id = $1`,
    [userId],
  );
  const row = rows[0];
  if (!row) return undefined;
  return {
    age: row.age,
    gender: row.gender,
    relationshipIntention: row.relationship_intention,
    latitude: row.latitude,
    longitude: row.longitude,
    heightCm: row.height_cm,
    weightG: row.weight_g,
    weightVisible: row.weight_visible,
    bodyType: row.body_type,
  };
}

/** Great-circle distance in km between two lat/long points. */
export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Resolves a `qb:`-prefixed filter key's candidate value against the NEW
 * typed question bank, see the file-level "CANDIDATE ATTRIBUTE SOURCING"
 * note. Only an `answered` row resolves to a concrete `self_value`;
 * absent, `skipped`, or `prefer_not_to_say` are all UNRESOLVED
 * (`undefined`), deliberately, so `prefer_not_to_say` can still fail a
 * strict (`excludeIfUnset: true`) deal-breaker filter exactly like an
 * absent answer does, matching `dealBreakers.ts`'s documented
 * "RESOLUTION NOTE".
 */
async function loadQuestionBankSelfValue(ctx: Ctx, userId: string, slug: string): Promise<unknown> {
  const { rows } = await ctx.db.query<{ status: string; self_value: unknown }>(
    `SELECT status, self_value FROM user_question_answers WHERE user_id = $1 AND question_slug = $2`,
    [userId, slug],
  );
  const row = rows[0];
  if (!row || row.status !== 'answered') return undefined;
  return row.self_value;
}

/** Resolves `subjectUserId`'s value for `filterKey`, given `filterOwnerUserId` (needed only for distance, which is relative to the filter owner). */
async function resolveAttributeValue(
  ctx: Ctx,
  subjectUserId: string,
  filterOwnerUserId: string,
  filterKey: string,
): Promise<unknown> {
  switch (filterKey) {
    case 'age_min':
    case 'age_max': {
      const profile = await loadProfile(ctx, subjectUserId);
      return profile?.age ?? undefined;
    }
    case 'distance_km': {
      const [subject, owner] = await Promise.all([
        loadProfile(ctx, subjectUserId),
        loadProfile(ctx, filterOwnerUserId),
      ]);
      if (
        subject?.latitude == null ||
        subject?.longitude == null ||
        owner?.latitude == null ||
        owner?.longitude == null
      ) {
        return undefined;
      }
      return haversineKm(subject.latitude, subject.longitude, owner.latitude, owner.longitude);
    }
    case 'gender_preference': {
      const profile = await loadProfile(ctx, subjectUserId);
      return profile?.gender ?? undefined;
    }
    case 'relationship_intention': {
      const profile = await loadProfile(ctx, subjectUserId);
      return profile?.relationshipIntention ?? undefined;
    }
    case 'height_cm': {
      const profile = await loadProfile(ctx, subjectUserId);
      return profile?.heightCm ?? undefined;
    }
    case 'weight_g': {
      const profile = await loadProfile(ctx, subjectUserId);
      // A hidden weight is UNRESOLVED for filtering, not merely hidden from
      // display, see the file-level CANDIDATE ATTRIBUTE SOURCING note.
      if (!profile || !profile.weightVisible || profile.weightG == null) return undefined;
      return profile.weightG;
    }
    case 'body_type': {
      const profile = await loadProfile(ctx, subjectUserId);
      return profile?.bodyType ?? undefined;
    }
    default:
      // See file-level QUESTION-SYSTEM CUTOVER note, only a `qb:`-prefixed
      // key resolves against the typed bank; anything else is always
      // unresolved (the OLD bank's bare-slug resolution has been removed).
      return filterKey.startsWith('qb:') ? loadQuestionBankSelfValue(ctx, subjectUserId, filterKey.slice(3)) : undefined;
  }
}

/**
 * Does `subjectUserId`'s resolved attributes satisfy every *enabled* hard
 * filter owned by `filterOwnerUserId`? Filterless users trivially pass.
 *
 * `unsetPolicyOverride` lets a caller ask "what if THIS ONE filter key's
 * `excludeIfUnset` were different" without writing anything, the
 * mechanism `previewPoolSizeWithUnsetPolicy` uses to answer "how many
 * candidates would flipping this toggle cost me" before the user commits
 * to the change (product owner's pool-count-visibility requirement).
 */
async function subjectPassesFiltersOf(
  ctx: Ctx,
  subjectUserId: string,
  filterOwnerUserId: string,
  unsetPolicyOverride?: { filterKey: string; excludeIfUnset: boolean },
): Promise<boolean> {
  const { rows } = await ctx.db.query<{ filter_key: string; operator: FilterOperator; value: unknown; exclude_if_unset: boolean }>(
    'SELECT filter_key, operator, value, exclude_if_unset FROM hard_filters WHERE user_id = $1 AND enabled = true',
    [filterOwnerUserId],
  );
  for (const f of rows) {
    const candidateValue = await resolveAttributeValue(ctx, subjectUserId, filterOwnerUserId, f.filter_key);
    const excludeIfUnset =
      unsetPolicyOverride && unsetPolicyOverride.filterKey === f.filter_key
        ? unsetPolicyOverride.excludeIfUnset
        : f.exclude_if_unset;
    if (!evaluateFilter({ operator: f.operator, value: f.value }, candidateValue, excludeIfUnset)) return false;
  }
  return true;
}

/**
 * §9.4 mutual filter check: does `userId` pass `candidateId`'s enabled
 * hard filters, AND does `candidateId` pass `userId`'s? Both directions
 * are required for discovery visibility by default (spec §9.4).
 */
export async function passesMutualFilters(ctx: Ctx, userId: string, candidateId: string): Promise<boolean> {
  const [candidatePassesMine, userPassesCandidates] = await Promise.all([
    subjectPassesFiltersOf(ctx, candidateId, userId),
    subjectPassesFiltersOf(ctx, userId, candidateId),
  ]);
  return candidatePassesMine && userPassesCandidates;
}

// =====================================================================
// SCALE FIX (docs/scale-and-sources.md Part 1, §1.1.2/§1.1.4 fix #2):
// batched filter evaluation.
//
// `subjectPassesFiltersOf` above is correct but does 1 query for the
// owner's filter rows PLUS 1 query per enabled filter, per call, fine
// for a single known pair (that's still how `passesMutualFilters` and
// `eligibility.service.ts` use it, unchanged), catastrophic when called
// in a loop over a whole candidate pool. Everything below computes the
// exact same result (same `resolveAttributeValue` switch, same
// `evaluateFilter`, reused verbatim) for MANY (subject, owner) pairs at
// once, in a number of queries that does NOT grow with the number of
// pairs, see `evaluateFilterPairsBatch`'s doc for the fixed query
// budget. `discovery.service.ts`'s candidate-pool gate,
// `countUsersMatchingMyFilters`, and `countUsersWhoseFiltersIMatch` all
// go through this now; `previewPoolSizeWithUnsetPolicy` uses the same
// batched attribute maps directly (it needs a per-call `excludeIfUnset`
// override `evaluateFilterPairsBatch` doesn't take a parameter for).
// =====================================================================

/** Filter keys resolved straight off a `profiles` row, see `resolveAttributeValue`. Anything not in this set is a slug-based `answers` lookup (the `default` case there). */
const STRUCTURED_ATTRIBUTE_KEYS: ReadonlySet<string> = new Set([
  'age_min',
  'age_max',
  'distance_km',
  'gender_preference',
  'relationship_intention',
  'height_cm',
  'weight_g',
  'body_type',
]);

interface AttributeMaps {
  profiles: Map<string, ProfileLocationAge>;
  /** userId -> question_bank slug -> self_value (typed per question, a number, string, or string[] depending on question type; may legitimately be `null`). Absent key = unresolved (never answered, or answered but not `status = 'answered'`), exactly like `loadQuestionBankSelfValue`'s `undefined`. Keyed by `qb:`-prefixed filter keys' resolution. */
  answers: Map<string, Map<string, unknown>>;
}

/** Batched `loadProfile`, one query for as many users as needed, instead of one query per user. Missing rows are simply absent from the map, exactly like `loadProfile` returning `undefined`. */
async function loadProfilesBatch(ctx: Ctx, userIds: string[]): Promise<Map<string, ProfileLocationAge>> {
  const map = new Map<string, ProfileLocationAge>();
  const ids = [...new Set(userIds)];
  if (ids.length === 0) return map;
  const { rows } = await ctx.db.query<{
    user_id: string;
    age: number;
    gender: string;
    relationship_intention: string;
    latitude: number | null;
    longitude: number | null;
    height_cm: number | null;
    weight_g: number | null;
    weight_visible: boolean;
    body_type: string | null;
  }>(
    `SELECT user_id, age, gender, relationship_intention, latitude, longitude, height_cm, weight_g, weight_visible, body_type
     FROM profiles WHERE user_id = ANY($1::uuid[])`,
    [ids],
  );
  for (const row of rows) {
    map.set(row.user_id, {
      age: row.age,
      gender: row.gender,
      relationshipIntention: row.relationship_intention,
      latitude: row.latitude,
      longitude: row.longitude,
      heightCm: row.height_cm,
      weightG: row.weight_g,
      weightVisible: row.weight_visible,
      bodyType: row.body_type,
    });
  }
  return map;
}

/** Batched `loadQuestionBankSelfValue`, one query for as many (user, slug) combinations as needed. `slugs` should already be deduplicated to the `qb:`-prefixed filter keys actually in play, with the prefix stripped (see callers). Only `status = 'answered'` rows are included, see `loadQuestionBankSelfValue`'s doc for why absent/skipped/prefer_not_to_say must stay unresolved rather than resolving to `null`. */
async function loadQuestionBankAnswersBatch(ctx: Ctx, userIds: string[], slugs: string[]): Promise<Map<string, Map<string, unknown>>> {
  const map = new Map<string, Map<string, unknown>>();
  const ids = [...new Set(userIds)];
  if (ids.length === 0 || slugs.length === 0) return map;
  const { rows } = await ctx.db.query<{ user_id: string; question_slug: string; status: string; self_value: unknown }>(
    `SELECT user_id, question_slug, status, self_value
     FROM user_question_answers
     WHERE user_id = ANY($1::uuid[]) AND question_slug = ANY($2::text[])`,
    [ids, slugs],
  );
  for (const row of rows) {
    if (row.status !== 'answered') continue;
    let perUser = map.get(row.user_id);
    if (!perUser) {
      perUser = new Map();
      map.set(row.user_id, perUser);
    }
    perUser.set(row.question_slug, row.self_value);
  }
  return map;
}

/** Same resolution as `resolveAttributeValue`, but reading from preloaded maps instead of issuing a query, MUST stay behaviorally identical to that function, switch case for switch case, since both exist only because a caller needs this either per-pair (I/O) or batched (maps). */
function resolveAttributeValueFromMaps(
  subjectUserId: string,
  filterOwnerUserId: string,
  filterKey: string,
  maps: AttributeMaps,
): unknown {
  switch (filterKey) {
    case 'age_min':
    case 'age_max':
      return maps.profiles.get(subjectUserId)?.age ?? undefined;
    case 'distance_km': {
      const subject = maps.profiles.get(subjectUserId);
      const owner = maps.profiles.get(filterOwnerUserId);
      if (subject?.latitude == null || subject?.longitude == null || owner?.latitude == null || owner?.longitude == null) {
        return undefined;
      }
      return haversineKm(subject.latitude, subject.longitude, owner.latitude, owner.longitude);
    }
    case 'gender_preference':
      return maps.profiles.get(subjectUserId)?.gender ?? undefined;
    case 'relationship_intention':
      return maps.profiles.get(subjectUserId)?.relationshipIntention ?? undefined;
    case 'height_cm':
      return maps.profiles.get(subjectUserId)?.heightCm ?? undefined;
    case 'weight_g': {
      const profile = maps.profiles.get(subjectUserId);
      if (!profile || !profile.weightVisible || profile.weightG == null) return undefined;
      return profile.weightG;
    }
    case 'body_type':
      return maps.profiles.get(subjectUserId)?.bodyType ?? undefined;
    default: {
      // See file-level QUESTION-SYSTEM CUTOVER note, only `qb:<slug>`
      // resolves against the typed bank; anything else is always
      // unresolved.
      if (!filterKey.startsWith('qb:')) return undefined;
      const slug = filterKey.slice(3);
      const perUser = maps.answers.get(subjectUserId);
      if (!perUser || !perUser.has(slug)) return undefined;
      return perUser.get(slug);
    }
  }
}

async function loadAttributeMapsFor(ctx: Ctx, userIds: string[], filterRows: HardFilterRow[]): Promise<AttributeMaps> {
  const qbSlugs = new Set<string>();
  for (const r of filterRows) {
    if (STRUCTURED_ATTRIBUTE_KEYS.has(r.filter_key)) continue;
    if (r.filter_key.startsWith('qb:')) qbSlugs.add(r.filter_key.slice(3));
    // Any other key is always unresolved, see file-level QUESTION-SYSTEM
    // CUTOVER note, so there is nothing to batch-load for it.
  }
  const [profiles, answers] = await Promise.all([
    loadProfilesBatch(ctx, userIds),
    qbSlugs.size > 0 ? loadQuestionBankAnswersBatch(ctx, userIds, [...qbSlugs]) : Promise.resolve(new Map<string, Map<string, unknown>>()),
  ]);
  return { profiles, answers };
}

export interface FilterCheckPair {
  subjectId: string;
  ownerId: string;
}

/**
 * Evaluates "does `subjectId` satisfy `ownerId`'s enabled hard filters"
 * for every pair in `pairs`, in a FIXED number of queries regardless of
 * how many pairs are given: one `hard_filters` fetch for every distinct
 * owner in the batch, one `profiles` fetch for every distinct subject/
 * owner id in the batch, and (only if at least one filter key needs it)
 * one `answers` fetch for every distinct subject/owner id, i.e. at most
 * 3 queries total, never `O(pairs)`. Returns results in the same order
 * as `pairs`.
 */
export async function evaluateFilterPairsBatch(ctx: Ctx, pairs: FilterCheckPair[]): Promise<boolean[]> {
  if (pairs.length === 0) return [];

  const ownerIds = [...new Set(pairs.map((p) => p.ownerId))];
  const { rows: filterRows } = await ctx.db.query<HardFilterRow>(
    `SELECT user_id, filter_key, operator, value, exclude_if_unset FROM hard_filters WHERE enabled = true AND user_id = ANY($1::uuid[])`,
    [ownerIds],
  );
  const filtersByOwner = new Map<string, HardFilterRow[]>();
  for (const r of filterRows) {
    const list = filtersByOwner.get(r.user_id);
    if (list) list.push(r);
    else filtersByOwner.set(r.user_id, [r]);
  }

  const allIds = new Set<string>();
  for (const p of pairs) {
    allIds.add(p.subjectId);
    allIds.add(p.ownerId);
  }
  const maps = await loadAttributeMapsFor(ctx, [...allIds], filterRows);

  return pairs.map(({ subjectId, ownerId }) => {
    const filters = filtersByOwner.get(ownerId) ?? [];
    for (const f of filters) {
      const value = resolveAttributeValueFromMaps(subjectId, ownerId, f.filter_key, maps);
      if (!evaluateFilter({ operator: f.operator, value: f.value }, value, f.exclude_if_unset)) return false;
    }
    return true;
  });
}

/**
 * Batched `passesMutualFilters` for a whole candidate pool at once,
 * `discovery.service.ts`'s replacement for calling `passesMutualFilters`
 * per candidate in a loop. Same semantics (both directions must pass),
 * same fixed (≤3-query) cost as `evaluateFilterPairsBatch` regardless of
 * `candidateIds.length`.
 */
export async function passesMutualFiltersForCandidates(
  ctx: Ctx,
  viewerId: string,
  candidateIds: string[],
): Promise<Set<string>> {
  const passing = new Set<string>();
  if (candidateIds.length === 0) return passing;

  const pairs: FilterCheckPair[] = [];
  for (const candidateId of candidateIds) {
    pairs.push({ subjectId: candidateId, ownerId: viewerId });
    pairs.push({ subjectId: viewerId, ownerId: candidateId });
  }
  const results = await evaluateFilterPairsBatch(ctx, pairs);
  for (let i = 0; i < candidateIds.length; i++) {
    if (results[2 * i] && results[2 * i + 1]) passing.add(candidateIds[i]!);
  }
  return passing;
}

// =====================================================================
// SCALE FIX (docs/scale-and-sources.md Part 1, §1.3/§1.9 fix #1):
// geographic bounding.
//
// "Who is near me" was implemented as "who exists, filtered client-side
// after every row is already pulled across the network", no bound, no
// index used. `boundingBoxForRadius` computes a plain lat/long bounding
// BOX (not a circle, a box that fully CONTAINS the circle of the given
// radius, so it can only ever admit extra candidates for the exact
// `haversineKm`/mutual-filter check downstream to then correctly reject,
// never wrongly exclude one that should pass). Deliberately NOT a new
// Postgres extension (no PostGIS, no earthdistance/cube): a composite
// btree index on `profiles (latitude, longitude)` is enough to make this
// box a real index-range prefilter (see
// `db/migrations/017_discovery_perf.sql`), and it avoids adding an
// extension dependency this codebase has never had, for a win a plain
// index already delivers at this codebase's scale (tens of thousands of
// candidates per city, not billions of geometries), see this build's
// report for the measured numbers.
//
// This box only ever narrows WHICH ROWS THE QUERY LOOKS AT for
// performance, it is never the thing that decides whether a candidate
// is a legitimate match. The exact mutual `distance_km` filter (via
// `haversineKm`, unchanged, exact-not-jittered, see the CANDIDATE
// ATTRIBUTE SOURCING note at the top of this file) and the SAF-2 privacy
// bucketing/jitter (`domain/units/distance.ts`, untouched by this build)
// both still run exactly as before, on whatever the box lets through.
// =====================================================================

export interface GeoBox {
  latMin: number;
  latMax: number;
  /** Two longitude ranges, OR'd together, so a box near the antimeridian (±180°) can be expressed without wraparound arithmetic in SQL. Identical (duplicated) range when the box doesn't cross the antimeridian, see below. */
  lon1Min: number;
  lon1Max: number;
  lon2Min: number;
  lon2Max: number;
}

const KM_PER_DEGREE_LAT = 111.32;

/**
 * A lat/long bounding box that fully contains every point within
 * `radiusKm` of `(lat, lon)`. Pure, no I/O, see `tests/unit/filter.test.ts`
 * for coverage of the equator/high-latitude/pole/antimeridian cases.
 *
 * Handles two edge cases a naive `lat ± d, lon ± d` box gets wrong:
 *   - Longitude degrees shrink toward the poles (`cos(latitude)`); using
 *     the box's own most-poleward latitude keeps the box from being too
 *     NARROW in longitude near a pole (over-narrow would wrongly drop
 *     real candidates, this function must only ever err toward "too
 *     wide", never "too narrow").
 *   - A box whose longitude span crosses ±180° (or one close enough to a
 *     pole that "east/west" stops being meaningful) is expressed as two
 *     OR'd ranges rather than silently wrapping into an inverted (empty)
 *     range.
 */
export function boundingBoxForRadius(lat: number, lon: number, radiusKm: number): GeoBox {
  const radius = Math.max(0.001, radiusKm);
  const latDelta = radius / KM_PER_DEGREE_LAT;
  let latMin = lat - latDelta;
  let latMax = lat + latDelta;
  const overrunsPole = latMax >= 90 || latMin <= -90;
  latMin = Math.max(-90, latMin);
  latMax = Math.min(90, latMax);

  if (overrunsPole) {
    // Every longitude is within radius of a point this close to a pole.
    return { latMin, latMax, lon1Min: -180, lon1Max: 180, lon2Min: -180, lon2Max: 180 };
  }

  const maxAbsLat = Math.max(Math.abs(latMin), Math.abs(latMax));
  const kmPerDegreeLon = Math.max(0.01, KM_PER_DEGREE_LAT * Math.cos((maxAbsLat * Math.PI) / 180));
  const lonDelta = radius / kmPerDegreeLon;

  if (lonDelta >= 180) {
    return { latMin, latMax, lon1Min: -180, lon1Max: 180, lon2Min: -180, lon2Max: 180 };
  }

  const lonMin = lon - lonDelta;
  const lonMax = lon + lonDelta;

  if (lonMin < -180) {
    return { latMin, latMax, lon1Min: -180, lon1Max: lonMax, lon2Min: lonMin + 360, lon2Max: 180 };
  }
  if (lonMax > 180) {
    return { latMin, latMax, lon1Min: lonMin, lon1Max: 180, lon2Min: -180, lon2Max: lonMax - 360 };
  }
  return { latMin, latMax, lon1Min: lonMin, lon1Max: lonMax, lon2Min: lonMin, lon2Max: lonMax };
}

/**
 * Would-ideally-be-config default search radius (km) used to build the
 * bounding box when a user has no enabled `distance_km` filter of their
 * own, same file-ownership-boundary situation as
 * `discovery.service.ts#MIN_PROFILE_COMPLETENESS_FOR_DISCOVERY` and
 * `compatibility.service.ts#DEFAULT_MIN_SHARED_QUESTIONS`
 * (`src/config/config.service.ts` is outside this build's ownership
 * boundary), flagged in this build's report as a natural
 * `discovery.default_search_radius_km` config key for whoever next
 * touches that file. ~160km ("greater metro area" scale) is wide enough
 * to be a sane default for someone who hasn't set a preference, without
 * defeating the whole point of bounding the query.
 */
export const DEFAULT_DISCOVERY_RADIUS_KM = 160;

/** The user's own `distance_km` filter value, if enabled and expressed as an upper bound (`lte`/`lt`, the only operators spec §9.2's own examples use for this key and the only ones a "maximum distance" reading makes sense for); `DEFAULT_DISCOVERY_RADIUS_KM` otherwise. Used ONLY to size the bounding box (a performance prefilter), the exact filter (any operator, including an unusual `gte`/`gt`/`eq`/`neq`/`in`) is still enforced exactly, unchanged, by `evaluateFilterPairsBatch`/`passesMutualFilters` downstream regardless of what this resolves to. */
async function resolveSearchRadiusKm(ctx: Ctx, userId: string): Promise<number> {
  const { rows } = await ctx.db.query<{ operator: FilterOperator; value: unknown }>(
    `SELECT operator, value FROM hard_filters WHERE user_id = $1 AND filter_key = 'distance_km' AND enabled = true`,
    [userId],
  );
  const row = rows[0];
  if (row && (row.operator === 'lte' || row.operator === 'lt')) {
    const n = toComparableNumber(row.value);
    if (n !== undefined && n > 0) return n;
  }
  return DEFAULT_DISCOVERY_RADIUS_KM;
}

export interface GeoSearchContext {
  latitude: number | null;
  longitude: number | null;
  radiusKm: number;
  /** `null` when `userId` has no location on file, nothing to bound a box around. Callers fall back to cap-only bounding (still no unbounded scan; see `discovery.service.ts#loadCandidatePool`). */
  box: GeoBox | null;
}

/** `discovery.service.ts#loadCandidatePool` and this file's own dashboard-count functions both build their geographic prefilter from this, one place that knows "viewer's location + effective search radius -> box". */
export async function resolveGeoSearchContext(ctx: Ctx, userId: string): Promise<GeoSearchContext> {
  const [profile, radiusKm] = await Promise.all([loadProfile(ctx, userId), resolveSearchRadiusKm(ctx, userId)]);
  if (!profile || profile.latitude == null || profile.longitude == null) {
    return { latitude: null, longitude: null, radiusKm, box: null };
  }
  return {
    latitude: profile.latitude,
    longitude: profile.longitude,
    radiusKm,
    box: boundingBoxForRadius(profile.latitude, profile.longitude, radiusKm),
  };
}

/** Unbounded, whole-platform population, kept ONLY for `previewPoolSizeWithUnsetPolicy` below, which must stay an exact count (including users with no `profiles` row at all, see that function's doc). Everything else (`countUsersMatchingMyFilters`/`countUsersWhoseFiltersIMatch`) now goes through `listNearbyActiveUserIds` instead, see the SCALE FIX note below. */
async function listOtherActiveUserIds(ctx: Ctx, userId: string): Promise<string[]> {
  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT id FROM users WHERE status = 'active' AND id <> $1`,
    [userId],
  );
  return rows.map((r) => r.id);
}

// =====================================================================
// SCALE FIX (docs/scale-and-sources.md Part 1, §1.1.3/§1.9): the reality
// dashboard's X/Y counts scanned literally every active user on the
// platform, with no gate at all, worse than discovery, which at least
// had the (weak) completeness/photo/block gate. Bounded "the same way"
// as discovery now means: same geographic box (`resolveGeoSearchContext`
// reusing the viewer's own location + effective search radius exactly
// as `loadCandidatePool` does), same hard cap, same batched filter
// evaluation. `DASHBOARD_SCAN_CAP` is larger than
// `discovery.service.ts#MAX_CANDIDATE_POOL_SIZE` because a count-only
// pass is cheaper per candidate than assembling a full ranked card
// (no compatibility scoring, no tag lookup, no photo join), see this
// build's report for the measured cost of each.
//
// HONESTY UNDER TRUNCATION: `RealityDashboard` (`domain/types.ts`, not
// owned by this build) is three plain numbers with no room for an
// `approximate: boolean` flag, flagged in this build's report as the
// ideal follow-up for whoever next owns that file. Until then, dishonesty
// is avoided the other way: below the cap, the count is EXACT (a full
// scan of the (now geographically bounded, still typically-everyone-in-
// range) population, not a sample), the estimator only activates once
// the geographic population itself exceeds the cap, and even then it is
// a documented, unbiased estimate (sample match-rate × true population
// size in the box, both measured from real queries, never a guess), not
// a silently-wrong exact-looking number. `ctx.logger.warn` fires whenever
// the estimator is used, so truncation is at least observable
// server-side even though the API response itself cannot say so.
// =====================================================================

/** Larger than the discovery pool cap, see block comment above for why a count-only pass affords a bigger sample. */
export const DASHBOARD_SCAN_CAP = 5000;

export interface NearbyActiveUsers {
  ids: string[];
  truncated: boolean;
  /** Exact count of active users in the geographic box (a single indexed aggregate query, O(1) round trips even though it touches every row in the box), independent of how many ids were actually returned/capped. Used to scale a truncated sample back up to a population estimate. */
  totalActiveInRadius: number;
}

/**
 * Active users near `userId` (status + geography only, no completeness/
 * photo/block gate; matches the ORIGINAL `listOtherActiveUserIds`
 * population for X/Y other than the new geographic bound, which is the
 * fix, not an accidental narrowing, see block comment above), ordered
 * most-recently-active first, capped at `cap`. `truncated` is true only
 * when the true in-box population exceeds `cap`.
 */
async function listNearbyActiveUserIds(ctx: Ctx, userId: string, cap: number): Promise<NearbyActiveUsers> {
  const geo = await resolveGeoSearchContext(ctx, userId);

  const params: unknown[] = [userId];
  let geoClause = '';
  if (geo.box) {
    params.push(geo.box.latMin, geo.box.latMax, geo.box.lon1Min, geo.box.lon1Max, geo.box.lon2Min, geo.box.lon2Max);
    geoClause = `
       AND p.latitude BETWEEN $2 AND $3
       AND (p.longitude BETWEEN $4 AND $5 OR p.longitude BETWEEN $6 AND $7)`;
  }

  const { rows: totalRows } = await ctx.db.query<{ count: string }>(
    `SELECT count(*)::text AS count
     FROM users u JOIN profiles p ON p.user_id = u.id
     WHERE u.status = 'active' AND u.id <> $1${geoClause}`,
    params,
  );
  const totalActiveInRadius = Number(totalRows[0]!.count);

  const limitParamIndex = params.length + 1;
  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT u.id
     FROM users u JOIN profiles p ON p.user_id = u.id
     WHERE u.status = 'active' AND u.id <> $1${geoClause}
     ORDER BY u.last_active_at DESC, u.id ASC
     LIMIT $${limitParamIndex}`,
    [...params, cap + 1],
  );
  const truncated = rows.length > cap;
  return { ids: rows.slice(0, cap).map((r) => r.id), truncated, totalActiveInRadius };
}

/** See `listNearbyActiveUserIds`'s "HONESTY UNDER TRUNCATION" note: exact below the cap, an unbiased sample-rate estimate above it, with a `logger.warn` so truncation is at least server-observable. Exported (takes its inputs as plain data, no I/O) so the estimator's math can be unit-tested directly without seeding `DASHBOARD_SCAN_CAP`-plus rows into a real database, see `tests/unit/filter.test.ts`. */
export function summarizeSampledCount(ctx: Ctx, logContext: string, matchingInSample: number, nearby: NearbyActiveUsers): number {
  if (!nearby.truncated) return matchingInSample;
  const rate = nearby.ids.length > 0 ? matchingInSample / nearby.ids.length : 0;
  const estimate = Math.round(rate * nearby.totalActiveInRadius);
  ctx.logger.warn(
    `${logContext}: geographic population (${nearby.totalActiveInRadius}) exceeds the dashboard scan cap (${DASHBOARD_SCAN_CAP}); ` +
      `returning an estimate (sample match rate ${(rate * 100).toFixed(1)}% over ${nearby.ids.length} sampled users, scaled to the true in-radius population) rather than an exact count.`,
  );
  return estimate;
}

/** Count of other active (geographically nearby) users who pass the given user's filters, feeds `discovery.service.ts#getRealityDashboard` (spec §9.3) "X". */
export async function countUsersMatchingMyFilters(ctx: Ctx, userId: string): Promise<number> {
  const nearby = await listNearbyActiveUserIds(ctx, userId, DASHBOARD_SCAN_CAP);
  if (nearby.ids.length === 0) return 0;
  const results = await evaluateFilterPairsBatch(ctx, nearby.ids.map((id) => ({ subjectId: id, ownerId: userId })));
  return summarizeSampledCount(ctx, 'countUsersMatchingMyFilters', results.filter(Boolean).length, nearby);
}

/** Count of other active (geographically nearby) users whose filters the given user passes, the "Y" half of the §9.3 dashboard. */
export async function countUsersWhoseFiltersIMatch(ctx: Ctx, userId: string): Promise<number> {
  const nearby = await listNearbyActiveUserIds(ctx, userId, DASHBOARD_SCAN_CAP);
  if (nearby.ids.length === 0) return 0;
  const results = await evaluateFilterPairsBatch(ctx, nearby.ids.map((id) => ({ subjectId: userId, ownerId: id })));
  return summarizeSampledCount(ctx, 'countUsersWhoseFiltersIMatch', results.filter(Boolean).length, nearby);
}

// =====================================================================
// excludeIfUnset pool preview (product owner requirement: show the cost
// of a strict toggle before the user commits to it).
// =====================================================================

/**
 * Same population and gating as the ORIGINAL (pre-scale-fix)
 * `countUsersMatchingMyFilters`, deliberately NOT geo-bounded, unlike
 * that function now: this preview must count EVERY other active user
 * (including one with no `profiles` row at all, which can't be placed in
 * any geographic box) because it exists to answer "exactly how many
 * candidates would this toggle cost me", and a geographically-narrowed
 * answer to that question would be a different, smaller, and wrong
 * number, see `tests/unit/profileAttributes.test.ts`'s exact-count
 * assertion for this function. `filterKey`'s `excludeIfUnset` is
 * temporarily overridden to `excludeIfUnsetOverride` for this computation
 * only, nothing is written to `hard_filters`.
 *
 * Still gets the SCALE FIX's other half, though: the N+1 (one query per
 * candidate, one more per that candidate's enabled filter) is gone, the
 * whole population's attributes are fetched in a fixed small number of
 * batched queries (same `loadProfilesBatch`/`loadAnswersBatch` machinery
 * as `evaluateFilterPairsBatch`, just inlined here since the per-call
 * `unsetPolicyOverride` isn't something that generic batch function
 * takes a parameter for), so this remains O(1) ROUND TRIPS even though
 * it is still, deliberately, O(all active users) ROWS SCANNED.
 *
 * `filterKey` need not currently exist among `userId`'s filters; if it
 * doesn't, the override has no effect and this returns the same count as
 * `countUsersMatchingMyFilters` would (a no-op preview, not an error,
 * lets a caller preview "what if I turned ON a filter I don't have yet"
 * uniformly with "what if I flipped one I already have").
 */
export async function previewPoolSizeWithUnsetPolicy(
  ctx: Ctx,
  userId: string,
  filterKey: string,
  excludeIfUnsetOverride: boolean,
): Promise<number> {
  const others = await listOtherActiveUserIds(ctx, userId);
  if (others.length === 0) return 0;

  const { rows: ownFilterRows } = await ctx.db.query<HardFilterRow>(
    `SELECT user_id, filter_key, operator, value, exclude_if_unset FROM hard_filters WHERE user_id = $1 AND enabled = true`,
    [userId],
  );
  const filters = ownFilterRows.map((f) =>
    f.filter_key === filterKey ? { ...f, exclude_if_unset: excludeIfUnsetOverride } : f,
  );

  const maps = await loadAttributeMapsFor(ctx, others, filters);

  let count = 0;
  for (const candidateId of others) {
    let passes = true;
    for (const f of filters) {
      const value = resolveAttributeValueFromMaps(candidateId, userId, f.filter_key, maps);
      if (!evaluateFilter({ operator: f.operator, value: f.value }, value, f.exclude_if_unset)) {
        passes = false;
        break;
      }
    }
    if (passes) count++;
  }
  return count;
}

// =====================================================================
// Age-range suggested default ("half your age plus seven"), product
// decision, no § reference. A STARTING SUGGESTION only: never a cap,
// never enforced, and, see `applySuggestedAgeRangeIfUnset`, never
// silently reapplied over a user's own choice once one exists.
// =====================================================================

/**
 * Pure arithmetic: `min = floor(age / 2) + 7`, `max = (age - 7) * 2`.
 * Exposed standalone (no I/O, no `Ctx`) so a caller, an onboarding UI,
 * an API endpoint that wants to show the suggestion without applying it,
 * or a test, can compute it for any age without touching the database.
 */
export function suggestedAgeRange(age: number): { min: number; max: number } {
  return {
    min: Math.floor(age / 2) + 7,
    max: (age - 7) * 2,
  };
}

/**
 * Applies `suggestedAgeRange(callersOwnAge)` to the caller's `age_min`/
 * `age_max` hard filters, but ONLY if NEITHER key has ever been set for
 * this user (checked directly against `hard_filters`, not "enabled",
 * not any other proxy: a row existing at all, even disabled, counts as
 * "already set" and makes this a no-op). This is what makes the
 * suggestion non-silent: calling this again after a user has edited (or
 * a prior call has already set) their age filters changes nothing,
 * because the row already exists, the user's explicit choice always
 * wins. There is no automatic call site for this function anywhere in
 * this build; it is exposed for a caller (e.g. an onboarding flow) to
 * invoke deliberately, never invoked implicitly from `getMyFilters`/
 * `updateMyFilters`/`passesMutualFilters`.
 *
 * Returns the applied `{min, max}`, or `null` if this was a no-op
 * (either an age_min/age_max filter already existed, or the caller has
 * no profile/age to suggest from yet).
 */
export async function applySuggestedAgeRangeIfUnset(ctx: Ctx): Promise<{ min: number; max: number } | null> {
  const { userId } = requireUserActor(ctx);
  const profile = await loadProfile(ctx, userId);
  if (!profile || profile.age == null) return null;

  const { rows } = await ctx.db.query<{ filter_key: string }>(
    `SELECT filter_key FROM hard_filters WHERE user_id = $1 AND filter_key IN ('age_min', 'age_max')`,
    [userId],
  );
  if (rows.length > 0) return null;

  const suggestion = suggestedAgeRange(profile.age);
  await updateMyFilters(ctx, [
    { filterKey: 'age_min', operator: 'gte', value: suggestion.min, enabled: true },
    { filterKey: 'age_max', operator: 'lte', value: suggestion.max, enabled: true },
  ]);
  return suggestion;
}
