/**
 * src/http/serializers/stats.ts, explicit, field-by-field allowlist views
 * for both stats pages (never a raw spread of a service return value into
 * `reply.send`), following the same discipline
 * `src/http/serializers/trust.ts` documents: a service return type can
 * grow a new field over time, and an allowlist here is what stops that
 * field reaching an HTTP response unreviewed.
 *
 * This file only reshapes/renames, it makes no privacy decisions of its
 * own (those are enforced upstream, in `stats.service.ts`/
 * `adminStats.service.ts`: small-cohort suppression, no trust weights, no
 * per-person data, aggregates-only for admin). Its job is narrower and
 * mechanical: never let a field the service layer didn't intend to expose
 * ride along by accident. `serializeUserFilterCosts` is the sharpest
 * example of that job actually mattering: `UserFilterCosts` carries a
 * `rawPool` field for `getMyPoolVenn` to reuse internally, and this
 * allowlist is the one thing standing between that pre-suppression number
 * and an HTTP response.
 */
import type {
  UserStatsOverview,
  UserStatsTrends,
  UserPhotoStats,
  UserFilterCosts,
  FilterCostEntry,
  UserStatsComparisons,
  RateComparison,
  CountComparison,
  SuppressibleCount,
} from '../../services/stats.service.js';
import type { PoolVennData, PoolVennRegion } from '../../services/statsVenn.js';
import type { AdminStatsOverview, AdminRetention } from '../../services/adminStats.service.js';

function suppressible(c: SuppressibleCount): { value: number | null; suppressed: boolean } {
  return { value: c.value, suppressed: c.suppressed };
}

interface FilterCostEntryView {
  filterKey: string;
  additionalCandidatesIfRemoved: { value: number | null; suppressed: boolean };
}

function filterCostEntry(f: FilterCostEntry): FilterCostEntryView {
  return { filterKey: f.filterKey, additionalCandidatesIfRemoved: suppressible(f.additionalCandidatesIfRemoved) };
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
  perFilter: FilterCostEntryView[];
  candidatesFailingTwoOrMore: { value: number | null; suppressed: boolean };
  costliestFilter: FilterCostEntryView | null;
  computedAt: Date;
  fromCache: boolean;
  // Deliberately no `rawPool` field here: `UserFilterCosts.rawPool` exists
  // only so `stats.service.ts#getMyPoolVenn` can reuse this same cached
  // computation without a second reality-dashboard call -- it is pre-
  // suppression, unlike every field above, and this allowlist is what
  // keeps it from ever reaching an HTTP response.
}

export function serializeUserFilterCosts(costs: UserFilterCosts): UserFilterCostsView {
  return {
    currentPool: suppressible(costs.currentPool),
    whoseFiltersIMatch: suppressible(costs.whoseFiltersIMatch),
    mutualMatchPool: suppressible(costs.mutualMatchPool),
    perFilter: costs.perFilter.map(filterCostEntry),
    candidatesFailingTwoOrMore: suppressible(costs.candidatesFailingTwoOrMore),
    costliestFilter: costs.costliestFilter ? filterCostEntry(costs.costliestFilter) : null,
    computedAt: costs.computedAt,
    fromCache: costs.fromCache,
  };
}

interface PoolVennRegionView {
  label: string;
  count: { value: number | null; suppressed: boolean };
}

function vennRegion(r: PoolVennRegion): PoolVennRegionView {
  return { label: r.label, count: suppressible(r.count) };
}

export interface UserPoolVennView {
  setA: PoolVennRegionView;
  setB: PoolVennRegionView;
  intersection: PoolVennRegionView;
  onlyA: PoolVennRegionView;
  onlyB: PoolVennRegionView;
}

export function serializeUserPoolVenn(data: PoolVennData): UserPoolVennView {
  return {
    setA: vennRegion(data.setA),
    setB: vennRegion(data.setB),
    intersection: vennRegion(data.intersection),
    onlyA: vennRegion(data.onlyA),
    onlyB: vennRegion(data.onlyB),
  };
}

function rateComparison(r: RateComparison): RateComparison {
  return { mine: r.mine, regionTypical: r.regionTypical, position: r.position };
}

function countComparison(c: CountComparison): CountComparison {
  return { mine: c.mine, regionTypical: c.regionTypical, position: c.position };
}

export interface UserStatsComparisonsView {
  hasLocation: boolean;
  regionPopulation: { value: number | null; suppressed: boolean };
  questionsAnswered: UserStatsComparisons['questionsAnswered'];
  filterStrictness: {
    myEnabledFilterCount: number;
    regionTypicalEnabledFilterCount: number | null;
    position: UserStatsComparisons['filterStrictness']['position'];
    costliestFilter: FilterCostEntryView | null;
  };
  tagPrevalence: Array<{ tagId: string; tagName: string; nearbyHolders: { value: number | null; suppressed: boolean } }>;
  sentInterestAcceptance: RateComparison;
  receivedInterestConversion: RateComparison;
  receivedInterestVolume: CountComparison;
  profileViews: CountComparison;
  photoPerformance: RateComparison;
  computedAt: Date;
}

export function serializeUserStatsComparisons(comparisons: UserStatsComparisons): UserStatsComparisonsView {
  return {
    hasLocation: comparisons.hasLocation,
    regionPopulation: suppressible(comparisons.regionPopulation),
    questionsAnswered: comparisons.questionsAnswered,
    filterStrictness: {
      myEnabledFilterCount: comparisons.filterStrictness.myEnabledFilterCount,
      regionTypicalEnabledFilterCount: comparisons.filterStrictness.regionTypicalEnabledFilterCount,
      position: comparisons.filterStrictness.position,
      costliestFilter: comparisons.filterStrictness.costliestFilter
        ? filterCostEntry(comparisons.filterStrictness.costliestFilter)
        : null,
    },
    tagPrevalence: comparisons.tagPrevalence.map((t) => ({
      tagId: t.tagId,
      tagName: t.tagName,
      nearbyHolders: suppressible(t.nearbyHolders),
    })),
    sentInterestAcceptance: rateComparison(comparisons.sentInterestAcceptance),
    receivedInterestConversion: rateComparison(comparisons.receivedInterestConversion),
    receivedInterestVolume: countComparison(comparisons.receivedInterestVolume),
    profileViews: countComparison(comparisons.profileViews),
    photoPerformance: rateComparison(comparisons.photoPerformance),
    computedAt: comparisons.computedAt,
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
