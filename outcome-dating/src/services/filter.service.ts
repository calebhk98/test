import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import type { FilterOperator, HardFilter } from '../domain/types.js';
import { BODY_TYPES } from '../domain/units/bodyType.js';
import { ValidationError } from '../lib/errors.js';

/**
 * filter.service — hard filters.
 * Spec: §9, §24.4 (routes).
 *
 * Owning agent: B.
 *
 * INVARIANT (spec §9.1, restated in INTERFACES.md): hard filters are
 * NEVER overridden by the compatibility algorithm. `passesMutualFilters`
 * is the sole gate `discovery.service.ts` calls before a candidate is even
 * scored — a candidate that fails it must not appear regardless of
 * compatibility score. Do not add a "soft override" path here for any
 * reason; if product wants one-sided filtering later it must be a new,
 * explicit function, not a fallback inside this one (spec §9.4 exception
 * clause: "it must be explicit").
 *
 * CANDIDATE ATTRIBUTE SOURCING (a design decision the spec leaves
 * implicit, documented here because it drives most of this file): a
 * `hard_filters` row only stores the *filter* (key/operator/value) — it
 * says nothing about where a candidate's actual value for that key comes
 * from. `db/migrations/001_init.sql` (frozen, not owned by this agent)
 * gives `profiles` exactly: display_name, bio, city, latitude, longitude,
 * age, gender, seeking, relationship_intention — no smoking/drinking/
 * drugs/children/religion columns. Meanwhile spec §9.2's own examples
 * (`smoking <= 2`, `wants_children >= 4`) are numeric comparisons on a 1-5
 * scale, which is exactly the scale `answers.self_value` uses (§8.1) — and
 * the seed data (`src/seed.ts`) ships a `smoking`/`wants_children`/
 * `religion`/... question in the bank with that same slug convention. So:
 *   - `age_min` / `age_max` resolve against `profiles.age`.
 *   - `distance_km` resolves against the haversine distance between the
 *     two users' `profiles.latitude/longitude` (never the fuzzed/exposed
 *     value — see `discovery.service.ts` for the rounded value shown on a
 *     card, §7.1/§28.5).
 *   - `gender_preference` resolves against `profiles.gender`.
 *   - `relationship_intention` resolves against `profiles.relationship_intention`.
 *   - `height_cm` / `weight_g` resolve against `profiles.height_cm` /
 *     `profiles.weight_g` (this build, `db/migrations/009_units_attributes.sql`)
 *     — always the CANONICAL stored value, never a display unit (see
 *     `src/domain/units/`). `weight_g` additionally resolves as
 *     UNRESOLVED whenever `profiles.weight_visible` is false: a hidden
 *     weight is invisible to filter matching exactly as it is invisible
 *     on the public profile view, not merely hidden from display while
 *     still usable to gate matches (see `profile.service.ts`'s
 *     `PublicProfileView` doc for the same discipline applied there).
 *   - `body_type` resolves against `profiles.body_type` — a categorical
 *     value, so a body-type PREFERENCE is expressed as a SET of
 *     acceptable values via the existing `in` operator, never a numeric
 *     midpoint comparison.
 *   - every other key (has_children, wants_children, smoking, drinking,
 *     drug_use, religion, and any admin-defined key) resolves against the
 *     candidate's `answers.self_value` for the `questions` row whose
 *     `slug` equals the filter key.
 *
 * MISSING/UNRESOLVED VALUES — the `excludeIfUnset` toggle (product
 * decision, no § reference; supersedes this file's original unconditional
 * "always fails closed" behavior). Every hard-filter row now carries an
 * `excludeIfUnset: boolean` (`hard_filters.exclude_if_unset`,
 * `009_units_attributes.sql`): when a candidate's value for a filter's
 * key cannot be resolved (`resolveAttributeValue` returns `undefined`),
 * `evaluateFilter` EXCLUDES that candidate if `excludeIfUnset` is true,
 * and INCLUDES them (does not fail the filter) if it is false. This is a
 * per-row, per-user, explicit choice, not a hardcoded rule:
 *   - Default when the caller omits it: FALSE, for EVERY filter key, no
 *     exceptions — including keys derived from a DEAL-BREAKER preference
 *     (built by another agent in `src/domain/questions/`, not this
 *     file). This went through two narrower designs before landing here
 *     (first "true for everything", then "true except three physical-
 *     attribute keys") — both were rejected by the product owner for the
 *     same underlying reason: a brand-new account has not filled
 *     everything in yet, and must not be punished for that. Someone who
 *     just signed up and has not entered a height (or answered the
 *     question a deal-breaker filter is derived from) should still be
 *     discoverable while they finish their profile — silently
 *     disappearing from every OTHER user's results because a field is
 *     blank is exactly the failure this toggle exists to prevent, and an
 *     opt-out-by-default policy re-creates that failure for anyone who
 *     forgets to opt in. So: nothing is ever excluded by an unresolved
 *     value unless a user (or a deal-breaker derivation acting on that
 *     user's explicit request) deliberately sets `excludeIfUnset: true`
 *     for that specific filter — see `defaultExcludeIfUnset`, which
 *     still takes a `filterKey` argument (for interface stability and
 *     so a future per-key exception, if product ever asks for one again,
 *     has a single place to live) but currently ignores it.
 *   - `updateMyFilters` always honors an EXPLICIT `excludeIfUnset` over
 *     this default — a deal-breaker derivation, or a user's own toggle,
 *     passing `true` is respected exactly. No change is needed in this
 *     file for the deal-breaker-derivation agent's code to work; the
 *     field's existence and this default are flagged in this build's
 *     report so that agent knows to set it explicitly when (and only
 *     when) the user has asked for that deal-breaker to be strict about
 *     unknowns.
 *   - The `hard_filters.exclude_if_unset` COLUMN default (used only by
 *     inserts that bypass this service, e.g. raw SQL fixtures) is
 *     `false`, matching the application-level default above exactly —
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
   * — see the file-level "MISSING/UNRESOLVED VALUES" note. Passing this
   * explicitly always wins over that default, and over whatever value was
   * previously stored for this filter.
   */
  excludeIfUnset?: boolean;
}

