/**
 * src/http/serializers/stats.ts — explicit, field-by-field allowlist views
 * for both stats pages (never a raw spread of a service return value into
 * `reply.send`), following the same discipline
 * `src/http/serializers/trust.ts` documents: a service return type can
 * grow a new field over time, and an allowlist here is what stops that
 * field reaching an HTTP response unreviewed.
 *
 * This file only reshapes/renames — it makes no privacy decisions of its
 * own (those are enforced upstream, in `stats.service.ts`/
 * `adminStats.service.ts`: small-cohort suppression, no trust weights, no
 * per-person data, aggregates-only for admin). Its job is narrower and
 * mechanical: never let a field the service layer didn't intend to expose
 * ride along by accident.
 */
import type {
  UserStatsOverview,
  UserStatsTrends,
  UserPhotoStats,
  UserFilterCosts,
  SuppressibleCount,
} from '../../services/stats.service.js';
import type { AdminStatsOverview, AdminRetention } from '../../services/adminStats.service.js';

function suppressible(c: SuppressibleCount): { value: number | null; suppressed: boolean } {
  return { value: c.value, suppressed: c.suppressed };
}

export interface UserStatsOverviewView {
  funnel: UserStatsOverview['funnel'];
  completeness: UserStatsOverview['completeness'];
  responseBehaviour: UserStatsOverview['responseBehaviour'];
  dateOutcomes: UserStatsOverview['dateOutcomes'];
  generatedAt: Date;
}

export function serializeUserStatsOverview(overview: UserStatsOverview): UserStatsOverviewView {
  return {
    funnel: overview.funnel,
    completeness: overview.completeness,
    responseBehaviour: overview.responseBehaviour,
    dateOutcomes: overview.dateOutcomes,
    generatedAt: overview.generatedAt,
  };
}

export interface UserStatsTrendsView {
  weeks: number;
  points: UserStatsTrends['points'];
}

export function serializeUserStatsTrends(trends: UserStatsTrends): UserStatsTrendsView {
  return { weeks: trends.weeks, points: trends.points };
}

export interface UserPhotoStatsView {
  photos: UserPhotoStats['photos'];
  hasEnoughDataForRecommendation: boolean;
}

export function serializeUserPhotoStats(stats: UserPhotoStats): UserPhotoStatsView {
  return { photos: stats.photos, hasEnoughDataForRecommendation: stats.hasEnoughDataForRecommendation };
}

export interface UserFilterCostsView {
  currentPool: { value: number | null; suppressed: boolean };
  whoseFiltersIMatch: { value: number | null; suppressed: boolean };
  mutualMatchPool: { value: number | null; suppressed: boolean };
  perFilter: Array<{ filterKey: string; additionalCandidatesIfRemoved: { value: number | null; suppressed: boolean } }>;
  computedAt: Date;
  fromCache: boolean;
}

export function serializeUserFilterCosts(costs: UserFilterCosts): UserFilterCostsView {
  return {
    currentPool: suppressible(costs.currentPool),
    whoseFiltersIMatch: suppressible(costs.whoseFiltersIMatch),
    mutualMatchPool: suppressible(costs.mutualMatchPool),
    perFilter: costs.perFilter.map((f) => ({
      filterKey: f.filterKey,
      additionalCandidatesIfRemoved: suppressible(f.additionalCandidatesIfRemoved),
    })),
    computedAt: costs.computedAt,
    fromCache: costs.fromCache,
  };
}

export interface AdminStatsOverviewView {
  window: AdminStatsOverview['window'];
  core: AdminStatsOverview['core'];
  money: AdminStatsOverview['money'];
  quality: AdminStatsOverview['quality'];
  freshness: AdminStatsOverview['freshness'];
}

export function serializeAdminStatsOverview(overview: AdminStatsOverview): AdminStatsOverviewView {
  return {
    window: overview.window,
    core: overview.core,
    money: overview.money,
    quality: overview.quality,
    freshness: overview.freshness,
  };
}

export interface AdminRetentionView {
  cohorts: AdminRetention['cohorts'];
  freshness: AdminRetention['freshness'];
}

export function serializeAdminRetention(retention: AdminRetention): AdminRetentionView {
  return { cohorts: retention.cohorts, freshness: retention.freshness };
}
