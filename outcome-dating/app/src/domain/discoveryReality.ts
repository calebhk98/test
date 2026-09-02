/**
 * Turns the three raw pool numbers from `GET /discovery/reality` into
 * one of two plain-language explanations for an empty grid, per the
 * product review's #2 abandonment risk: "an unexplained empty or thin
 * discovery grid... surface [the reality dashboard] proactively the
 * first time a grid comes back thin, rather than waiting for someone
 * to go looking for it." A cold market (almost nobody nearby at all)
 * and a too-narrow filter set (plenty of people nearby, but this
 * person's own filters exclude nearly all of them) call for different
 * copy and a different next action, so this is worth naming explicitly
 * rather than showing one generic "nobody found" message either way.
 */
import type { RealityDashboard } from '../api/types';

export type EmptyGridReason = 'cold_start' | 'narrow_filters' | 'unclear';

const COLD_START_THRESHOLD = 5;

export function classifyEmptyGrid(dashboard: RealityDashboard): EmptyGridReason {
  const { matchesMyFilters, whoseFiltersIMatch } = dashboard;
  const nearbyPeople = Math.max(matchesMyFilters, whoseFiltersIMatch);

  if (nearbyPeople <= COLD_START_THRESHOLD) return 'cold_start';
  if (dashboard.mutualMatchPool === 0) return 'narrow_filters';
  return 'unclear';
}

export function copyForEmptyGrid(reason: EmptyGridReason): { title: string; message: string } {
  switch (reason) {
    case 'cold_start':
      return {
        title: 'Not many people here yet',
        message: "There aren't many people on Outcome Dating in your area right now. This isn't about your filters, the pool nearby is just small today. Check back as more people join.",
      };
    case 'narrow_filters':
      return {
        title: 'Your filters are excluding everyone nearby',
        message: 'There are people nearby, but your current filters rule all of them out. Try widening your distance or age range in Settings.',
      };
    case 'unclear':
      return {
        title: 'No one new to show right now',
        message: 'Check back soon, or try widening your filters in Settings.',
      };
  }
}