/**
 * `HardFilter` (`domain/types.ts`, not owned by this agent) predates the
 * `excludeIfUnset` toggle. Rather than edit a file outside this build's
 * ownership boundary, every row this service returns is `HardFilter`
 * PLUS that one field — a strict superset, so every existing consumer
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
 * Default for an omitted `excludeIfUnset`, for any filter key — see the
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

/** Upserts the caller's filters. Does not cap the number of filter slots (spec §9.2 "do not block filter slots"). */
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
 * Pure evaluation of one filter against one candidate attribute value —
 * no I/O. Exported so both `passesMutualFilters` and unit tests can use
 * the exact same operator semantics.
 *
 * `candidateValue === undefined` means "could not be resolved". What
 * happens then is `excludeIfUnset` (see the file-level "MISSING/
 * UNRESOLVED VALUES" note): `true` fails the filter (excludes the
 * candidate); `false` — the default parameter value, matching
 * `defaultExcludeIfUnset`'s current universal default — passes it despite
 * the unresolved value. `null` is a resolved-but-empty value and is
 * compared normally (so `neq: null` etc. behave as expected) — only
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
  /** Canonical centimetres, or `null` if the user never set it — see `src/domain/units/height.ts`. */
  heightCm: number | null;
  /** Canonical grams, or `null` if the user never set it — see `src/domain/units/weight.ts`. */
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

async function loadSelfAnswerBySlug(ctx: Ctx, userId: string, slug: string): Promise<number | null | undefined> {
  const { rows } = await ctx.db.query<{ self_value: number | null }>(
    `SELECT a.self_value
     FROM answers a
     JOIN questions q ON q.id = a.question_id
     WHERE a.user_id = $1 AND q.slug = $2`,
    [userId, slug],
  );
  if (rows.length === 0) return undefined; // no such question, or candidate never answered it
  return rows[0]!.self_value; // may legitimately be null ("prefer not to say")
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
      // display — see the file-level CANDIDATE ATTRIBUTE SOURCING note.
      if (!profile || !profile.weightVisible || profile.weightG == null) return undefined;
      return profile.weightG;
    }
    case 'body_type': {
      const profile = await loadProfile(ctx, subjectUserId);
      return profile?.bodyType ?? undefined;
    }
    default:
      return loadSelfAnswerBySlug(ctx, subjectUserId, filterKey);
  }
}

