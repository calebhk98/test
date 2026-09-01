import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { requireUserActor } from '../lib/ctx.js';
import type { FilterOperator, HardFilter } from '../domain/types.js';

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
 *   - every other key (has_children, wants_children, smoking, drinking,
 *     drug_use, religion, and any admin-defined key) resolves against the
 *     candidate's `answers.self_value` for the `questions` row whose
 *     `slug` equals the filter key.
 * A value that cannot be resolved (missing profile field, no matching
 * question/answer) makes that filter FAIL CLOSED — spec §9.1 says filters
 * "MUST be enforced strictly", and treating "I can't verify this" as "it
 * passes" would let an unverifiable candidate slip through a filter the
 * user believes is being enforced. Fail-closed is the safer reading.
 */

export interface UpdateFilterInput {
  filterKey: string;
  operator: FilterOperator;
  value: unknown;
  enabled: boolean;
}

interface HardFilterRow {
  user_id: string;
  filter_key: string;
  operator: FilterOperator;
  value: unknown;
  enabled: boolean;
  updated_at: Date;
}

function filterFromRow(row: HardFilterRow): HardFilter {
  return {
    userId: row.user_id,
    filterKey: row.filter_key,
    operator: row.operator,
    value: row.value,
    enabled: row.enabled,
    updatedAt: row.updated_at,
  };
}

export async function getMyFilters(ctx: Ctx): Promise<HardFilter[]> {
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
});

/** Upserts the caller's filters. Does not cap the number of filter slots (spec §9.2 "do not block filter slots"). */
export async function updateMyFilters(ctx: Ctx, filters: UpdateFilterInput[]): Promise<HardFilter[]> {
  const { userId } = requireUserActor(ctx);
  const parsed = z.array(updateFilterInputSchema).parse(filters);

  for (const f of parsed) {
    await ctx.db.query(
      `INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled, updated_at)
       VALUES ($1, $2, $3, $4::jsonb, $5, $6)
       ON CONFLICT (user_id, filter_key) DO UPDATE SET
         operator = EXCLUDED.operator,
         value = EXCLUDED.value,
         enabled = EXCLUDED.enabled,
         updated_at = EXCLUDED.updated_at`,
      [userId, f.filterKey, f.operator, JSON.stringify(f.value), f.enabled, ctx.clock.now()],
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
 * `candidateValue === undefined` means "could not be resolved" and always
 * fails (see file-level "fail closed" note). `null` is a resolved-but-empty
 * value and is compared normally (so `neq: null` etc. behave as expected).
 */
export function evaluateFilter(filter: Pick<HardFilter, 'operator' | 'value'>, candidateValue: unknown): boolean {
  if (candidateValue === undefined) return false;

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
}

async function loadProfile(ctx: Ctx, userId: string): Promise<ProfileLocationAge | undefined> {
  const { rows } = await ctx.db.query<{
    age: number;
    gender: string;
    relationship_intention: string;
    latitude: number | null;
    longitude: number | null;
  }>('SELECT age, gender, relationship_intention, latitude, longitude FROM profiles WHERE user_id = $1', [userId]);
  const row = rows[0];
  if (!row) return undefined;
  return {
    age: row.age,
    gender: row.gender,
    relationshipIntention: row.relationship_intention,
    latitude: row.latitude,
    longitude: row.longitude,
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
    default:
      return loadSelfAnswerBySlug(ctx, subjectUserId, filterKey);
  }
}

/** Does `subjectUserId`'s resolved attributes satisfy every *enabled* hard filter owned by `filterOwnerUserId`? Filterless users trivially pass. */
async function subjectPassesFiltersOf(ctx: Ctx, subjectUserId: string, filterOwnerUserId: string): Promise<boolean> {
  const { rows } = await ctx.db.query<{ filter_key: string; operator: FilterOperator; value: unknown }>(
    'SELECT filter_key, operator, value FROM hard_filters WHERE user_id = $1 AND enabled = true',
    [filterOwnerUserId],
  );
  for (const f of rows) {
    const candidateValue = await resolveAttributeValue(ctx, subjectUserId, filterOwnerUserId, f.filter_key);
    if (!evaluateFilter({ operator: f.operator, value: f.value }, candidateValue)) return false;
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
