import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
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
 */

export interface UpdateFilterInput {
  filterKey: string;
  operator: FilterOperator;
  value: unknown;
  enabled: boolean;
}

export async function getMyFilters(ctx: Ctx): Promise<HardFilter[]> {
  throw new NotImplementedError('filter.getMyFilters');
}

/** Upserts the caller's filters. Does not cap the number of filter slots (spec §9.2 "do not block filter slots"). */
export async function updateMyFilters(ctx: Ctx, filters: UpdateFilterInput[]): Promise<HardFilter[]> {
  throw new NotImplementedError('filter.updateMyFilters');
}

/**
 * Pure evaluation of one filter against one candidate attribute value —
 * no I/O. Exported so both `passesMutualFilters` and unit tests can use
 * the exact same operator semantics.
 */
export function evaluateFilter(filter: Pick<HardFilter, 'operator' | 'value'>, candidateValue: unknown): boolean {
  throw new NotImplementedError('filter.evaluateFilter');
}

/**
 * §9.4 mutual filter check: does `userId` pass `candidateId`'s enabled
 * hard filters, AND does `candidateId` pass `userId`'s? Both directions
 * are required for discovery visibility by default (spec §9.4).
 */
export async function passesMutualFilters(ctx: Ctx, userId: string, candidateId: string): Promise<boolean> {
  throw new NotImplementedError('filter.passesMutualFilters');
}

/** Count of other active users who pass the given user's filters — feeds `discovery.service.ts#getRealityDashboard` (spec §9.3). */
export async function countUsersMatchingMyFilters(ctx: Ctx, userId: string): Promise<number> {
  throw new NotImplementedError('filter.countUsersMatchingMyFilters');
}

/** Count of other active users whose filters the given user passes — the other half of the §9.3 dashboard. */
export async function countUsersWhoseFiltersIMatch(ctx: Ctx, userId: string): Promise<number> {
  throw new NotImplementedError('filter.countUsersWhoseFiltersIMatch');
}