/**
 * Does `subjectUserId`'s resolved attributes satisfy every *enabled* hard
 * filter owned by `filterOwnerUserId`? Filterless users trivially pass.
 *
 * `unsetPolicyOverride` lets a caller ask "what if THIS ONE filter key's
 * `excludeIfUnset` were different" without writing anything — the
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

async function listOtherActiveUserIds(ctx: Ctx, userId: string): Promise<string[]> {
  const { rows } = await ctx.db.query<{ id: string }>(
    `SELECT id FROM users WHERE status = 'active' AND id <> $1`,
    [userId],
  );
  return rows.map((r) => r.id);
}

/** Count of other active users who pass the given user's filters — feeds `discovery.service.ts#getRealityDashboard` (spec §9.3). */
export async function countUsersMatchingMyFilters(ctx: Ctx, userId: string): Promise<number> {
  const others = await listOtherActiveUserIds(ctx, userId);
  let count = 0;
  for (const candidateId of others) {
    if (await subjectPassesFiltersOf(ctx, candidateId, userId)) count++;
  }
  return count;
}

/** Count of other active users whose filters the given user passes — the other half of the §9.3 dashboard. */
export async function countUsersWhoseFiltersIMatch(ctx: Ctx, userId: string): Promise<number> {
  const others = await listOtherActiveUserIds(ctx, userId);
  let count = 0;
  for (const candidateId of others) {
    if (await subjectPassesFiltersOf(ctx, userId, candidateId)) count++;
  }
  return count;
}

// =====================================================================
// excludeIfUnset pool preview (product owner requirement: show the cost
// of a strict toggle before the user commits to it).
// =====================================================================

/**
 * Same population and gating as `countUsersMatchingMyFilters` (the "X"
 * reality-dashboard count: how many other active users pass `userId`'s
 * enabled filters), except `filterKey`'s `excludeIfUnset` is temporarily
 * overridden to `excludeIfUnsetOverride` for this computation only —
 * nothing is written to `hard_filters`. Lets a caller show, e.g., "turning
 * on 'must have height set' would cost you N candidates" before the user
 * flips the toggle for real via `updateMyFilters`.
 *
 * `filterKey` need not currently exist among `userId`'s filters; if it
 * doesn't, the override has no effect and this returns the same count as
 * `countUsersMatchingMyFilters` would (a no-op preview, not an error —
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
  let count = 0;
  for (const candidateId of others) {
    if (await subjectPassesFiltersOf(ctx, candidateId, userId, { filterKey, excludeIfUnset: excludeIfUnsetOverride })) {
      count++;
    }
  }
  return count;
}

// =====================================================================
// Age-range suggested default ("half your age plus seven") — product
// decision, no § reference. A STARTING SUGGESTION only: never a cap,
// never enforced, and — see `applySuggestedAgeRangeIfUnset` — never
// silently reapplied over a user's own choice once one exists.
// =====================================================================

/**
 * Pure arithmetic: `min = floor(age / 2) + 7`, `max = (age - 7) * 2`.
 * Exposed standalone (no I/O, no `Ctx`) so a caller — an onboarding UI,
 * an API endpoint that wants to show the suggestion without applying it,
 * or a test — can compute it for any age without touching the database.
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
 * this user (checked directly against `hard_filters` — not "enabled",
 * not any other proxy: a row existing at all, even disabled, counts as
 * "already set" and makes this a no-op). This is what makes the
 * suggestion non-silent: calling this again after a user has edited (or
 * a prior call has already set) their age filters changes nothing,
 * because the row already exists — the user's explicit choice always
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
