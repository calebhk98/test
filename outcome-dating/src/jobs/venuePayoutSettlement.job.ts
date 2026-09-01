/**
 * §15.4/§13.2 Venue Payout Settlement job. Thin wrapper around
 * `venueSettlement.service#settleDueVenuePayouts` — every `completed`,
 * venue-redeemed date proposal without an existing settlement gets one,
 * exactly once (idempotent — see that module's own doc). No domain logic
 * lives here; this file only gives the scheduler/CLI a stable name and
 * interval, same pattern as every other `src/jobs/*.job.ts` file.
 */
import type { Ctx } from '../lib/ctx.js';
import { settleDueVenuePayouts } from '../services/venueSettlement.service.js';
import type { SettleDueVenuePayoutsResult } from '../services/venueSettlement.service.js';
import type { JobDefinition } from './types.js';

export async function runVenuePayoutSettlementJob(ctx: Ctx): Promise<SettleDueVenuePayoutsResult> {
  return settleDueVenuePayouts(ctx);
}

export const venuePayoutSettlementJob: JobDefinition = {
  name: 'venue_payout_settlement',
  description: 'Settle payouts for completed, venue-redeemed date proposals that have not yet been settled (§15.4, §13.2).',
  intervalMs: 30 * 60 * 1000,
  run: runVenuePayoutSettlementJob,
};
